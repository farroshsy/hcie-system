"""Bridge: ``app.infrastructure.di.get_container`` → canonical ``container_access``.

Phase 14e correction: the previous bridge routed through the now-deleted
``hcie/`` shim package. After the sitecustomize.py projection was extended to
map ``app.infrastructure.di.*`` directly to ``07_infrastructure/00_di/`` (the
real location of ``container_access.py``), this module just forwards to it.
"""

from __future__ import annotations

from app.infrastructure.di.container_access import (
    get_container as _get,
    set_container as _set,
)


def get_container():
    """Return the Phase 14e composition-root Container singleton."""
    return _get()


def set_container(container):
    """Inject or clear the process-local Container (tests / smoke)."""
    return _set(container)
