from app.runtime.composition import RuntimeRole, build_worker_runtime
from app.workers.learning_consumer import LearningConsumerService


class SettingsStub:
    pass


def test_build_worker_runtime_returns_correct_role():
    runtime = build_worker_runtime(RuntimeRole.LEARNING_CONSUMER, SettingsStub())
    assert runtime.role == RuntimeRole.LEARNING_CONSUMER
    assert runtime.unified_brain_runtime.role == RuntimeRole.LEARNING_CONSUMER


def test_learning_consumer_get_runtime_service_uses_composition_root():
    service = LearningConsumerService()
    runtime = service.get_runtime_service()
    assert runtime.role == RuntimeRole.LEARNING_CONSUMER
    assert runtime.unified_brain_runtime.role == RuntimeRole.LEARNING_CONSUMER
