from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.runtime.unified_brain_runtime_service import UnifiedBrainRuntimeService


class RuntimeRole(str, Enum):
    API = "api"
    LEARNING_CONSUMER = "learning-consumer"
    PROJECTION_CONSUMER = "projection-consumer"
    ADAPTATION_CONSUMER = "adaptation-consumer"
    TRAJECTORY_RECORDER = "trajectory-recorder"
    EXPERIMENT_WORKER = "experiment-worker"


@dataclass
class ApiRuntime:
    unified_brain_runtime: UnifiedBrainRuntimeService


@dataclass
class WorkerRuntime:
    role: RuntimeRole
    unified_brain_runtime: UnifiedBrainRuntimeService


def build_runtime_service(role: RuntimeRole, settings: Any) -> UnifiedBrainRuntimeService:
    return UnifiedBrainRuntimeService(role=role, settings=settings)


def build_api_runtime(settings: Any) -> ApiRuntime:
    return ApiRuntime(unified_brain_runtime=build_runtime_service(RuntimeRole.API, settings))


def build_worker_runtime(role: RuntimeRole, settings: Any) -> WorkerRuntime:
    return WorkerRuntime(role=role, unified_brain_runtime=build_runtime_service(role, settings))
