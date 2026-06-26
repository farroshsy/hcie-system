"""
Attribution Research API (Attribution Telemetry Domain)

Attribution telemetry for research validation.
Authority State: experimental → converging → authoritative
Runtime Contract Version: 1.0
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.projection import AttributionProjection


router = APIRouter(prefix="/research/attribution", tags=["research-attribution"])

attribution_router = router


# Pydantic models for API
class AttributionTelemetryResponse(BaseModel):
    """Attribution telemetry response."""
    user_id: str
    attribution_metrics: Dict[str, Any]
    semantic_version: str = "1.0"


# Dependency injection
from app.api.v3.dependencies import get_attribution_projection


@router.get("/telemetry/{user_id}", response_model=AttributionTelemetryResponse)
async def get_attribution_telemetry(
    user_id: str,
    projection: AttributionProjection = Depends(get_attribution_projection)
):
    """
    Get attribution telemetry for a user.
    
    READ fresh from source every time.
    NO caching as authority.
    NO temporal memory ownership.
    """
    try:
        telemetry = projection.project_attribution_telemetry(user_id)
        return telemetry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
