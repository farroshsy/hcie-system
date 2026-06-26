"""
ReplayRuntimeAPI (Replay Authority Domain)

Replay authority domain - exposes replay state and results for research validation.
Authority State: experimental → converging → authoritative
Runtime Contract Version: 1.0
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.projection import ReplayProjection


router = APIRouter(prefix="/runtime/replay", tags=["replay-runtime"])

replay_router = router


# Pydantic models for API
class ReplayStateResponse(BaseModel):
    """Replay state response."""
    replay_id: str
    replay_status: str
    replay_results: Dict[str, Any]
    semantic_version: str = "1.0"


class ReplayRequest(BaseModel):
    """Replay request."""
    snapshot_id: str
    replay_config: Optional[Dict[str, Any]] = None


class BatchReplayTriggerRequest(BaseModel):
    experiment_run_id: str
    num_users: int = 10


# Dependency injection
from app.api.v3.dependencies import get_replay_projection


@router.get("/status/{replay_id}", response_model=ReplayStateResponse)
async def get_replay_status(
    replay_id: str,
    projection: ReplayProjection = Depends(get_replay_projection)
):
    """
    Get replay status for a replay ID.
    
    READ fresh from source every time.
    NO caching as authority.
    NO temporal memory ownership.
    """
    try:
        state = projection.project_replay_status(replay_id)
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger")
async def trigger_replay(
    request: BatchReplayTriggerRequest,
):
    """
    Trigger ReplayEngine batch replay.

    Slice 4c replaces the old placeholder status projection with the real
    replay authority path.
    """
    try:
        from app.api.v3.service.router import _batch_replay

        result = _batch_replay(request.experiment_run_id, request.num_users)
        return {
            "status": "ok",
            "experiment_run_id": request.experiment_run_id,
            "result": result,
            "semantic_version": "1.0",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
