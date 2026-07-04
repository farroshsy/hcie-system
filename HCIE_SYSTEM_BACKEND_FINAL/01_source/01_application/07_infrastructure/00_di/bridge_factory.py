"""BrainBridgeService composition.

The bridge is now an application service (see PHASE_3_PROGRESS). It is
constructed here against an injected Postgres store + optional event bus +
optional deterministic config. The bridge itself constructs its own
`OutboxPattern` via `outbox_factory.build_outbox`.
"""

from __future__ import annotations

from typing import Any, Optional


def build_brain_bridge(
    *,
    db_store: Any,
    event_bus: Optional[Any] = None,
    deterministic_config: Optional[Any] = None,
) -> Any:
    """Build a `BrainBridgeService` ready for runtime orchestration."""
    # Module name does not collide with the legacy core path because the
    # canonical home is now `01_application/01_services/02_session/...`.
    # During this migration window the live import path that ships with the
    # production stack is still `core.session.brain_bridge_service` (the
    # FINAL tree is copy-only). The composition root therefore prefers the
    # application-layer module if it has been packaged, and falls back to
    # the legacy path while the FINAL tree is not yet on sys.path.
    try:
        from application.services.session.brain_bridge_service import BrainBridgeService  # type: ignore[import-not-found]
    except ImportError:
        from core.session.brain_bridge_service import BrainBridgeService

    return BrainBridgeService(
        db_store=db_store,
        event_bus=event_bus,
        deterministic_config=deterministic_config,
    )
