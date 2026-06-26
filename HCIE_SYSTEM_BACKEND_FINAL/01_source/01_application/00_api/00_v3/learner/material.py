"""Learner-facing learning_materials endpoints.

These return instructional content distinct from gradeable tasks. A material
has no answer, no correctness signal, and never goes through the MAB scorer
— it's meant to be *read* (or watched / heard / explored) before the learner
attempts the practice tasks for a concept.

Endpoints:

- ``GET /v3/learner/material?concept_id=<id>&language=<lang>`` — list
  materials available for the concept, ordered by difficulty then id.
- ``GET /v3/learner/material/{material_id}`` — fetch a single material in
  full (used by the ``/learn`` page when a learner picks one to study).

The endpoints are deliberately unauthenticated at the row level: materials
are concept-scoped, not learner-scoped. The frontend already gates access
to concepts via the existing locked-concept logic on ``/learn``.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.dependencies.rbac import require_student
from app.api.v3.dependencies_its import get_its_runtime_service


router = APIRouter(prefix="/material", tags=["v3-learner-material"])


class LearningMaterialView(BaseModel):
    id: str
    concept_id: str
    language: str
    modality: str
    archetype_tags: List[str] = Field(default_factory=list)
    title: str
    body: Optional[str] = None
    media_url: Optional[str] = None
    transcript: Optional[str] = None
    estimated_minutes: int = 5
    difficulty: float = 0.4
    prerequisites_assumed: List[str] = Field(default_factory=list)
    # Archetype personalization (observational UX only — never feeds the MAB):
    # how well this material's archetype_tags match the learner's self-reported
    # profile. 0.0 when the learner hasn't onboarded.
    match_score: float = 0.0
    best_fit: bool = False


def _archetype_score_map(store: Any, user_id: str) -> Dict[str, float]:
    """Flatten a learner's archetype profile into the material-tag vocabulary,
    e.g. ``{'vark_visual': 0.6, 'motiv_explorer': 0.2, ...}`` — so a material
    tagged ``vark_visual`` scores the learner's visual weight. Empty dict when
    the learner has no profile (not onboarded) → ordering stays default."""
    try:
        row = store.execute_read(
            """
            SELECT vark_scores, behav_scores, motiv_scores
            FROM user_archetype_profile
            WHERE user_id::text = %s
            """,
            (str(user_id),),
            fetch_one=True,
        )
    except Exception:
        return {}
    if not row:
        return {}
    out: Dict[str, float] = {}
    for prefix, col in (("vark", "vark_scores"), ("behav", "behav_scores"), ("motiv", "motiv_scores")):
        scores = row.get(col)
        if isinstance(scores, str):
            try:
                scores = json.loads(scores)
            except Exception:
                scores = {}
        if isinstance(scores, dict):
            for k, val in scores.items():
                try:
                    out[f"{prefix}_{k}"] = float(val)
                except (TypeError, ValueError):
                    pass
    return out


def _row_to_view(row: Dict[str, Any]) -> LearningMaterialView:
    """Normalize a postgres row into the response shape. JSONB columns can
    come back as either ``list`` / ``dict`` (when the driver decoded them) or
    as ``str`` (psycopg2 ``RealDictCursor`` quirk under some compose
    configs), so we handle both.
    """

    def _as_list(value: Any) -> List[str]:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return []
        if isinstance(value, list):
            return [str(x) for x in value]
        return []

    return LearningMaterialView(
        id=str(row["id"]),
        concept_id=str(row["concept_id"]),
        language=str(row.get("language") or "en"),
        modality=str(row.get("modality") or "reading"),
        archetype_tags=_as_list(row.get("archetype_tags")),
        title=str(row.get("title") or ""),
        body=row.get("body"),
        media_url=row.get("media_url"),
        transcript=row.get("transcript"),
        estimated_minutes=int(row.get("estimated_minutes") or 5),
        difficulty=float(row.get("difficulty") or 0.4),
        prerequisites_assumed=_as_list(row.get("prerequisites_assumed")),
    )


@router.get("", response_model=List[LearningMaterialView])
async def list_materials(
    concept_id: str = Query(..., min_length=1, description="K-12 concept id, e.g. 'k2_algorithms'"),
    language: Optional[List[str]] = Query(
        None,
        description=(
            "Optional language filter. Accepts repeated query params, e.g. "
            "?language=en&language=id. Empty/missing returns any language."
        ),
    ),
    user: Dict[str, Any] = Depends(require_student),
    its=Depends(get_its_runtime_service),
):
    lang_filter: Optional[List[str]] = None
    if language:
        lang_filter = [l.strip().lower() for l in language if l and l.strip()] or None

    store = its.postgres_store
    try:
        if lang_filter:
            rows = store.execute_read(
                """
                SELECT id, concept_id, language, modality, archetype_tags, title,
                       body, media_url, transcript, estimated_minutes, difficulty,
                       prerequisites_assumed
                FROM learning_materials
                WHERE concept_id = %s AND language = ANY(%s)
                ORDER BY difficulty ASC, id ASC
                """,
                (concept_id, lang_filter),
            )
        else:
            rows = store.execute_read(
                """
                SELECT id, concept_id, language, modality, archetype_tags, title,
                       body, media_url, transcript, estimated_minutes, difficulty,
                       prerequisites_assumed
                FROM learning_materials
                WHERE concept_id = %s
                ORDER BY difficulty ASC, id ASC
                """,
                (concept_id,),
            )
    except Exception as exc:  # pragma: no cover — defensive log path
        # We deliberately surface a 200 with an empty list rather than a 5xx:
        # the frontend's "Material → Practice" flow falls back gracefully to
        # the Practice tab when materials are unavailable, while a 5xx would
        # break the whole /learn page.
        its.logger.warning(
            "list_materials_failed",
            concept_id=concept_id,
            error=str(exc),
        )
        return []

    views = [_row_to_view(r) for r in (rows or [])]

    # Archetype-aware ordering: prefer materials whose archetype_tags match the
    # learner's self-reported profile (a visual learner sees video/diagram first,
    # a read/write learner sees text first, etc.). Pure study-content
    # personalization — materials never go through the MAB or write any outcome
    # table, so this cannot affect the sealed evaluation or the representation
    # bandit. Falls back to the default (difficulty, id) order when the learner
    # has no profile.
    user_id = user.get("id") or user.get("user_id")
    score_map = _archetype_score_map(store, user_id) if user_id else {}
    if score_map and views:
        for v in views:
            v.match_score = round(sum(score_map.get(t, 0.0) for t in v.archetype_tags), 4)
        views.sort(key=lambda v: (-v.match_score, v.difficulty, v.id))
        if views[0].match_score > 0:
            views[0].best_fit = True
    return views


@router.get("/{material_id}", response_model=LearningMaterialView)
async def get_material(
    material_id: str,
    user: Dict[str, Any] = Depends(require_student),
    its=Depends(get_its_runtime_service),
):
    store = its.postgres_store
    row = store.execute_read(
        """
        SELECT id, concept_id, language, modality, archetype_tags, title,
               body, media_url, transcript, estimated_minutes, difficulty,
               prerequisites_assumed
        FROM learning_materials
        WHERE id = %s
        """,
        (material_id,),
        fetch_one=True,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Material not found")
    return _row_to_view(row)
