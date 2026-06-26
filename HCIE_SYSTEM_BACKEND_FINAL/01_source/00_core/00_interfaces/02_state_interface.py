"""Cross-module state interface.

The canonical learner state lives behind this protocol. Source of truth is
`HCIE_SYSTEM_BACKENDV2/core/ownership/canonical_schema.py`, which defines
the Tier1/Tier2/Tier3 field hierarchy. Concrete TypedDicts are defined in
`01_source/00_core/02_state/01_learner_state.py` during Phase 2.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class StateInterface(Protocol):
    """Canonical state envelope used across cognition + persistence."""

    def get_field(self, key: str) -> Any:
        ...

    def set_field(self, key: str, value: Any) -> None:
        ...

    def validate(self) -> tuple[bool, list[str]]:
        """Return (ok, errors). Mandatory Tier1 fields enforced here."""
        ...

    def to_dict(self) -> Mapping[str, Any]:
        ...

    def from_dict(self, payload: Mapping[str, Any]) -> "StateInterface":
        ...
