"""Protocol contract for `learners`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/learning/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

@runtime_checkable
class LearnerProtocol(Protocol):
    """Single estimator (Bayesian, Kalman, Lyapunov, transfer-aware, etc.)."""

    learner_id: str

    def update(self, observation: Mapping[str, Any], *, rng_key: Any | None = None) -> Mapping[str, Any]: ...
    def predict(self, query: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def snapshot(self) -> Mapping[str, Any]: ...
    def restore(self, snapshot: Mapping[str, Any]) -> None: ...
