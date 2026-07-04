"""Protocol contract for `adaptation`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/adaptation/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

@runtime_checkable
class AdaptationProtocol(Protocol):
    """Deterministic adaptation engine + policy isolation/registry."""

    def adapt(self, learner_state: Mapping[str, Any], governance: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def policy_id(self) -> str: ...
