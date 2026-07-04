"""
Learning API Router - Core adaptive learning system
"""

from fastapi import APIRouter
from .endpoints import state, regret, tasks, decision, frontend, realtime, research

router = APIRouter(prefix="/learning", tags=["learning"])

router.include_router(state.router)
router.include_router(regret.router)
router.include_router(tasks.router)
router.include_router(decision.router)

# Mount frontend-friendly endpoints
router.include_router(frontend.router)

# Mount real-time endpoints
router.include_router(realtime.router)

# Mount research endpoints (algorithm introspection)
router.include_router(research.router)
