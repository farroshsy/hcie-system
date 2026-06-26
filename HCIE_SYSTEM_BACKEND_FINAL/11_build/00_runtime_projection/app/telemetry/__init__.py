"""Legacy telemetry exports for the FINAL runtime projection."""

from __future__ import annotations

from pathlib import Path

_FINAL_ROOT = Path(__file__).resolve().parents[4]
__path__ = [
    str(Path(__file__).resolve().parent),
    str(_FINAL_ROOT / "01_source" / "01_application" / "08_telemetry"),
]

from .opentelemetry_setup import get_meter, get_tracer, setup_opentelemetry


def _metric(name: str):
    from . import opentelemetry_setup

    return getattr(opentelemetry_setup, name, None)


def get_request_counter():
    return _metric("request_counter")


def get_request_duration():
    return _metric("request_duration")


def get_kafka_events_counter():
    return _metric("kafka_events_counter")


def get_postgres_operations_counter():
    return _metric("postgres_operations_counter")


def get_redis_operations_counter():
    return _metric("redis_operations_counter")


def get_submission_counter():
    return _metric("submission_counter")


def get_transfer_events_counter():
    return _metric("transfer_events_counter")


def get_mastery_updates_counter():
    return _metric("mastery_updates_counter")


def get_interaction_counter():
    return _metric("interaction_counter")


def get_interaction_reward_sum():
    return _metric("interaction_reward_sum")


def get_interaction_reward_histogram():
    return _metric("interaction_reward_histogram")


def get_latency_histogram():
    return _metric("latency_histogram")


tracer = get_tracer
meter = get_meter
request_counter = get_request_counter
request_duration = get_request_duration
kafka_events_counter = get_kafka_events_counter
postgres_operations_counter = get_postgres_operations_counter
redis_operations_counter = get_redis_operations_counter
submission_counter = get_submission_counter
transfer_events_counter = get_transfer_events_counter
mastery_updates_counter = get_mastery_updates_counter
interaction_counter = get_interaction_counter
interaction_reward_sum = get_interaction_reward_sum
interaction_reward_histogram = get_interaction_reward_histogram
latency_histogram = get_latency_histogram
