"""Protocol contract for `policy`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/policy/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

@runtime_checkable
class PolicyProtocol(Protocol):
    """Policy engine: turns governance signals into intervention decisions."""

    def decide(self, governance: Mapping[str, Any], learner_state: Mapping[str, Any]) -> Mapping[str, Any]: ...
