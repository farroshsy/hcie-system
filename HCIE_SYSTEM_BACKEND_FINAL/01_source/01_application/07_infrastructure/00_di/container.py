"""Tiny lazy singleton container for the composition root.

Intentionally small: dependency graphs are explicit in the per-collaborator
factories. The container exists so wiring code can opt into singleton
semantics for the heavy stores (Redis pool, Postgres pool) without smuggling
globals into core.

Usage::

    container = Container()
    redis_store = container.get("redis_store", build_redis_store)
    pg_store = container.get("pg_store", build_postgres_store)

    # Phase 5 -- typed accessor for the config provider:
    config = container.config_provider()

`build_X` callables are passed in by the per-collaborator factories so the
container holds no infrastructure imports of its own.
"""

from __future__ import annotations

from threading import RLock
from typing import Any, Callable, Dict


CONFIG_KEY = "config_provider"


class Container:
    """Process-local lazy singleton container.

    Thread-safe via a coarse RLock. Designed for ~tens of bindings, not a
    full IoC framework.
    """

    def __init__(self) -> None:
        self._bindings: Dict[str, Any] = {}
        self._lock = RLock()

    def get(self, key: str, build: Callable[[], Any]) -> Any:
        with self._lock:
            if key not in self._bindings:
                self._bindings[key] = build()
            return self._bindings[key]

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._bindings[key] = value

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._bindings

    def clear(self) -> None:
        with self._lock:
            self._bindings.clear()

    def config_provider(self) -> Any:
        """Return a memoized `ConfigProviderProtocol` instance.

        Lazily imports `build_config_provider` to avoid pulling the
        config_factory module at Container import time. This keeps the
        Container usable in unit tests where the factory's optional
        BACKENDV2 fallback is undesirable.
        """
        def _build() -> Any:
            from .config_factory import build_config_provider
            return build_config_provider()
        return self.get(CONFIG_KEY, _build)

    def logger(self, name: str = "hcie") -> Any:
        """Return a memoized `LoggerProtocol` instance.

        The memoization key includes the logger name so multiple
        sub-loggers can coexist in the same container.
        """
        def _build() -> Any:
            from .telemetry_factory import build_logger
            return build_logger(name)
        return self.get(f"logger:{name}", _build)

    def metrics_recorder(self) -> Any:
        """Return a memoized `MetricsRecorderProtocol` instance."""
        def _build() -> Any:
            from .telemetry_factory import build_metrics_recorder
            return build_metrics_recorder()
        return self.get("metrics_recorder", _build)

    def tracer(self) -> Any:
        """Return a memoized `TracerProtocol` instance."""
        def _build() -> Any:
            from .telemetry_factory import build_tracer
            return build_tracer()
        return self.get("tracer", _build)

    def secrets_provider(self) -> Any:
        """Return a memoized `SecretsProviderProtocol` instance."""
        def _build() -> Any:
            from .security_factory import build_secrets_provider
            return build_secrets_provider()
        return self.get("secrets_provider", _build)

    def authorizer(self) -> Any:
        """Return a memoized `AuthorizationProtocol` instance."""
        def _build() -> Any:
            from .security_factory import build_authorizer
            return build_authorizer()
        return self.get("authorizer", _build)

    def audit_sink(self) -> Any:
        """Return a memoized `AuditSinkProtocol` instance."""
        def _build() -> Any:
            from .security_factory import build_audit_sink
            return build_audit_sink()
        return self.get("audit_sink", _build)

    def redis_store(self) -> Any:
        def _build() -> Any:
            from .storage_factory import build_redis_store
            return build_redis_store()
        return self.get("redis_store", _build)

    def postgres_store(self) -> Any:
        def _build() -> Any:
            from .storage_factory import build_postgres_store
            return build_postgres_store()
        return self.get("postgres_store", _build)

    def event_bus(self) -> Any:
        def _build() -> Any:
            try:
                from app.infrastructure.kafka.kafka_factory import (
                    KafkaFactory,
                    DefaultKafkaProducerFactory,
                )
                from app.infrastructure.messaging.event_bus import KafkaEventBus
                from config.env import settings

                factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
                producer = factory.create_producer()
                return KafkaEventBus(producer)
            except Exception:
                return None
        return self.get("event_bus", _build)

    def outbox(self) -> Any:
        def _build() -> Any:
            from .outbox_factory import build_outbox
            return build_outbox(self.postgres_store(), self.event_bus())
        return self.get("outbox", _build)

    def personalizer(self) -> Any:
        def _build() -> Any:
            from .personalizer import build_personalizer
            return build_personalizer()
        return self.get("personalizer", _build)

    def rng_stream_manager(self, seed: int = 42) -> Any:
        def _build() -> Any:
            from core.determinism.rng_stream_manager import RNGStreamManager
            return RNGStreamManager(seed=seed)
        return self.get(f"rng_stream_manager:{seed}", _build)

    def unified_brain(self, *, environment: str = "production") -> Any:
        def _build() -> Any:
            from .brain_factory import build_unified_brain
            from config.env import settings
            
            # 🔥 P2 FIX: Initialize trajectory recorder for research validation
            trajectory_recorder = None
            if getattr(settings, 'enable_trajectory_recording', True):
                try:
                    from infrastructure.experiment.trajectory_recorder import TrajectoryRecorder
                    trajectory_recorder = TrajectoryRecorder(self.postgres_store())
                except Exception as e:
                    # Log but don't fail - trajectory recording is optional for operation
                    import logging
                    logging.getLogger(__name__).warning(f"Failed to initialize trajectory recorder: {e}")
            
            return build_unified_brain(
                redis_store=self.redis_store(),
                postgres_store=self.postgres_store(),
                event_bus=self.event_bus(),
                outbox=self.outbox(),
                environment=environment,
                personalizer=self.personalizer(),
                trajectory_recorder=trajectory_recorder,
            )
        return self.get(f"unified_brain:{environment}", _build)

    def bandit(self) -> Any:
        def _build() -> Any:
            try:
                from core.bandit.bandit import ContextualBandit
            except Exception:
                from core.bandit.contextual_bandit import ContextualBandit  # type: ignore
            try:
                return ContextualBandit(
                    uncertainty_weight=0.1,
                    learning_gain_weight=0.05,
                    representations=["text", "code", "multiple_choice", "video", "interactive"],
                )
            except TypeError:
                return ContextualBandit()

        return self.get("bandit", _build)

    def brain_runtime_service(self) -> Any:
        def _build() -> Any:
            from .brain_runtime_factory import build_brain_runtime_service
            return build_brain_runtime_service(
                unified_brain=self.unified_brain(),
                postgres_store=self.postgres_store(),
                outbox=self.outbox(),
                redis_store=self.redis_store(),
            )
        return self.get("brain_runtime_service", _build)

    def recommendation_projection(self) -> Any:
        def _build() -> Any:
            from app.services.projection.recommendation_projection import (
                RecommendationProjection,
            )
            return RecommendationProjection(
                unified_brain=self.unified_brain(),
                postgres_store=self.postgres_store(),
                cache_store=self.redis_store(),
            )
        return self.get("recommendation_projection", _build)

    def its_runtime_service(self) -> Any:
        def _build() -> Any:
            from .its_runtime_factory import build_its_runtime_service
            return build_its_runtime_service(
                spine=self.brain_runtime_service(),
                projection=self.recommendation_projection(),
                personalizer=self.personalizer(),
                rng=self.rng_stream_manager(),
                logger=self.logger("hcie.its"),
                metrics=self.metrics_recorder(),
                tracer=self.tracer(),
                postgres_store=self.postgres_store(),
                bandit=self.bandit(),
                outbox=self.outbox(),
            )
        return self.get("its_runtime_service", _build)
