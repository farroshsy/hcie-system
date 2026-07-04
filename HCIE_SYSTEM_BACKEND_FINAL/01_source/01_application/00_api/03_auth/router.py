"""
Auth API Router - Authentication and authorization
"""

from fastapi import APIRouter
from .endpoints import register, login, refresh, me

router = APIRouter(prefix="/auth", tags=["auth"])

# Mount auth endpoints
router.include_router(register.router)
router.include_router(login.router)
router.include_router(refresh.router)
router.include_router(me.router)
