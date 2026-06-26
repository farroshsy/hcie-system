"""
Event Runtime API (Event Authority Domain)

Event authority domain - event propagation visibility for operational monitoring.
Authority State: converging → authoritative
Runtime Contract Version: 1.0
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.projection import EventProjection


router = APIRouter(prefix="/runtime/events", tags=["event-runtime"])

event_router = router


# Pydantic models for API
class EventPropagationResponse(BaseModel):
    """Event propagation status response."""
    outbox_state: Dict[str, Any]
    kafka_lag: int
    dlq_state: Dict[str, Any]
    semantic_version: str = "1.0"


# Dependency injection for projection service
def get_event_projection() -> EventProjection:
    """Dependency injection for event projection service (wired via DI)."""
    from app.api.v3.dependencies import get_event_projection as get_projection
    return get_projection()


@router.get("/propagation", response_model=EventPropagationResponse)
async def get_event_propagation_status(
    context: Optional[Dict[str, Any]] = None,
    projection: EventProjection = Depends(get_event_projection)
):
    """
    Get event propagation status.
    
    API: GET /v3/runtime/events/propagation
    
    Parameters:
    - context: Optional context (e.g., experiment_run_id for parameterized runtime sessions)
    
    Returns:
    - EventPropagationResponse with outbox_state, kafka_lag, dlq_state, semantic_version
    
    Authority State: experimental
    Runtime Contract Version: 1.0
    """
    try:
        # Project event propagation status via projection service (stateless view)
        status = projection.project_event_propagation_status()
        
        return EventPropagationResponse(
            outbox_state=status.outbox_state,
            kafka_lag=status.kafka_lag,
            dlq_state=status.dlq_state,
            semantic_version=status.semantic_version
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Export router for registration
events_router = router
