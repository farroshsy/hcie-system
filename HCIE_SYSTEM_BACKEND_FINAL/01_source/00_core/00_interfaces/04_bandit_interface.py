"""Cross-module bandit interface.

Migrated from `core/bandit/bandit.py`,
`core/bandit/transfer_aware_bandit.py`. Thompson + UCB selection that
drives task choice for Contribution B.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable


@runtime_checkable
class BanditInterface(Protocol):
    """Policy that selects the next arm from a context + arm set."""

    def select_arm(self, context: Mapping[str, Any], arms: Sequence[str]) -> tuple[str, Mapping[str, Any]]:
        """Return (arm_id, telemetry). Telemetry must include the score per arm."""
        ...

    def update(self, arm_id: str, reward: float, context: Mapping[str, Any]) -> None:
        ...

    def regret(self) -> float:
        """Cumulative regret since last reset, used by Contribution B."""
        ...
