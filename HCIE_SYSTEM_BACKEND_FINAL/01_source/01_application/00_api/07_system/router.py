"""
System API Router - Infrastructure and performance monitoring
"""

from fastapi import APIRouter
from .endpoints import health, performance, tiered

router = APIRouter(prefix="/system", tags=["system"])

# Mount system endpoints
router.include_router(health.router)
router.include_router(performance.router)
router.include_router(tiered.router)
