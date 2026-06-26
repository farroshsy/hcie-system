"""
ObjectiveRuntimeAPI (Objective Authority Domain)

Objective function and canonical state health for system optimization.
Authority State: experimental → converging → authoritative
Runtime Contract Version: 1.0
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.projection import ObjectiveProjection


router = APIRouter(prefix="/runtime/objective", tags=["objective-runtime"])

objective_router = router


# Pydantic models for API
class ObjectiveStateResponse(BaseModel):
    """Objective function state response."""
    objective_function_value: float
    canonical_state_health: Dict[str, Any]
    research_metrics: Dict[str, float]
    semantic_version: str = "1.0"


# Dependency injection
from app.api.v3.dependencies import get_objective_projection


@router.get("/state", response_model=ObjectiveStateResponse)
async def get_objective_state(
    projection: ObjectiveProjection = Depends(get_objective_projection)
):
    """
    Get objective function state and canonical state health.
    
    READ fresh from source every time.
    NO caching as authority.
    NO temporal memory ownership.
    """
    try:
        state = projection.project_objective_state()
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
