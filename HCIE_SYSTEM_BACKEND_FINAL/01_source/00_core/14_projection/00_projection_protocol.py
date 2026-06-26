"""Protocol contract for `projection`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/projection/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

@runtime_checkable
class ProjectionProtocol(Protocol):
    """Canonical-state -> UX projection (lifecycle, governance, mutation, event, replay, trajectory)."""

    def project(self, canonical_state: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def event_payload(self, canonical_state: Mapping[str, Any]) -> Mapping[str, Any]: ...
