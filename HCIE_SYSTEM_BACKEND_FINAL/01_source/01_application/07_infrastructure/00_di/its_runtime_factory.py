"""ItsRuntimeService composition for Phase 14e production ITS spine."""

from __future__ import annotations

from typing import Any, Optional


def build_its_runtime_service(
    *,
    spine: Any,
    projection: Any,
    personalizer: Any,
    rng: Any,
    logger: Any,
    metrics: Any,
    tracer: Any,
    postgres_store: Any,
    bandit: Optional[Any] = None,
    outbox: Optional[Any] = None,
) -> Any:
    from app.runtime.its_runtime_service import ItsRuntimeService

    return ItsRuntimeService(
        spine=spine,
        projection=projection,
        personalizer=personalizer,
        rng=rng,
        logger=logger,
        metrics=metrics,
        tracer=tracer,
        postgres_store=postgres_store,
        bandit=bandit,
        outbox=outbox,
    )
