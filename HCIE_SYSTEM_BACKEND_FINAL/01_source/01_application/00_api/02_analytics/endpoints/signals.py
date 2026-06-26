"""
Analytics Signals API - User learning signals and analytics
"""

from fastapi import APIRouter
from app.api.routes.analytics.analytics import router as analytics_router

router = APIRouter()

# Mount existing analytics router - clean path
router.include_router(analytics_router)

# Export the router for proper module import
__all__ = ['router']
