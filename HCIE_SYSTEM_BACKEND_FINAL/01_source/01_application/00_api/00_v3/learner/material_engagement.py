"""Modality-effectiveness observability endpoints.

This is *additive observability only*. It captures WHICH study-material
modality a learner opened for a concept (reading / diagram / audio /
interactive / video) so a reviewer can study "reading vs interactive vs audio
→ learning speed / mastery" per concept and per grade-band.

INVARIANT (do not break): the ``material_engagement`` table is NEVER read by
the MAB / bandit and NEVER feeds the sealed evaluation. It mirrors the existing
"material ordering is observational UX only — never feeds the MAB" contract in
``material.py``. Nothing here writes a reward, a mastery value, or an arm
selection — it only records that a learner *viewed* a material, and then joins
that view (read-only) against the already-recorded ``experiment_trajectories``
mastery deltas for display.

Two endpoints, two routers:

- ``POST /v3/learner/material-view`` (``require_student``) — INSERT one
  engagement row. Registered on the learner router (see learner/__init__.py).
- ``GET  /v3/frontend/dashboard/modality-effectiveness`` (no strict auth,
  mirrors ``/session-trace``) — returns display aggregates. Registered next to
  the dashboard router (see frontend/dashboard __init__).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies.rbac import require_student
from app.api.v3.dependencies_its import get_its_runtime_service

logger = logging.getLogger(__name__)


# ── POST /v3/learner/material-view (require_student) ─────────────────────────
material_engagement_router = APIRouter(tags=["v3-learner-material-engagement"])


class MaterialViewBody(BaseModel):
    concept_id: str = Field(..., min_length=1)
    modality: str = Field(..., min_length=1)
    grade_band: Optional[str] = None
    ms_spent: Optional[int] = None


@material_engagement_router.post("/material-view")
async def record_material_view(
    body: MaterialViewBody,
    user: Dict[str, Any] = Depends(require_student),
    its=Depends(get_its_runtime_service),
) -> Dict[str, Any]:
    """Record that ``user`` opened a ``modality`` material for ``concept_id``.

    Observational only — no scoring, no MAB, no mastery write. On any DB error
    we still return ``{ok: true}`` so the learner's /learn flow is never broken
    by an analytics write (the beacon is fire-and-forget on the client too).
    """
    user_id = user.get("id") or user.get("user_id")
    if not user_id:
        return {"ok": True}

    try:
        its.postgres_store.execute_write(
            """
            INSERT INTO material_engagement
                (user_id, concept_id, modality, grade_band, ms_spent)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                str(user_id),
                body.concept_id,
                body.modality,
                body.grade_band,
                body.ms_spent,
            ),
        )
    except Exception as exc:  # pragma: no cover — defensive; never break /learn
        logger.warning("material_view_insert_failed err=%s", exc)

    return {"ok": True}


# ── GET /v3/frontend/dashboard/modality-effectiveness (no strict auth) ───────
modality_effectiveness_router = APIRouter(
    prefix="/frontend/dashboard", tags=["v3-frontend"]
)


def _store():
    """Lazy postgres store accessor (matches dashboard.py)."""
    from storage.postgres_store.interaction_store import PostgresInteractionStore

    return PostgresInteractionStore()


