"""Protocol contract for `transfer`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/learning/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

@runtime_checkable
class TransferProtocol(Protocol):
    """Cross-concept transfer learning + DAG dependencies."""

    def transfer(self, source: str, target: str, observation: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def dag_edges(self) -> Sequence[tuple[str, str, float]]: ...
