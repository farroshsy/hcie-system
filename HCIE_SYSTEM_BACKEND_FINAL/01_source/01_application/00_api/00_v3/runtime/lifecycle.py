"""
LifecycleRuntimeAPI (Lifecycle Authority Domain)

Lifecycle authority domain - exposes lifecycle state and transitions.
Authority State: experimental → converging → authoritative
Runtime Contract Version: 1.0
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.projection import LifecycleProjection


router = APIRouter(prefix="/runtime/lifecycle", tags=["lifecycle-runtime"])

lifecycle_router = router


# Pydantic models for API
class LifecycleStateResponse(BaseModel):
    """Lifecycle state response."""
    user_id: str
    lifecycle_state: str
    state_transitions: list[Dict[str, Any]]
    semantic_version: str = "1.0"


# Dependency injection
from app.api.v3.dependencies import get_lifecycle_projection


@router.get("/health")
async def runtime_health_check():
    """Runtime health check endpoint with dependency checks"""
    from app.runtime.composition import build_api_runtime
    from config.env import settings
    import time

    health_status = {
        "status": "healthy",
        "runtime": "unified-brain",
        "semantic_version": "1.0",
        "timestamp": time.time(),
        "checks": {}
    }

    # Check PostgreSQL
    try:
        from app.infrastructure.database import get_postgres_store
        postgres = get_postgres_store()
        await postgres.execute("SELECT 1")
        health_status["checks"]["postgres"] = {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["postgres"] = {"status": "unhealthy", "error": str(e)}

    # Check Redis
    try:
        from app.infrastructure.redis_client import get_redis_client
        redis = get_redis_client()
        await redis.ping()
        health_status["checks"]["redis"] = {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}

    # Check Runtime Service
    try:
        runtime = build_api_runtime(settings)
        health_status["checks"]["runtime"] = {"status": "healthy"}
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["runtime"] = {"status": "unhealthy", "error": str(e)}

    return health_status


@router.get("/metrics")
async def runtime_metrics():
    """Runtime metrics endpoint for Prometheus"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/state/{user_id}", response_model=LifecycleStateResponse)
async def get_lifecycle_state(
    user_id: str,
    projection: LifecycleProjection = Depends(get_lifecycle_projection)
):
    """
    Get lifecycle state for a user.
    
    READ fresh from source every time.
    NO caching as authority.
    NO temporal memory ownership.
    """
    try:
        state = projection.project_lifecycle_state(user_id)
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
