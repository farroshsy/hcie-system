"""
HCIE messaging — Kafka event streaming for the adaptive learning system.
"""

from .schema.events import (
    BaseEvent,
    EventType,
    TaskGeneratedEvent,
    TaskSubmittedEvent,
    MasteryUpdatedEvent,
    PolicyExecutedEvent,
    RewardCalculatedEvent,
    UserSessionStartedEvent,
    UserSessionEndedEvent,
    SystemHealthCheckEvent,
    UserRegisteredEvent,
    UserLoggedInEvent,
    TokenRefreshedEvent,
    UserProfileUpdatedEvent,
    UserLoggedOutEvent,
    PasswordChangedEvent,
)
from .producer.kafka_producer import HCIEKafkaProducer, get_kafka_producer, close_kafka_producer
from .consumer.kafka_consumer import HCIEKafkaConsumer
from .event_worker import HCIEEventWorker, get_event_worker, start_event_worker, stop_event_worker
from .auth_worker import AuthEventWorker, get_auth_event_worker, start_auth_event_worker, stop_auth_event_worker

__all__ = [
    "BaseEvent",
    "EventType",
    "TaskGeneratedEvent",
    "TaskSubmittedEvent",
    "MasteryUpdatedEvent",
    "PolicyExecutedEvent",
    "RewardCalculatedEvent",
    "UserSessionStartedEvent",
    "UserSessionEndedEvent",
    "SystemHealthCheckEvent",
    "UserRegisteredEvent",
    "UserLoggedInEvent",
    "TokenRefreshedEvent",
    "UserProfileUpdatedEvent",
    "UserLoggedOutEvent",
    "PasswordChangedEvent",
    "HCIEKafkaProducer",
    "get_kafka_producer",
    "close_kafka_producer",
    "HCIEKafkaConsumer",
    "HCIEEventWorker",
    "get_event_worker",
    "start_event_worker",
    "stop_event_worker",
    "AuthEventWorker",
    "get_auth_event_worker",
    "start_auth_event_worker",
    "stop_auth_event_worker",
]
