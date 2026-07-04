"""
UX API Router - User-friendly endpoints (V2 Production)
"""

from fastapi import APIRouter
from .endpoints import dashboard, learning
from .endpoints import dashboard_v2, learning_v2

router = APIRouter(prefix="/ux", tags=["ux"])

# Mount V2 production endpoints
router.include_router(dashboard_v2.router)
router.include_router(learning_v2.router)

# Keep V1 for backward compatibility (deprecated)
router.include_router(dashboard.router, prefix="/v1", tags=["ux-deprecated"])
router.include_router(learning.router, prefix="/v1", tags=["ux-deprecated"])
