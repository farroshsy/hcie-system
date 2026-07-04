"""
Users API Router - User management and profiles
"""

from fastapi import APIRouter
from .endpoints import profile, progress

router = APIRouter(prefix="/users", tags=["users"])

# Mount user endpoints
router.include_router(profile.router)
router.include_router(progress.router)
