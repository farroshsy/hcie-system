"""POST /v3/its/recommend — canonical ITS recommendation ingress."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies.rbac import require_student
from app.api.v3.dependencies_its import get_its_runtime_service
from app.runtime.its_runtime_service import RuntimeDegraded
from core.determinism.deterministic_config import DeterministicModeConfig

router = APIRouter()


class RecommendRequest(BaseModel):
    """V3 ITS recommend request.

    Slice 0a (Phase 14g) hard-removed ``policy_mode`` because the brain
    ignored it and only the OTel span recorded the value, producing a
    semantic-telemetry lie. Slice 4d reintroduces a narrower ``policy``
    field — but only because ``ItsRuntimeService.recommend`` now actually
    branches on it for synthetic research cohorts and rejects the parameter
    for non-synthetic users. ``extra='forbid'`` is retained so any
    unrecognized field still produces HTTP 422.
    """

    model_config = ConfigDict(extra="forbid")

    concept_filter: Optional[List[str]] = None
    deterministic: bool = False
    seed: int = 42
    policy: Optional[str] = Field(
        default=None,
        description=(
            "Optional task selector for synthetic-cohort baseline runs. "
            "Allowed values include 'hcie', 'bandit', 'thompson', 'ucb', "
            "'epsilon_greedy', 'mastery_greedy', 'zpd_aligned', "
            "'uncertainty_reduction', 'random', and 'static'. "
            "Rejected for non-synthetic user IDs."
        ),
    )
    language: Optional[List[str]] = Field(
        default=None,
        description=(
            "Optional language filter for task content. Accepts a list of "
            "ISO-639-1 codes such as ['en'], ['id'], or ['en','id']. When "
            "omitted, the recommend service returns tasks in any seeded "
            "language (current production: 'en' + selected 'id' siblings). "
            "If the filter yields zero rows for a concept, the service "
            "transparently falls back to language-agnostic selection so "
            "the learner is never blocked on the language preference."
        ),
    )


class RecommendResponse(BaseModel):
    user_id: str
    task_id: Optional[str]
    concept_id: Optional[str]
    representation: Optional[str]
    difficulty: Optional[float]
    question_text: Optional[str]
    choices: List[Any] = Field(default_factory=list)
    selection_metrics: Dict[str, Any]
    kind: Optional[str] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    transcript: Optional[str] = None
    governance: Dict[str, Any] = Field(default_factory=dict)
    cold_start: Dict[str, Any] = Field(default_factory=dict)
    deterministic_inputs_hash: Optional[str] = None
    semantic_version: str = "1.0"


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    body: RecommendRequest,
    user: Dict[str, Any] = Depends(require_student),
    its=Depends(get_its_runtime_service),
    x_deterministic: Optional[str] = Header(default=None, alias="X-HCIE-Deterministic"),
    x_deterministic_seed: Optional[str] = Header(default=None, alias="X-HCIE-Deterministic-Seed"),
):
    user_id = user.get("id") or user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User identity missing")

    deterministic = None
    if body.deterministic or (x_deterministic or "").lower() in ("1", "true", "yes"):
        seed = body.seed
        if x_deterministic_seed:
            try:
                seed = int(x_deterministic_seed)
            except ValueError:
                pass
        deterministic = DeterministicModeConfig.experiment(seed=seed)

    try:
        view = its.recommend(
            user_id,
            concept_filter=body.concept_filter,
            deterministic=deterministic,
            policy=body.policy,
            language=body.language,
        )
    except RuntimeDegraded as exc:
        if exc.reason == "policy_forbidden_for_real_user":
            raise HTTPException(
                status_code=403,
                detail={
                    "reason": exc.reason,
                    "details": exc.details,
                },
            ) from exc
        if exc.reason == "policy_not_supported":
            raise HTTPException(
                status_code=422,
                detail={
                    "reason": exc.reason,
                    "details": exc.details,
                },
            ) from exc
        if exc.reason == "concept_locked":
            raise HTTPException(
                status_code=409,
                detail={
                    "reason": exc.reason,
                    "details": exc.details,
                },
            ) from exc
        raise HTTPException(
            status_code=503,
            detail={
                "reason": exc.reason,
                "details": exc.details,
                "policy_type": "degraded",
            },
        ) from exc

    return RecommendResponse(
        user_id=view.user_id,
        task_id=view.task_id,
        concept_id=view.concept_id,
        representation=view.representation,
        difficulty=view.difficulty,
        question_text=view.question_text,
        choices=view.choices,
        kind=view.kind,
        content=view.content,
        media_url=view.media_url,
        media_type=view.media_type,
        transcript=view.transcript,
        selection_metrics=view.selection_metrics,
        governance=view.governance,
        cold_start=view.cold_start,
        deterministic_inputs_hash=view.deterministic_inputs_hash,
        semantic_version=view.semantic_version,
    )
