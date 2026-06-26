"""Cross-module governance interface.

Migrated from `HCIE_SYSTEM_BACKENDV2/core/learning/metrics_governance.py`
and `governance_validator.py`. The JT-decomposed governance signal is the
sole driver of pacing/intervention decisions; this contract isolates its
surface from the implementations.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class GovernanceInterface(Protocol):
    """Governance computes constitutional weights and validates transitions."""

    def evaluate(self, learner_state: Mapping[str, Any], context: Mapping[str, Any]) -> Mapping[str, Any]:
        """Return a JT-decomposed governance signal.

        Required keys in the returned mapping:
            - delta_mastery (float)
            - transfer (float)
            - uncertainty (float)
            - challenge (float)
            - exploration_pressure (float)
        """
        ...

    def validate_transition(self, prev: Mapping[str, Any], curr: Mapping[str, Any]) -> bool:
        """Reject state transitions that violate stability/safety constraints."""
        ...

    def constitutional_weights(self) -> Mapping[str, float]:
        """Current weighting of the governance signal components."""
        ...
