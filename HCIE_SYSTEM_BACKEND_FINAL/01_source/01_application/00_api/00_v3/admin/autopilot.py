"""Autopilot — drive a real ITS learner from cold-start to mastered.

Why this endpoint exists
========================

For demos, screenshots and stakeholder walk-throughs we need to *see* a
learner cross from "knows nothing" to "fully mastered" inside one sitting.
A real human would need ~30–150 attempts; autopilot performs that
end-to-end on their behalf using the exact same code paths a human
exercises: ``ItsRuntimeService.recommend`` for the next concept/task and
``ItsRuntimeService.submit_attempt`` for the answer. The result is
indistinguishable from a real session — every attempt produces a
``CognitionUpdated`` event, lands in ``experiment_trajectories`` with
``experiment_run_id = 'live::<user_id>'``, and updates the user's
``learning_state`` row.

Correctness model
-----------------

A two-parameter Rasch-style sigmoid:

    P(correct) = sigmoid( (ability + mastery_bonus * mastery_after) - difficulty )

* ``ability`` — the learner's intrinsic skill. 0.0 = average; 0.5 = strong.
* ``mastery_bonus`` — how much the *current* mastery for the picked
  concept should boost P(correct). Default 1.0 means: as the learner
  practices a concept, they get visibly better at it (which is what
  produces the 0 → mastered arc in the journey chart).
* ``difficulty`` — the task's catalogued difficulty (already 0..1).

This is intentionally not a research-grade learner model — its only job
is to produce a believable mastery curve so the visualisations populate.
The endpoint is gated behind ``require_admin`` so it cannot be invoked
by ordinary learners; it lives in ``/v3/admin/`` for that reason.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import random
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies.rbac import require_researcher_or_admin
from app.api.v3.dependencies_its import get_its_runtime_service
from storage.postgres_store.interaction_store import PostgresInteractionStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/autopilot", tags=["v3-admin-autopilot"])

# Rate limit: max autopilot invocations per actor per rolling hour.
_AUTOPILOT_MAX_PER_HOUR = 5
_autopilot_timestamps: Dict[str, List[float]] = {}


def _check_autopilot_rate(actor_key: str) -> None:
    now = time.monotonic()
    window = 3600.0
    hits = _autopilot_timestamps.setdefault(actor_key, [])
    _autopilot_timestamps[actor_key] = [t for t in hits if now - t < window]
    if len(_autopilot_timestamps[actor_key]) >= _AUTOPILOT_MAX_PER_HOUR:
        raise HTTPException(
            status_code=429,
            detail=f"Autopilot rate limit: max {_AUTOPILOT_MAX_PER_HOUR} runs per hour per user",
        )
    _autopilot_timestamps[actor_key].append(now)


def _audit_autopilot(actor: str, target_user_id: str, req: "AutopilotRequest", result: Dict[str, Any]) -> None:
    try:
        store = PostgresInteractionStore()
        store.execute_write(
            """
            CREATE TABLE IF NOT EXISTS admin_audit_log (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                prior_state JSONB NOT NULL DEFAULT '{}'::jsonb,
                result JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
            (),
        )
        store.execute_write(
            """
            INSERT INTO admin_audit_log (actor, action, reason, prior_state, result)
            VALUES (%s, %s, %s, %s::jsonb, %s::jsonb)
            """,
            (
                actor,
                "autopilot_run",
                f"autopilot target={target_user_id}",
                json.dumps({"target_user_id": target_user_id, "request": req.model_dump()}, default=str),
                json.dumps(result, default=str),
            ),
        )
    except Exception as exc:
        logger.warning("autopilot audit write failed: %s", exc)


# ── Request / response models ────────────────────────────────────────────────

class AutopilotRequest(BaseModel):
    """Run N recommend+attempt cycles for a single user.

    ``ability``, ``mastery_bonus`` and ``response_time_seconds`` shape the
    synthetic responses; the bandit / task selection itself is fully real.
    ``stop_when_mastered`` aborts early once the curriculum-complete
    threshold is reached, so a strong learner doesn't keep grinding.
    """

    target_attempts: int = Field(30, ge=1, le=400, description="Maximum attempts")
    ability: float = Field(
        0.4, ge=-2.0, le=2.0,
        description="Learner skill on the Rasch scale; 0 = average",
    )
    mastery_bonus: float = Field(
        1.0, ge=0.0, le=3.0,
        description=(
            "How much current mastery should boost P(correct); higher values "
            "produce steeper mastery curves."
        ),
    )
    response_time_seconds: float = Field(
        12.0, ge=0.5, le=120.0,
        description="Synthetic response time recorded on each attempt",
    )
    mastered_threshold: float = Field(
        0.85, ge=0.5, le=1.0,
        description="Per-concept threshold considered 'mastered'",
    )
    stop_when_mastered: bool = Field(
        True,
        description=(
            "Stop early when every K-12 concept the bandit has touched is "
            "at/above ``mastered_threshold`` for at least 3 consecutive attempts."
        ),
    )
    seed: Optional[int] = Field(
        None, description="Optional RNG seed for reproducible runs",
    )


class AutopilotStep(BaseModel):
    step: int
    concept: Optional[str]
    task_id: Optional[str]
    difficulty: Optional[float]
    p_correct: float
    correct: bool
    mastery_after: Optional[float]


class AutopilotResponse(BaseModel):
    status: str
    user_id: str
    attempts_made: int
    concepts_touched: List[str]
    concepts_mastered: List[str]
    final_mastery: Dict[str, float]
    steps: List[AutopilotStep]
    duration_seconds: float
    stopped_reason: str


# ── Helpers ──────────────────────────────────────────────────────────────────

