"""Protocol contract for `state`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/ownership/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

@runtime_checkable
class StateProtocol(Protocol):
    """Canonical learner state envelope (Tier1/2/3 schema)."""

    def get_field(self, key: str) -> Any: ...
    def set_field(self, key: str, value: Any) -> None: ...
    def validate(self) -> tuple[bool, list[str]]: ...
    def to_dict(self) -> Mapping[str, Any]: ...
    def merge(self, other: Mapping[str, Any]) -> "StateProtocol": ...
