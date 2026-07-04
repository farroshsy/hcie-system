from fastapi import APIRouter

from .autopilot import router as autopilot_router
from .ops import router as ops_router
from .runtime import router as runtime_router

router = APIRouter()
router.include_router(runtime_router)
router.include_router(ops_router)
router.include_router(autopilot_router)

