"""
Learning Tasks API - Task selection and submission
"""

from fastapi import APIRouter
from app.api.routes.tasks.tasks import router as tasks_router

router = APIRouter()

# Mount existing tasks router - clean path
router.include_router(tasks_router)
