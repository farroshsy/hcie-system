"""
Admin API Router - Internal system administration and debugging
"""

from fastapi import APIRouter
from app.api.routes.admin.tiered import router as tiered_router

router = APIRouter(prefix="/admin", tags=["admin"])

# Mount tiered admin routes (clean - no internal prefix)
router.include_router(tiered_router)

# Add simple admin endpoints
@router.get("/status")
async def admin_status():
    """Get admin system status"""
    return {
        "status": "active",
        "admin_api": "v1",
        "tiered_system": "integrated"
    }
