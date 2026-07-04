"""GET /v3/its/progress and /v3/its/session — read-only ITS views."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies.rbac import require_student
from app.api.v3.dependencies_its import get_its_runtime_service

router = APIRouter()


class ProgressResponse(BaseModel):
    user_id: str
    concepts: Dict[str, float] = Field(default_factory=dict)
    semantic_version: str = "1.0"


class SessionResponse(BaseModel):
    """Slice 0a (Phase 14g) hard-removed ``policy_mode``: see recommend.py."""

    user_id: str
    active_concept: Optional[str] = None
    semantic_version: str = "1.0"


@router.get("/progress", response_model=ProgressResponse)
async def progress(
    user: Dict[str, Any] = Depends(require_student),
    its=Depends(get_its_runtime_service),
):
    user_id = user.get("id") or user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User identity missing")
    view = its.get_progress(user_id)
    return ProgressResponse(
        user_id=view.user_id,
        concepts=view.concepts,
        semantic_version=view.semantic_version,
    )


@router.get("/session", response_model=SessionResponse)
async def session(
    user: Dict[str, Any] = Depends(require_student),
    its=Depends(get_its_runtime_service),
):
    user_id = user.get("id") or user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User identity missing")
    view = its.get_session(user_id)
    return SessionResponse(
        user_id=view.user_id,
        active_concept=view.active_concept,
        semantic_version=view.semantic_version,
    )
