"""RuntimeCoordinator composition.

`RuntimeCoordinator` now requires an injected `brain_bridge_service`. The
composition root builds the bridge first (via `bridge_factory.build_brain_bridge`)
and threads every other session collaborator through the same constructor.
"""

from __future__ import annotations

from typing import Any, Optional

from .bridge_factory import build_brain_bridge


def build_runtime_coordinator(
    *,
    session_service: Any,
    task_selection_service: Any,
    attempt_evaluation_service: Any,
    adaptation_service: Any,
    projection_service: Any,
    db_store: Any,
    event_bus: Optional[Any] = None,
    deterministic_config: Optional[Any] = None,
    brain_bridge_service: Optional[Any] = None,
    learner_progress_repository: Optional[Any] = None,
    task_attempt_repository: Optional[Any] = None,
    adaptation_event_repository: Optional[Any] = None,
    learning_session_repository: Optional[Any] = None,
    concept_registry: Optional[Any] = None,
) -> Any:
    """Build a fully-wired `RuntimeCoordinator`.

    `db_store` is required because the bridge can only emit outbox events
    inside a transaction-capable store. If the caller has already built a
    bridge it can pass `brain_bridge_service`; otherwise one is composed
    here.
    """
    from core.session.runtime_coordinator import RuntimeCoordinator

    if brain_bridge_service is None:
        brain_bridge_service = build_brain_bridge(
            db_store=db_store,
            event_bus=event_bus,
            deterministic_config=deterministic_config,
        )

    return RuntimeCoordinator(
        session_service=session_service,
        task_selection_service=task_selection_service,
        attempt_evaluation_service=attempt_evaluation_service,
        adaptation_service=adaptation_service,
        projection_service=projection_service,
        learner_progress_repository=learner_progress_repository,
        task_attempt_repository=task_attempt_repository,
        adaptation_event_repository=adaptation_event_repository,
        learning_session_repository=learning_session_repository,
        brain_bridge_service=brain_bridge_service,
        concept_registry=concept_registry,
        db_store=db_store,
        event_bus=event_bus,
    )
