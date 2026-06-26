"""Protocol contract for `determinism`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/determinism/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

@runtime_checkable
class DeterminismProtocol(Protocol):
    """RNG stream manager + entropy instrumentation."""

    def child_rng(self, name: str) -> Any: ...
    def record_entropy(self, name: str, value: float) -> None: ...
    def replay(self, log: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]: ...
