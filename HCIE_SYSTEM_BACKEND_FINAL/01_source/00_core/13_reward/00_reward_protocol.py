"""Protocol contract for `reward`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/reward/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

@runtime_checkable
class RewardProtocol(Protocol):
    """Reward signal for the bandit (CT reward, etc.)."""

    def reward(self, interaction: Mapping[str, Any], outcome: Mapping[str, Any]) -> float: ...
