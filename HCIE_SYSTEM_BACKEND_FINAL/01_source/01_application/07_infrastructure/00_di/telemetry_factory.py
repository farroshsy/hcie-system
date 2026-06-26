"""Telemetry adapters + factories for Phase 6.

Provides concrete implementations of:

- `LoggerProtocol`        -> `StdLoggingLogger`   (stdlib `logging`)
- `MetricsRecorderProtocol`-> `NoopMetricsRecorder` (default)
- `TracerProtocol`         -> `NoopTracer`         (default)

The no-op variants are the default because the live runtime continues to
boot Prometheus / OpenTelemetry through `app.telemetry.opentelemetry_setup`.
Migrating those globals onto the protocol surface is a follow-up; the
protocols exist so new core code can take a dependency on telemetry
without coupling to the global state.

A future `PrometheusMetricsRecorder` adapter would wrap the existing
prometheus_client `Counter` / `Histogram` objects already created by
`PrometheusMiddleware`; deliberately omitted here to keep Phase 6 tight.
"""

from __future__ import annotations

import logging
from contextlib import AbstractContextManager
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Logger adapter
# ---------------------------------------------------------------------------

class StdLoggingLogger:
    """`LoggerProtocol` adapter over the stdlib `logging` module.

    Structured fields are appended as a `key=value ...` suffix; if the
    underlying handler supports `extra=`, those fields are also attached
    so JSON-formatted handlers see them.
    """

    def __init__(self, name: str = "hcie", logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger if logger is not None else logging.getLogger(name)

    @staticmethod
    def _format(msg: str, fields: Dict[str, Any]) -> str:
        if not fields:
            return msg
        suffix = " ".join(f"{k}={v}" for k, v in fields.items())
        return f"{msg} {suffix}"

    def debug(self, msg: str, **fields: Any) -> None:
        self._logger.debug(self._format(msg, fields), extra={"fields": fields} if fields else None)

    def info(self, msg: str, **fields: Any) -> None:
        self._logger.info(self._format(msg, fields), extra={"fields": fields} if fields else None)

    def warning(self, msg: str, **fields: Any) -> None:
        self._logger.warning(self._format(msg, fields), extra={"fields": fields} if fields else None)

    def error(self, msg: str, **fields: Any) -> None:
        self._logger.error(self._format(msg, fields), extra={"fields": fields} if fields else None)


def build_logger(name: str = "hcie") -> StdLoggingLogger:
    return StdLoggingLogger(name=name)


# ---------------------------------------------------------------------------
# Metrics adapter
# ---------------------------------------------------------------------------

class NoopMetricsRecorder:
    """`MetricsRecorderProtocol` no-op default."""

    def __init__(self) -> None:
        # Counters captured in-memory for tests / debug. Production
        # callers should replace this with a Prometheus adapter.
        self.events: list = []

    def incr(self, name: str, value: float = 1.0, **tags: str) -> None:
        self.events.append(("incr", name, value, dict(tags)))

    def observe(self, name: str, value: float, **tags: str) -> None:
        self.events.append(("observe", name, value, dict(tags)))

    def gauge(self, name: str, value: float, **tags: str) -> None:
        self.events.append(("gauge", name, value, dict(tags)))


def build_metrics_recorder() -> NoopMetricsRecorder:
    return NoopMetricsRecorder()


# ---------------------------------------------------------------------------
# Tracer adapter
# ---------------------------------------------------------------------------

class NoopSpan(AbstractContextManager):
    """`SpanProtocol` no-op. Records attrs for assertion in tests."""

    def __init__(self, name: str, attrs: Optional[Dict[str, Any]] = None) -> None:
        self.name = name
        self.attrs: Dict[str, Any] = dict(attrs or {})
        self.finished: bool = False

    def set_attr(self, key: str, value: Any) -> None:
        self.attrs[key] = value

    def finish(self) -> None:
        self.finished = True

    def __enter__(self) -> "NoopSpan":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.finish()


class NoopTracer:
    """`TracerProtocol` no-op default."""

    def __init__(self) -> None:
        self.spans: list = []

    def start_span(self, name: str, **attrs: Any) -> NoopSpan:
        span = NoopSpan(name=name, attrs=attrs)
        self.spans.append(span)
        return span


class OtelSpan(AbstractContextManager):
    """OpenTelemetry-backed span implementing ``SpanProtocol``."""

    def __init__(self, otel_span: Any, recorded: list, name: Optional[str] = None) -> None:
        self._span = otel_span
        self._recorded = recorded
        self.attrs: Dict[str, Any] = {}
        # Record the name passed to start_span. OTel span objects don't reliably expose a
        # readable `.name`, so deriving it via getattr() silently mislabelled every span
        # 'span'; the caller's name is authoritative (getattr kept only as a last resort).
        self.name = name if name is not None else getattr(otel_span, "name", "span")
        self.finished = False

    def set_attr(self, key: str, value: Any) -> None:
        self.attrs[key] = value
        if self._span is not None and hasattr(self._span, "set_attribute"):
            try:
                self._span.set_attribute(key, value)
            except Exception:
                pass

    def finish(self) -> None:
        if self.finished:
            return
        self.finished = True
        if self._span is not None and hasattr(self._span, "end"):
            try:
                self._span.end()
            except Exception:
                pass

    def __enter__(self) -> "OtelSpan":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is not None and self._span is not None:
            try:
                self._span.record_exception(exc)
            except Exception:
                pass
        self._recorded.append(self)
        self.finish()


class OtelTracer:
    """`TracerProtocol` adapter over the global OpenTelemetry tracer."""

    def __init__(self, service_name: str = "hcie-its") -> None:
        self.service_name = service_name
        self.spans: list = []
        self._tracer = None
        try:
            from opentelemetry import trace

            self._tracer = trace.get_tracer(service_name)
        except Exception:
            self._tracer = None

    def start_span(self, name: str, **attrs: Any) -> Any:
        if self._tracer is not None:
            try:
                otel_span = self._tracer.start_span(name)
                wrapped = OtelSpan(otel_span, self.spans, name=name)
                for key, value in attrs.items():
                    wrapped.set_attr(key, value)
                return wrapped
            except Exception:
                pass
        fallback = NoopSpan(name=name, attrs=attrs)
        self.spans.append(fallback)
        return fallback


def build_tracer(*, prefer_otel: bool = True) -> Any:
    if prefer_otel:
        tracer = OtelTracer()
        if tracer._tracer is not None:
            return tracer
    return NoopTracer()
