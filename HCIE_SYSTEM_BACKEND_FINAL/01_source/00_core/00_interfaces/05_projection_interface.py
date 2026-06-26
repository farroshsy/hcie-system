"""Cross-module projection interface.

Migrated from `core/projection/ux_semantics.py` and the
`projection_consumer` worker. Projects canonical cognition state into UX-
ready views and emits `ProjectionUpdated` events.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class ProjectionInterface(Protocol):
    """Pure projection from canonical state -> UX/UI view."""

    def project(self, canonical_state: Mapping[str, Any]) -> Mapping[str, Any]:
        ...

    def event_payload(self, canonical_state: Mapping[str, Any]) -> Mapping[str, Any]:
        """Schema-compliant payload for `ProjectionUpdated` outbox writes."""
        ...
