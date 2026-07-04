"""
Governance Runtime API (Governance Authority Domain)

Governance authority domain - exposes governance state and trajectory.
Authority State: converging → authoritative
Runtime Contract Version: 1.0
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.projection import GovernanceProjection


router = APIRouter(prefix="/runtime/governance", tags=["governance-runtime"])


# Pydantic models for API
class GovernanceStateResponse(BaseModel):
    """Governance state response."""
    governance_weights: Dict[str, float]
    normalization_state: Dict[str, Any]
    component_history: Dict[str, Any]
    semantic_version: str = "1.0"


class GovernanceTrajectoryResponse(BaseModel):
    """Governance trajectory response."""
    jt_trajectory: list[float]
    component_history: Dict[str, Any]
    semantic_version: str = "1.0"


# Dependency injection for projection service
def get_governance_projection() -> GovernanceProjection:
    """Dependency injection for governance projection service (wired via DI)."""
    from app.api.v3.dependencies import get_governance_projection as get_projection
    return get_projection()


@router.get("/state", response_model=GovernanceStateResponse)
async def get_governance_state(
    user_id: str,
    context: Optional[Dict[str, Any]] = None,
    projection: GovernanceProjection = Depends(get_governance_projection)
):
    """
    Get governance state for a user.
    
    API: GET /v3/runtime/governance/state
    
    Parameters:
    - user_id: User identifier
    - context: Optional context (e.g., experiment_run_id for parameterized runtime sessions)
    
    Returns:
    - GovernanceStateResponse with governance_weights, normalization_state, component_history, semantic_version
    
    Authority State: experimental
    Runtime Contract Version: 1.0
    """
    try:
        # Project governance state via projection service (stateless view)
        state = projection.project_state(user_id)
        
        return GovernanceStateResponse(
            governance_weights=state.governance_weights,
            normalization_state=state.normalization_state,
            component_history=state.component_history,
            semantic_version=state.semantic_version
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trajectory", response_model=GovernanceTrajectoryResponse)
async def get_governance_trajectory(
    user_id: str,
    context: Optional[Dict[str, Any]] = None,
    projection: GovernanceProjection = Depends(get_governance_projection)
):
    """
    Get governance trajectory for a user.
    
    API: GET /v3/runtime/governance/trajectory
    
    Parameters:
    - user_id: User identifier
    - context: Optional context (e.g., experiment_run_id for parameterized runtime sessions)
    
    Returns:
    - GovernanceTrajectoryResponse with jt_trajectory, component_history, semantic_version
    
    Authority State: experimental
    Runtime Contract Version: 1.0
    """
    try:
        # Project governance trajectory via projection service (stateless view)
        trajectory = projection.project_trajectory(user_id)
        
        return GovernanceTrajectoryResponse(
            jt_trajectory=trajectory.jt_trajectory,
            component_history=trajectory.component_history,
            semantic_version=trajectory.semantic_version
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Export router for registration
governance_router = router
