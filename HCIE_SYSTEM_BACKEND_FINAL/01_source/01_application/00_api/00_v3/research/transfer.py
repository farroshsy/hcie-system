"""
Transfer Research API (Transfer Telemetry Domain)

Transfer learning telemetry for research validation.
Authority State: experimental → converging → authoritative
Runtime Contract Version: 1.0
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.projection import TransferProjection


router = APIRouter(prefix="/research/transfer", tags=["research-transfer"])

transfer_router = router


# Pydantic models for API
class TransferTelemetryResponse(BaseModel):
    """Transfer telemetry response."""
    user_id: str
    transfer_metrics: Dict[str, Any]
    semantic_version: str = "1.0"


# Dependency injection
from app.api.v3.dependencies import get_transfer_projection


@router.get("/telemetry/{user_id}", response_model=TransferTelemetryResponse)
async def get_transfer_telemetry(
    user_id: str,
    projection: TransferProjection = Depends(get_transfer_projection)
):
    """
    Get transfer learning telemetry for a user.
    
    READ fresh from source every time.
    NO caching as authority.
    NO temporal memory ownership.
    """
    try:
        telemetry = projection.project_transfer_telemetry(user_id)
        return telemetry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
