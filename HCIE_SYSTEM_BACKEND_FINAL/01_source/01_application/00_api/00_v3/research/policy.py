"""
Policy Research API (Policy Telemetry Domain)

Policy telemetry for research validation.
Authority State: experimental → converging → authoritative
Runtime Contract Version: 1.0
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.projection import PolicyProjection


router = APIRouter(prefix="/research/policy", tags=["research-policy"])

policy_router = router


# Pydantic models for API
class PolicyTelemetryResponse(BaseModel):
    """Policy telemetry response."""
    user_id: str
    policy_metrics: Dict[str, Any]
    semantic_version: str = "1.0"


class PolicyTelemetryIngest(BaseModel):
    """Inbound telemetry payload from v3_client."""
    telemetry_data: Optional[Dict[str, Any]] = None


class PolicyTelemetryAck(BaseModel):
    """Acknowledgement for inbound policy telemetry."""
    status: str = "accepted"
    semantic_version: str = "1.0"


# Dependency injection
from app.api.v3.dependencies import get_policy_projection


@router.post("", response_model=PolicyTelemetryAck, status_code=202)
async def ingest_policy_telemetry(payload: PolicyTelemetryIngest):
    """
    Accept policy telemetry from internal consumers (v3_client).

    This is a fire-and-forget ingest surface — the payload is acknowledged
    but not persisted here; consumers that need durable storage should write
    directly via the canonical outbox path.
    """
    return PolicyTelemetryAck(status="accepted")


@router.get("/telemetry/{user_id}", response_model=PolicyTelemetryResponse)
async def get_policy_telemetry(
    user_id: str,
    projection: PolicyProjection = Depends(get_policy_projection)
):
    """
    Get policy telemetry for a user.

    READ fresh from source every time.
    NO caching as authority.
    NO temporal memory ownership.
    """
    try:
        telemetry = projection.project_policy_telemetry(user_id)
        return telemetry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
