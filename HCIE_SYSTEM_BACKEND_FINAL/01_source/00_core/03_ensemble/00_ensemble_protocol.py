"""Protocol contract for `ensemble`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/learning/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

@runtime_checkable
class EnsembleProtocol(Protocol):
    """Composes learners; arbitrates between them under independence constraint."""

    def members(self) -> Sequence[Any]: ...
    def update_all(self, observation: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]: ...
    def aggregate(self, query: Mapping[str, Any]) -> Mapping[str, Any]: ...
