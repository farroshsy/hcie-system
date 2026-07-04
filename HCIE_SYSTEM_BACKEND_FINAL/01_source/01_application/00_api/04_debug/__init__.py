"""
Debug API package - System debugging and mathematical showcase endpoints
"""

from ..debug_routes import router as debug_router
from .math_showcase import router as math_showcase_router

# Combine debug routers
debug_router.include_router(math_showcase_router, tags=["mathematical-showcase"])

__all__ = ['debug_router']
