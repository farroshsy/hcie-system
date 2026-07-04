"""Unit tests for the Phase 6 telemetry ports.

Verifies that:

1. The four protocols (LoggerProtocol / MetricsRecorderProtocol /
   TracerProtocol / SpanProtocol) are `runtime_checkable`.
2. The default no-op / stdlib adapters in `telemetry_factory.py`
   satisfy the protocols at runtime.
3. The `Container` exposes telemetry accessors as memoized singletons.
"""

from __future__ import annotations

import logging

import pytest

from finals_loader import from_finals


def test_protocols_are_runtime_checkable() -> None:
    ports = from_finals("01_source/00_core/00_interfaces/10_telemetry_ports.py")
    factory = from_finals("01_source/01_application/07_infrastructure/00_di/telemetry_factory.py")

    logger = factory.build_logger("test")
    metrics = factory.build_metrics_recorder()
    tracer = factory.build_tracer()

    assert isinstance(logger, ports.LoggerProtocol)
    assert isinstance(metrics, ports.MetricsRecorderProtocol)
    assert isinstance(tracer, ports.TracerProtocol)

    span = tracer.start_span("unit-test")
    assert isinstance(span, ports.SpanProtocol)


def test_std_logging_logger_writes_to_logger() -> None:
    factory = from_finals("01_source/01_application/07_infrastructure/00_di/telemetry_factory.py")
    bag = []

    class _Capture(logging.Handler):
        def emit(self, record):
            bag.append((record.levelno, record.getMessage()))

    handler = _Capture(level=logging.DEBUG)
    log = factory.build_logger("hcie.test.telemetry")
    log._logger.addHandler(handler)
    log._logger.setLevel(logging.DEBUG)
    try:
        log.info("hello", user="u1", value=3)
        log.warning("careful", code=42)
    finally:
        log._logger.removeHandler(handler)

    assert any("hello" in msg and "user=u1" in msg for _lvl, msg in bag)
    assert any("careful" in msg and "code=42" in msg for _lvl, msg in bag)


def test_noop_metrics_recorder_captures_events() -> None:
    factory = from_finals("01_source/01_application/07_infrastructure/00_di/telemetry_factory.py")
    recorder = factory.build_metrics_recorder()

    recorder.incr("requests", endpoint="/x")
    recorder.observe("latency", 0.5, endpoint="/x")
    recorder.gauge("queue_depth", 7.0)

    kinds = [e[0] for e in recorder.events]
    assert kinds == ["incr", "observe", "gauge"]
    assert recorder.events[1][1] == "latency"
    assert recorder.events[1][2] == 0.5


def test_noop_tracer_records_spans_with_context_manager() -> None:
    factory = from_finals("01_source/01_application/07_infrastructure/00_di/telemetry_factory.py")
    tracer = factory.build_tracer()

    with tracer.start_span("compute_mastery", concept_id="c1") as span:
        span.set_attr("delta", 0.04)

    assert len(tracer.spans) == 1
    recorded = tracer.spans[0]
    assert recorded.name == "compute_mastery"
    assert recorded.attrs["concept_id"] == "c1"
    assert recorded.attrs["delta"] == 0.04
    assert recorded.finished is True


def test_container_telemetry_accessors_are_singletons() -> None:
    container_mod = from_finals("01_source/01_application/07_infrastructure/00_di/container.py")
    container = container_mod.Container()

    logger_a = container.logger("hcie.test")
    logger_b = container.logger("hcie.test")
    metrics_a = container.metrics_recorder()
    metrics_b = container.metrics_recorder()
    tracer_a = container.tracer()
    tracer_b = container.tracer()

    assert logger_a is logger_b
    assert metrics_a is metrics_b
    assert tracer_a is tracer_b

    # Different logger name must yield a different instance
    logger_other = container.logger("hcie.other")
    assert logger_other is not logger_a
