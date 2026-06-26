"""
TrajectoryRuntimeAPI (Trajectory Authority Domain)

Trajectory authority domain - exposes trajectory state and history.
Authority State: experimental → converging → authoritative
Runtime Contract Version: 1.0
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.projection import TrajectoryProjection


router = APIRouter(prefix="/runtime/trajectory", tags=["trajectory-runtime"])

trajectory_router = router


# Pydantic models for API
class TrajectoryStateResponse(BaseModel):
    """Trajectory state response."""
    user_id: str
    trajectory_data: list[float]
    trajectory_metadata: Dict[str, Any]
    semantic_version: str = "1.0"


# Dependency injection
from app.api.v3.dependencies import get_trajectory_projection


@router.get("/state/{user_id}", response_model=TrajectoryStateResponse)
async def get_trajectory_state(
    user_id: str,
    projection: TrajectoryProjection = Depends(get_trajectory_projection)
):
    """
    Get trajectory state for a user.
    
    READ fresh from source every time.
    NO caching as authority.
    NO temporal memory ownership.
    """
    try:
        state = projection.project_trajectory_state(user_id)
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
