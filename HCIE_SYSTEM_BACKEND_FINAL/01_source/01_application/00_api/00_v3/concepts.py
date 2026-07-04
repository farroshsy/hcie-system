"""V3 concept availability APIs."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies.rbac import require_student
from app.api.v3.dependencies_its import get_its_runtime_service


router = APIRouter(prefix="/concepts", tags=["v3-concepts"])


class ConceptLockState(BaseModel):
    id: str
    locked: bool
    prerequisites: list[str] = Field(default_factory=list)
    missing_prereqs: list[str] = Field(default_factory=list)
    mastery_threshold: float


class ConceptLockResponse(BaseModel):
    user_id: str
    threshold: float
    concepts: list[ConceptLockState]


@router.get("/{user_id}/locked", response_model=ConceptLockResponse)
async def concept_locked_state(
    user_id: str,
    user: Dict[str, Any] = Depends(require_student),
    its=Depends(get_its_runtime_service),
):
    auth_user_id = str(user.get("id") or user.get("user_id") or "")
    if not auth_user_id:
        raise HTTPException(status_code=401, detail="User identity missing")
    if user_id != auth_user_id:
        raise HTTPException(status_code=403, detail="Cannot inspect another learner's concept locks")

    threshold = 0.6
    concepts = its.get_concept_lock_states(user_id, mastery_threshold=threshold)
    return ConceptLockResponse(user_id=user_id, threshold=threshold, concepts=concepts)
