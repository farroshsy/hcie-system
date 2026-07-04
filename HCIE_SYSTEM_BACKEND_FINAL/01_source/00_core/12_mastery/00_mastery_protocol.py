"""Protocol contract for `mastery`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/mastery/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

@runtime_checkable
class MasteryProtocol(Protocol):
    """Mastery point estimate + uncertainty + history."""

    def compute(self, learner_state: Mapping[str, Any]) -> Mapping[str, float]: ...
    def threshold_reached(self, learner_state: Mapping[str, Any], concept_id: str) -> bool: ...
