"""FastAPI dependencies for Phase 14e ``/v3/its/*`` routes."""

from __future__ import annotations

from typing import Any


def get_container_dep() -> Any:
    from app.infrastructure.di.get_container import get_container

    return get_container()


def get_its_runtime_service() -> Any:
    return get_container_dep().its_runtime_service()
