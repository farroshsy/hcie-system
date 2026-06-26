"""Cross-module learning interface.

The contract every learner-style component implements before being composed
into the ensemble or governance layer. Migrated from
`HCIE_SYSTEM_BACKENDV2/core/learning/base_learner.py`.

NOTE: This is the public re-export surface. The intra-module protocol lives
in `01_source/00_core/04_learners/00_learner_protocol.py`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class LearningInterface(Protocol):
    """Public learning contract used by application + infrastructure layers."""

    learner_id: str

    def update(self, observation: Mapping[str, Any], *, rng_key: Any | None = None) -> Mapping[str, Any]:
        """Apply one observation, return the resulting state delta."""
        ...

    def predict(self, query: Mapping[str, Any]) -> Mapping[str, Any]:
        """Return point + uncertainty estimate for a query."""
        ...

    def snapshot(self) -> Mapping[str, Any]:
        """Deterministic, JSON-serializable state snapshot."""
        ...

    def restore(self, snapshot: Mapping[str, Any]) -> None:
        """Rehydrate from a snapshot. Pure: must yield byte-identical updates."""
        ...
