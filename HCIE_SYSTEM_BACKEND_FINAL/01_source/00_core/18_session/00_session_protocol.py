"""Protocol contract for `session`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/session/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

@runtime_checkable
class SessionProtocol(Protocol):
    """Per-learner session lifecycle (start, step, end, snapshot, restore)."""

    def start(self, learner_id: str, *, seed: int | None = None) -> Mapping[str, Any]: ...
    def step(self, learner_id: str, interaction: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def end(self, learner_id: str) -> Mapping[str, Any]: ...
