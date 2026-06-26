"""
Services layer — business logic and service implementations.

Heavy exports (``TaskService``) are lazy-loaded so Phase 14e ITS routes do not
pull the full brain graph at import time.
"""

from .kafka import KafkaService
from .service_factory import ServiceFactory, get_service_factory

__all__ = [
    "TaskService",
    "ServiceFactory",
    "get_service_factory",
    "KafkaService",
]


def __getattr__(name: str):
    if name == "TaskService":
        from .task import TaskService

        return TaskService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
