"""
Admin API Routes
Administrative endpoints for service management and system operations
"""

from .service_management import router as service_management_router
from .dashboard import router as dashboard_router
from .interactions import router as interactions_router
from .metrics import router as metrics_router
from .tiered import router as tiered_router

__all__ = [
    'service_management_router', 
    'dashboard_router',
    'interactions_router',
    'metrics_router',
    'tiered_router'
]