def _sigmoid(x: float) -> float:
    if x > 35:
        return 1.0
    if x < -35:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def _looks_correct_for_task(task_payload: Dict[str, Any]) -> Any:
    """Best-effort correct answer to pass to ``submit_attempt``.

    The brain trusts the ``correct`` boolean we pass in for grading
    (bypassing per-task grading code paths that would otherwise depend on
    the task representation). We still hand it a sensible ``answer`` so
    audit logs read as intended.
    """

    # MCQ-style → first declared correct option index if available
    choices = task_payload.get("choices") or []
    content = task_payload.get("content") or {}
    correct_idx = content.get("correct_index")
    if isinstance(correct_idx, int) and 0 <= correct_idx < len(choices):
        return choices[correct_idx]
    if choices:
        return choices[0]
    return content.get("solution") or "autopilot"


# ── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/{user_id}", response_model=AutopilotResponse)
async def run_autopilot(
    user_id: str,
    req: AutopilotRequest,
    its=Depends(get_its_runtime_service),
    actor=Depends(require_researcher_or_admin),
) -> AutopilotResponse:
    """Drive ``user_id`` through ``target_attempts`` real ITS cycles.

    Each iteration:

    1. Calls ``its.recommend(user_id)`` — the bandit picks a concept
       (respecting prerequisites and locks) and a task.
    2. Computes ``p = sigmoid(ability + mastery_bonus * mastery - difficulty)``.
    3. Samples ``correct = rng() < p``.
    4. Calls ``its.submit_attempt(..., correct=correct, ...)``.

    Mastery climbs naturally because the brain updates the learner state
    on every attempt; once a concept stabilises above ``mastered_threshold``
    the bandit naturally rotates to its successor in the prereq DAG,
    producing the curriculum-traversal narrative the journey UI plots.
    """
    actor_key = str(actor.get("email") or actor.get("id") or actor.get("user_id") or "unknown")
    _check_autopilot_rate(actor_key)

    rng = random.Random(req.seed)
    started = time.monotonic()

    steps: List[AutopilotStep] = []
    mastery_per_concept: Dict[str, float] = {}
    consecutive_above_threshold: Dict[str, int] = {}
    concepts_touched: List[str] = []
    stopped_reason = "target_attempts"

    for i in range(req.target_attempts):
        try:
            rec = its.recommend(user_id)
        except Exception as exc:  # noqa: BLE001 — keep the loop robust
            logger.warning(
                "autopilot_recommend_failed user=%s step=%s err=%s",
                user_id, i, exc,
            )
            stopped_reason = f"recommend_failed: {type(exc).__name__}"
            break

        # Normalize rec into a dict so we tolerate either dataclass or dict.
        if hasattr(rec, "__dict__"):
            rec_d = {k: v for k, v in rec.__dict__.items() if not k.startswith("_")}
        else:
            rec_d = dict(rec or {})

        concept = rec_d.get("recommended_concept") or rec_d.get("concept_id")
        task_id = rec_d.get("task_id")
        difficulty = rec_d.get("difficulty") or 0.5
        if not concept or not task_id:
            stopped_reason = "no_task_returned"
            break

        if concept not in concepts_touched:
            concepts_touched.append(concept)

        current_mastery = mastery_per_concept.get(concept, 0.0)
        # Rasch-style logit, ability + bonus*mastery − difficulty.
        logit = req.ability + req.mastery_bonus * current_mastery - float(difficulty)
        p_correct = _sigmoid(logit)
        correct = rng.random() < p_correct

        try:
            result = its.submit_attempt(
                user_id,
                task_id=task_id,
                concept_id=concept,
                answer=_looks_correct_for_task(rec_d),
                correct=correct,
                response_time=req.response_time_seconds,
                event_id=str(uuid.uuid4()),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "autopilot_attempt_failed user=%s step=%s err=%s",
                user_id, i, exc,
            )
            stopped_reason = f"attempt_failed: {type(exc).__name__}"
            break

        mastery_after = getattr(result, "mastery", None)
        if mastery_after is None and isinstance(getattr(result, "payload", None), dict):
            mastery_after = result.payload.get("mastery")
        if mastery_after is not None:
            mastery_per_concept[concept] = float(mastery_after)

        if mastery_after is not None and float(mastery_after) >= req.mastered_threshold:
            consecutive_above_threshold[concept] = consecutive_above_threshold.get(concept, 0) + 1
        else:
            consecutive_above_threshold[concept] = 0

        steps.append(AutopilotStep(
            step=i + 1,
            concept=concept,
            task_id=task_id,
            difficulty=float(difficulty),
            p_correct=round(p_correct, 4),
            correct=bool(correct),
            mastery_after=(float(mastery_after) if mastery_after is not None else None),
        ))

        # Tiny yield so we don't monopolise the event loop on long runs.
        await asyncio.sleep(0)

        # Early-stop heuristic: every touched concept is sustainably mastered.
        if (
            req.stop_when_mastered
            and concepts_touched
            and all(consecutive_above_threshold.get(c, 0) >= 3 for c in concepts_touched)
        ):
            stopped_reason = "all_touched_concepts_mastered"
            break

    concepts_mastered = [
        c for c, m in mastery_per_concept.items() if m >= req.mastered_threshold
    ]

    response = AutopilotResponse(
        status="ok",
        user_id=user_id,
        attempts_made=len(steps),
        concepts_touched=concepts_touched,
        concepts_mastered=concepts_mastered,
        final_mastery={k: round(v, 4) for k, v in mastery_per_concept.items()},
        steps=steps,
        duration_seconds=round(time.monotonic() - started, 3),
        stopped_reason=stopped_reason,
    )
    _audit_autopilot(actor_key, user_id, req, response.model_dump())
    return response
