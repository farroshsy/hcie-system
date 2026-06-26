"""
System Health API - Infrastructure health checks
"""

from fastapi import APIRouter
from app.api.routes.health.health import router as health_router

router = APIRouter()

# Mount existing health router - clean path
router.include_router(health_router)
