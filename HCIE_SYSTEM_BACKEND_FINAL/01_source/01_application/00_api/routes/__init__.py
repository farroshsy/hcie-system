"""
API Routes
FastAPI route definitions
"""

from .health.health import router as health_router
from .tasks.tasks import router as tasks_router
from .analytics.analytics import router as analytics_router
from .analytics.dependency_graph import router as dependency_graph_router
from .admin.service_management import router as service_management_router
from .admin.dashboard import router as dashboard_router
from .admin.metrics import router as metrics_router
from .admin.interactions import router as interactions_router
from .admin.tiered import router as tiered_router
from .debug.debug import router as debug_router

__all__ = [
    "health_router",
    "tasks_router",
    "analytics_router",
    "dependency_graph_router",
    "service_management_router",
    "dashboard_router",
    "metrics_router",
    "interactions_router",
    "tiered_router",
    "debug_router"
]
