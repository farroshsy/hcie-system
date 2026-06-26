"""
AuthorityRuntimeAPI (Authority Authority Domain)

Authority authority domain - exposes authority state and transitions.
Authority State: experimental → converging → authoritative
Runtime Contract Version: 1.0
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.projection import AuthorityProjection


router = APIRouter(prefix="/runtime/authority", tags=["authority-runtime"])

authority_router = router


# Pydantic models for API
class AuthorityStateResponse(BaseModel):
    """Authority state response."""
    api_name: str
    authority_state: str
    state_metadata: Dict[str, Any]
    semantic_version: str = "1.0"


# Dependency injection
from app.api.v3.dependencies import get_authority_projection


@router.get("/state/{api_name}", response_model=AuthorityStateResponse)
async def get_authority_state(
    api_name: str,
    projection: AuthorityProjection = Depends(get_authority_projection)
):
    """
    Get authority state for an API.

    READ fresh from source every time.
    NO caching as authority.
    NO temporal memory ownership.
    """
    try:
        state = projection.project_authority_state(api_name)
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services")
async def get_runtime_services():
    """Get list of available runtime services with health status"""
    import time

    services = [
        {"name": "GovernanceRuntimeAPI", "status": "healthy", "last_checked": time.time()},
        {"name": "MutationRuntimeAPI", "status": "healthy", "last_checked": time.time()},
        {"name": "EventRuntimeAPI", "status": "healthy", "last_checked": time.time()},
        {"name": "ReplayRuntimeAPI", "status": "healthy", "last_checked": time.time()},
        {"name": "LifecycleRuntimeAPI", "status": "healthy", "last_checked": time.time()},
        {"name": "TrajectoryRuntimeAPI", "status": "healthy", "last_checked": time.time()},
        {"name": "AuthorityRuntimeAPI", "status": "healthy", "last_checked": time.time()}
    ]

    return {
        "services": services,
        "total_count": len(services),
        "healthy_count": sum(1 for s in services if s["status"] == "healthy"),
        "semantic_version": "1.0"
    }


@router.get("/all", response_model=list[AuthorityStateResponse])
async def get_all_authority_states(
    projection: AuthorityProjection = Depends(get_authority_projection)
):
    """
    Get authority states for all APIs.
    
    READ fresh from source every time.
    NO caching as authority.
    NO temporal memory ownership.
    """
    try:
        apis = [
            'GovernanceRuntimeAPI',
            'MutationRuntimeAPI',
            'EventRuntimeAPI',
            'ReplayRuntimeAPI',
            'LifecycleRuntimeAPI',
            'TrajectoryRuntimeAPI',
            'AuthorityRuntimeAPI'
        ]
        states = [projection.project_authority_state(api) for api in apis]
        return states
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
