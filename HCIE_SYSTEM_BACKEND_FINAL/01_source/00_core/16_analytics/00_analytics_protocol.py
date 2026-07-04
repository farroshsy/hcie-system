"""Protocol contract for `analytics`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/analytics/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

@runtime_checkable
class AnalyticsProtocol(Protocol):
    """Adaptation effectiveness, intervention outcomes, misconception tracking, pacing stability."""

    def emit(self, event: str, payload: Mapping[str, Any]) -> None: ...
    def query(self, view: str, params: Mapping[str, Any]) -> Mapping[str, Any]: ...
