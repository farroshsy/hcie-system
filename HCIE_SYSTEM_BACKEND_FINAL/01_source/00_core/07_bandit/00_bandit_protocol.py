"""Protocol contract for `bandit`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/bandit/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

@runtime_checkable
class BanditProtocol(Protocol):
    """Thompson/UCB selection over the task arm space."""

    def select_arm(self, context: Mapping[str, Any], arms: Sequence[str]) -> tuple[str, Mapping[str, Any]]: ...
    def update(self, arm_id: str, reward: float, context: Mapping[str, Any]) -> None: ...
    def regret(self) -> float: ...
