"""UnifiedBrainRuntimeService composition for the Phase 14 ITS spine."""

from __future__ import annotations

from typing import Any, Optional


def build_brain_runtime_service(
    *,
    unified_brain: Any,
    postgres_store: Any,
    outbox: Optional[Any] = None,
    redis_store: Optional[Any] = None,
    settings: Optional[Any] = None,
) -> Any:
    """Compose API-scoped UnifiedBrainRuntimeService with idempotency + ownership."""
    from app.runtime.unified_brain_runtime_service import UnifiedBrainRuntimeService
    from app.runtime.composition import RuntimeRole  # 01_application/09_runtime

    if settings is None:
        try:
            from config.env import settings as app_settings
            settings = app_settings
        except Exception:
            settings = _SettingsStub()

    idempotency_manager = None
    if redis_store is not None:
        try:
            from core.validation.idempotency_manager import IdempotencyManager  # 09_validation
            from .idempotency_adapter import build_idempotency_key_store

            idempotency_manager = IdempotencyManager(
                key_store=build_idempotency_key_store(redis_store)
            )
        except Exception:
            idempotency_manager = None

    ownership = None
    try:
        from core.ownership.ownership_enforcement import OwnershipEnforcement

        ownership = OwnershipEnforcement()
    except Exception:
        ownership = None

    transaction_factory = None
    if postgres_store is not None:
        try:
            from app.infrastructure.unit_of_work import get_transaction

            transaction_factory = lambda: get_transaction(postgres_store)
        except Exception:
            transaction_factory = None

    return UnifiedBrainRuntimeService(
        role=RuntimeRole.API,
        settings=settings,
        unified_brain=unified_brain,
        postgres_store=postgres_store,
        outbox=outbox,
        idempotency_manager=idempotency_manager,
        ownership=ownership,
        transaction_factory=transaction_factory,
    )


class _SettingsStub:
    app_name = "HCIE FINAL"
    app_version = "14e"
    debug = True
