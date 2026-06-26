"""Dependency inversion ports for Phase 3 layer cleanup.

These protocols describe the *core-facing* shape of infrastructure and
application services that currently leak into `01_source/00_core/`. They
are intentionally narrow per the Interface Segregation Principle so each
core component depends on the smallest contract sufficient for its job.

Storage-specific ports live in `07_storage_ports.py`.

Concrete implementations belong outside core, usually in:

- `01_source/01_application/07_infrastructure/00_di/`
- `01_source/02_infrastructure/01_storage/`
- `01_source/03_experiments/`

Core code should depend on these protocols, not on Redis/Postgres/outbox or
experiment modules directly.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable


@runtime_checkable
class ClockProtocol(Protocol):
    """Deterministic clock port for code that must avoid direct wall-clock access."""

    def now(self) -> float:
        ...

    def iso_now(self) -> str:
        ...


@runtime_checkable
class PersonalizedMasteryProtocol(Protocol):
    """Personalized cold-start mastery port used by learner configuration.

    Aligned with the static method
    `ColdStartOptimizer.get_personalized_mastery(user_id, concept)` in
    `app/services/user_profiling/cold_start_optimizer.py`. Injecting via this
    protocol removes the app-layer reach-in from
    `01_source/00_core/04_learners/prior_config.py`.

    `ColdStartOptimizer.get_personalized_mastery` is declared as a static
    method; the protocol contract here is intentionally instance-shaped so
    the application-layer adapter can decide whether to wrap the static
    function or expose a stateful service.
    """

    def get_personalized_mastery(
        self,
        user_id: str,
        concept: str,
        user_profile: Any | None = None,
    ) -> float:
        ...


@runtime_checkable
class TransferWeightTunerProtocol(Protocol):
    """Transfer-weight tuner port matching the multi-step pipeline used by
    `01_source/00_core/05_engines/transfer_aware_engine.py`.

    Aligned with `TransferWeightTuner.{extract_learning_events,
    detect_transfer_opportunities, calculate_transfer_effects}` in
    `experiments/transfer_weight_tuner.py`. Keeps the existing call shape
    while letting application-layer wiring decide how the tuner is built.
    """

    def extract_learning_events(self, interactions_df: Any) -> Sequence[Mapping[str, Any]]:
        ...

    def detect_transfer_opportunities(
        self,
        events: Sequence[Mapping[str, Any]],
    ) -> Sequence[Mapping[str, Any]]:
        ...

    def calculate_transfer_effects(
        self,
        opportunities: Sequence[Mapping[str, Any]],
    ) -> Mapping[str, Mapping[str, Sequence[float]]]:
        ...


@runtime_checkable
class OutboxPortProtocol(Protocol):
    """Outbox writer port for bridge/orchestration code.

    Aligned with `OutboxPattern.{create_event, save_event}` in
    `app/infrastructure/outbox/outbox_pattern.py`. The current core consumer
    is `brain_bridge_service.py`, which is flagged in PHASE_3_PLAN.md for
    reclassification into the application layer; this protocol exists so any
    other core-side code (e.g. session orchestration) can depend on the port
    instead of importing the concrete implementation.

    `event` and the return of `create_event` are typed as `Any` because the
    canonical `OutboxEvent` dataclass lives in the application layer; core
    should treat it as an opaque handle until/unless we publish an
    OutboxEvent contract from core itself.
    """

    def create_event(
        self,
        event_id: str,
        event_type: str,
        payload: Mapping[str, Any],
        topic: str,
        deterministic_mode: Any | None = None,
        deterministic_seed: Any | None = None,
    ) -> Any:
        ...

    def save_event(self, event: Any, transaction: Any | None = None) -> str:
        ...
