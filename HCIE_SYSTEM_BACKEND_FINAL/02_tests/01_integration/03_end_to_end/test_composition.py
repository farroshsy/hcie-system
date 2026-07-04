from app.runtime.composition import RuntimeRole, build_runtime_service
from app.runtime.unified_brain_runtime_service import UnifiedBrainRuntimeService


class SettingsStub:
    enable_deterministic_mode = True
    deterministic_seed = 42
    deterministic_uuids = True
    deterministic_time = True
    trajectory_determinism = True
    enable_trajectory_recording = False


def test_build_runtime_service_returns_unified_brain_runtime_service():
    service = build_runtime_service(RuntimeRole.API, SettingsStub())
    assert isinstance(service, UnifiedBrainRuntimeService)
    assert service.role == RuntimeRole.API


def test_build_runtime_service_uses_same_factory_for_worker_roles():
    api_service = build_runtime_service(RuntimeRole.API, SettingsStub())
    worker_service = build_runtime_service(RuntimeRole.LEARNING_CONSUMER, SettingsStub())
    assert type(api_service) is type(worker_service)
    assert worker_service.role == RuntimeRole.LEARNING_CONSUMER
