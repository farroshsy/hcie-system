"""Cross-module ensemble interface.

Migrated from `core/learning/unified_brain.py`. The ensemble composes
multiple learners and arbitrates between them under the F-016 independence
constraint (post-recalibration: NOT_CONFIRMED collapsed under isolation;
ongoing validation under multi-learner conditions).
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Protocol, runtime_checkable


@runtime_checkable
class EnsembleInterface(Protocol):
    """Composes multiple learners; emits a single arbitrated estimate."""

    def members(self) -> Iterable[Any]:
        ...

    def update_all(self, observation: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
        """Update every member; return per-member deltas keyed by learner_id."""
        ...

    def aggregate(self, query: Mapping[str, Any]) -> Mapping[str, Any]:
        """Aggregate member outputs into a single point + uncertainty + per-member breakdown."""
        ...