def _safe_read(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a read; on any failure return []. Never invent rows."""
    try:
        rows = _store().execute_read(query, params)
        return list(rows) if rows else []
    except Exception as exc:  # noqa: BLE001
        logger.warning("modality-effectiveness query failed: %r | %s", exc, query[:80])
        return []


# Per-(user, concept) mastery gain, read-only, from the already-recorded
# experiment_trajectories. gain = mastery_after(last) - mastery_before(first)
# over that learner's interactions on that concept. Falls back to the sum of
# mastery_delta when the endpoints are null. This CTE is joined against
# material_engagement so every aggregate is "views a learner made" × "mastery
# that learner actually gained on the concept they viewed material for".
_GAIN_CTE = """
    WITH engaged AS (
        -- Only the (user, concept) pairs that actually have a material view.
        -- Scoping the gain scan to these (tiny set) avoids scanning all ~1.1M
        -- experiment_trajectories rows 3-4× per request (was a 20s timeout).
        SELECT DISTINCT user_id, concept_id FROM material_engagement
    ),
    gain AS (
        SELECT et.user_id, et.concept,
               COALESCE(
                   (array_agg(et.mastery_after ORDER BY et.interaction_number DESC))[1]
                 - (array_agg(et.mastery_before ORDER BY et.interaction_number ASC))[1],
                   SUM(et.mastery_delta)
               ) AS mastery_gain
        FROM experiment_trajectories et
        JOIN engaged e ON e.user_id = et.user_id AND e.concept_id = et.concept
        GROUP BY et.user_id, et.concept
    )
"""


@modality_effectiveness_router.get("/modality-effectiveness")
async def get_modality_effectiveness() -> Dict[str, Any]:
    """Display aggregates for the Modality Effectiveness Lab.

    OBSERVATIONAL: the modality is *learner-chosen* (which material they opened),
    NOT bandit-selected. Joins material_engagement (views) against
    experiment_trajectories mastery deltas (read-only). If a join is empty every
    array comes back empty — we never fabricate numbers.

    Authority: material_engagement + experiment_trajectories (+ k12_concepts for
    grade-band fallback). Never feeds the MAB or the sealed evaluation.
    """
    # by_modality — one row per modality across all engagements.
    by_modality = [
        {
            "modality": r["modality"],
            "learners": int(r["learners"] or 0),
            "avg_mastery_gain": round(float(r["avg_mastery_gain"] or 0.0), 4),
            "avg_attempts": round(float(r["avg_attempts"] or 0.0), 2),
            "engagements": int(r["engagements"] or 0),
        }
        for r in _safe_read(
            _GAIN_CTE
            + """
            SELECT me.modality,
                   COUNT(DISTINCT me.user_id)              AS learners,
                   AVG(g.mastery_gain)                     AS avg_mastery_gain,
                   AVG(att.n_attempts)                     AS avg_attempts,
                   COUNT(*)                                AS engagements
            FROM material_engagement me
            LEFT JOIN gain g
                   ON g.user_id = me.user_id AND g.concept = me.concept_id
            LEFT JOIN (
                   SELECT et.user_id, et.concept, COUNT(*) AS n_attempts
                   FROM experiment_trajectories et
                   JOIN engaged e ON e.user_id = et.user_id AND e.concept_id = et.concept
                   GROUP BY et.user_id, et.concept
            ) att ON att.user_id = me.user_id AND att.concept = me.concept_id
            GROUP BY me.modality
            ORDER BY avg_mastery_gain DESC NULLS LAST
            """
        )
    ]

    # by_concept_modality — best modality per concept.
    by_concept_modality = [
        {
            "concept_id": r["concept_id"],
            "modality": r["modality"],
            "avg_mastery_gain": round(float(r["avg_mastery_gain"] or 0.0), 4),
            "n": int(r["n"] or 0),
        }
        for r in _safe_read(
            _GAIN_CTE
            + """
            SELECT me.concept_id, me.modality,
                   AVG(g.mastery_gain) AS avg_mastery_gain,
                   COUNT(*)            AS n
            FROM material_engagement me
            LEFT JOIN gain g
                   ON g.user_id = me.user_id AND g.concept = me.concept_id
            GROUP BY me.concept_id, me.modality
            ORDER BY me.concept_id ASC, avg_mastery_gain DESC NULLS LAST
            """
        )
    ]

    # by_gradeband_modality — grade-band from the engagement row, falling back
    # to k12_concepts.grade_band when the row didn't carry one.
    by_gradeband_modality = [
        {
            "grade_band": r["grade_band"],
            "modality": r["modality"],
            "avg_mastery_gain": round(float(r["avg_mastery_gain"] or 0.0), 4),
            "n": int(r["n"] or 0),
        }
        for r in _safe_read(
            _GAIN_CTE
            + """
            SELECT COALESCE(me.grade_band, kc.grade_band, 'unknown') AS grade_band,
                   me.modality,
                   AVG(g.mastery_gain) AS avg_mastery_gain,
                   COUNT(*)            AS n
            FROM material_engagement me
            LEFT JOIN gain g
                   ON g.user_id = me.user_id AND g.concept = me.concept_id
            LEFT JOIN k12_concepts kc ON kc.id = me.concept_id
            GROUP BY COALESCE(me.grade_band, kc.grade_band, 'unknown'), me.modality
            ORDER BY grade_band ASC, avg_mastery_gain DESC NULLS LAST
            """
        )
    ]

    totals_rows = _safe_read(
        """
        SELECT COUNT(*)                     AS engagements,
               COUNT(DISTINCT user_id)      AS learners,
               COUNT(DISTINCT concept_id)   AS concepts
        FROM material_engagement
        """
    )
    tr = totals_rows[0] if totals_rows else {}
    totals = {
        "engagements": int(tr.get("engagements") or 0),
        "learners": int(tr.get("learners") or 0),
        "concepts": int(tr.get("concepts") or 0),
    }

    return {
        "by_modality": by_modality,
        "by_concept_modality": by_concept_modality,
        "by_gradeband_modality": by_gradeband_modality,
        "totals": totals,
        "authority": "material_engagement + experiment_trajectories",
        "note": "observational — learner-chosen modality, never feeds the MAB",
        "semantic_version": "1.0",
    }
