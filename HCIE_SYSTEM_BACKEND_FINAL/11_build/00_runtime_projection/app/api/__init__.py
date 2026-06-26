"""Legacy `app.api` exports for the numbered FINAL API tree."""

from __future__ import annotations

from pathlib import Path

_FINAL_ROOT = Path(__file__).resolve().parents[4]
__path__ = [
    str(Path(__file__).resolve().parent),
    str(_FINAL_ROOT / "01_source" / "01_application" / "00_api"),
]

__all__ = [
    "learning_router",
    "analytics_router",
    "system_router",
    "admin_router",
    "experiments_router",
    "auth_router",
    "users_router",
]


def __getattr__(name: str):
    if name == "learning_router":
        from .learning import learning_router

        return learning_router
    if name == "analytics_router":
        from .analytics import analytics_router

        return analytics_router
    if name == "system_router":
        from .system import system_router

        return system_router
    if name == "admin_router":
        from .admin import admin_router

        return admin_router
    if name == "experiments_router":
        from .experiments import experiments_router

        return experiments_router
    if name == "auth_router":
        from .auth import auth_router

        return auth_router
    if name == "users_router":
        from .users import users_router

        return users_router
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
