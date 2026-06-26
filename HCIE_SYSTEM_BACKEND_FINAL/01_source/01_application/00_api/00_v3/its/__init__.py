"""Deprecated `/v3/its/*` redirects.

Slice 1 makes `/v3/learner/*` the canonical learner-facing namespace. These
routes remain as a migration alias only and return permanent redirects.
"""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/its", tags=["v3-its-deprecated"], deprecated=True)


def _redirect(request: Request, target: str) -> RedirectResponse:
    url = request.url.replace(path=f"/v3/learner{target}")
    return RedirectResponse(str(url), status_code=301)


@router.post("/recommend", include_in_schema=True)
async def recommend_redirect(request: Request):
    return _redirect(request, "/recommend")


@router.post("/attempt", include_in_schema=True)
async def attempt_redirect(request: Request):
    return _redirect(request, "/attempt")


@router.get("/progress", include_in_schema=True)
async def progress_redirect(request: Request):
    return _redirect(request, "/progress")


@router.get("/session", include_in_schema=True)
async def session_redirect(request: Request):
    return _redirect(request, "/session")
