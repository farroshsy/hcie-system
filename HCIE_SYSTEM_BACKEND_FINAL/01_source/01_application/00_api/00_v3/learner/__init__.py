"""Canonical V3 learner API surface.

Slice 1 renames the production ITS spine from `/v3/its/*` to
`/v3/learner/*`. The underlying runtime service stays the same; only the
external persona-facing namespace changes.
"""

from fastapi import APIRouter

from app.api.v3.its.attempt import router as attempt_router
from app.api.v3.its.progress import router as progress_router
from app.api.v3.its.recommend import router as recommend_router
from app.api.v3.learner.material import router as material_router
from app.api.v3.learner.archetype_profile import router as archetype_profile_router

router = APIRouter(prefix="/learner", tags=["v3-learner-production"])

router.include_router(recommend_router)
router.include_router(attempt_router)
router.include_router(progress_router)
router.include_router(material_router)
router.include_router(archetype_profile_router)

