"""POST /v3/its/attempt — canonical ITS mutation ingress (H1 via spine)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies.rbac import require_student
from app.api.v3.dependencies_its import get_its_runtime_service
from core.determinism.deterministic_config import DeterministicModeConfig

router = APIRouter()


class AttemptRequest(BaseModel):
    task_id: str
    concept_id: str
    answer: Any
    correct: Optional[bool] = None
    response_time: float = 10.0
    signal_detail: Dict[str, Any] = Field(default_factory=dict)
    event_id: Optional[str] = None
    deterministic: bool = False
    seed: int = 42


class AttemptResponse(BaseModel):
    user_id: str
    event_id: str
    concept_id: str
    correct: bool
    mastery: Optional[float]
    payload: Dict[str, Any]
    semantic_version: str = "1.0"


@router.post("/attempt", response_model=AttemptResponse)
async def submit_attempt(
    body: AttemptRequest,
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

    result = its.submit_attempt(
        user_id,
        task_id=body.task_id,
        concept_id=body.concept_id,
        answer=body.answer,
        correct=body.correct,
        response_time=body.response_time,
        signal_detail=body.signal_detail,
        event_id=body.event_id,
        deterministic=deterministic,
    )
    return AttemptResponse(
        user_id=result.user_id,
        event_id=result.event_id,
        concept_id=result.concept_id,
        correct=result.correct,
        mastery=result.mastery,
        payload=result.payload,
        semantic_version=result.semantic_version,
    )
