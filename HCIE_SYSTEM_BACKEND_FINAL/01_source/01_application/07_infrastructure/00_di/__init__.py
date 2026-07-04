"""Composition root for HCIE_SYSTEM_BACKEND_FINAL.

This package wires concrete implementations from the live infrastructure
(`storage/*`, `app/*`, `experiments/*`) into the core protocols defined under
`01_source/00_core/00_interfaces/`. Core remains import-clean
(`tools/migrate/check_layers.py --strict`) because every concrete dependency
is constructed here and passed in via constructor arguments.

The factories follow Interface Segregation: each one builds the smallest
collaborator graph required for a slice of the system. They are intentionally
side-effect free (no global state) and idempotent (calling twice returns two
independent graphs unless a `Container` is reused).

Module roles:

- `container.py`            small lazy singleton container
- `storage_factory.py`      Redis + Postgres concrete stores
- `outbox_factory.py`       OutboxPattern bound to a Postgres store
- `personalizer.py`         adapter for the static ColdStartOptimizer
- `tuner_factory.py`        TransferWeightTuner adapter
- `brain_factory.py`        UnifiedLearningBrain with injected deps
- `bridge_factory.py`       application-layer BrainBridgeService
- `runtime_factory.py`      RuntimeCoordinator wired to the bridge
- `config_factory.py`       ConfigProviderProtocol adapters + builder
- `telemetry_factory.py`    LoggerProtocol / MetricsRecorderProtocol /
                             TracerProtocol adapters + builders
"""

from .container import Container
from .container_access import get_container, set_container
from .storage_factory import build_redis_store, build_postgres_store
from .outbox_factory import build_outbox
from .personalizer import StaticColdStartPersonalizer, build_personalizer
from .tuner_factory import build_transfer_weight_tuner
from .brain_factory import build_unified_brain
from .bridge_factory import build_brain_bridge
from .runtime_factory import build_runtime_coordinator
from .config_factory import (
    PydanticSettingsConfigProvider,
    EnvOverlayConfigProvider,
    build_config_provider,
)
from .telemetry_factory import (
    StdLoggingLogger,
    NoopMetricsRecorder,
    NoopSpan,
    NoopTracer,
    build_logger,
    build_metrics_recorder,
    build_tracer,
)
from .security_factory import (
    EnvSecretsProvider,
    InMemorySecretsProvider,
    AllowAllAuthorizer,
    RoleAllowlistAuthorizer,
    LoggingAuditSink,
    NullAuditSink,
    build_secrets_provider,
    build_authorizer,
    build_audit_sink,
)

__all__ = [
    "Container",
    "get_container",
    "set_container",
    "build_redis_store",
    "build_postgres_store",
    "build_outbox",
    "StaticColdStartPersonalizer",
    "build_personalizer",
    "build_transfer_weight_tuner",
    "build_unified_brain",
    "build_brain_bridge",
    "build_runtime_coordinator",
    "PydanticSettingsConfigProvider",
    "EnvOverlayConfigProvider",
    "build_config_provider",
    "StdLoggingLogger",
    "NoopMetricsRecorder",
    "NoopSpan",
    "NoopTracer",
    "build_logger",
    "build_metrics_recorder",
    "build_tracer",
    "EnvSecretsProvider",
    "InMemorySecretsProvider",
    "AllowAllAuthorizer",
    "RoleAllowlistAuthorizer",
    "LoggingAuditSink",
    "NullAuditSink",
    "build_secrets_provider",
    "build_authorizer",
    "build_audit_sink",
]
