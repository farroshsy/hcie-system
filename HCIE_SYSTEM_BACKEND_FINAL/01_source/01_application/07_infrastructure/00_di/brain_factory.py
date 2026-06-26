"""UnifiedLearningBrain composition.

Builds a `UnifiedLearningBrain` with every infrastructure/application
collaborator pre-resolved. Core code (`01_source/00_core/03_ensemble/
unified_brain.py`) now accepts these as keyword arguments and no longer
imports concrete Redis/Postgres/optimizer classes itself.
"""

from __future__ import annotations

from typing import Any, Optional

from .personalizer import build_personalizer


def build_unified_brain(
    *,
    redis_store: Any,
    postgres_store: Any,
    environment: str = "production",
    event_bus: Optional[Any] = None,
    outbox: Optional[Any] = None,
    policy_config: Optional[Any] = None,
    experiment_context: bool = False,
    deterministic_config: Optional[Any] = None,
    trajectory_recorder: Optional[Any] = None,
    personalizer: Optional[Any] = None,
) -> Any:
    """Compose the brain. `redis_store` and `postgres_store` are required.

    The `LearningStateRepository` / `LearningTraceRepository` graph is wired
    here so core never imports `app.repositories.*` directly.
    """
    from core.learning.unified_brain import UnifiedLearningBrain

    learning_state_repo: Optional[Any] = None
    trace_repo: Optional[Any] = None
    if environment == "production":
        from app.repositories.learning_state_repository import LearningStateRepository
        from app.repositories.learning_trace_repository import LearningTraceRepository
        learning_state_repo = LearningStateRepository(
            postgres_store=postgres_store,
            redis_store=redis_store,
        )
        trace_repo = LearningTraceRepository(postgres_store)

    if personalizer is None:
        personalizer = build_personalizer()

    return UnifiedLearningBrain(
        event_bus=event_bus,
        outbox=outbox,
        environment=environment,
        policy_config=policy_config,
        experiment_context=experiment_context,
        deterministic_config=deterministic_config,
        trajectory_recorder=trajectory_recorder,
        redis_store=redis_store,
        postgres_store=postgres_store,
        learning_state_repo=learning_state_repo,
        trace_repo=trace_repo,
        personalizer=personalizer,
    )
