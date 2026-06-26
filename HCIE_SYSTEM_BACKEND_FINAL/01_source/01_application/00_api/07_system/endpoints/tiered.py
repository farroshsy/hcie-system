"""
Tiered System API - Tiered reconstruction monitoring and control
"""

from fastapi import APIRouter
from app.api.routes.admin.tiered import router as tiered_router

router = APIRouter()

# Mount existing tiered router - clean path
router.include_router(tiered_router)
