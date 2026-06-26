"""V3 admin runtime topology endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.rbac import require_admin

router = APIRouter(prefix="/admin/runtime", tags=["v3-admin-runtime"])


def _manifest_from_container() -> Dict[str, Any] | None:
    try:
        from app.infrastructure.di.get_container import get_container

        brain = get_container().unified_brain()
        manifest = getattr(brain, "capability_manifest", None)
        if manifest is not None and hasattr(manifest, "to_dict"):
            return manifest.to_dict()
    except Exception:
        pass

    try:
        from core.learning.unified_brain import get_latest_capability_manifest

        return get_latest_capability_manifest()
    except Exception:
        return None


@router.get("/capabilities")
async def get_runtime_capabilities(
    _admin: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    """Return the boot-time Cognitive Capability Manifest.

    This is an admin surface because it exposes runtime topology and optional
    engine availability. It is read-only and does not trigger cognition.
    """

    manifest = _manifest_from_container()
    if not manifest:
        raise HTTPException(
            status_code=503,
            detail="Cognitive Capability Manifest has not been emitted for this process",
        )
    return {
        "status": "ok",
        "manifest": manifest,
        "semantic_version": "1.0",
    }

