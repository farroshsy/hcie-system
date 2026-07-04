"""Telemetry ports for Phase 6 monitoring integration.

Phase 5 introduced `ConfigProviderProtocol` so core code stops touching
`os.environ`. This file does the analogous job for telemetry: logging,
metrics, and tracing. Core modules can depend on these protocols and the
composition root injects either the production adapter (stdlib logging
+ Prometheus client + OTel) or a no-op for tests.

Design choices:

- Minimal surface (3-4 methods per port). The full
  OpenTelemetry / Prometheus surface stays in the application-layer
  adapter; core only needs the parts it actually emits.
- `MetricsRecorderProtocol` uses simple counter / observe / gauge verbs
  rather than counter-vs-histogram type machinery, because most core
  emits are conceptual ("I observed mastery=0.4 for user=X") and the
  adapter decides the underlying instrument.
- `TracerProtocol.start_span` returns a context-manager-shaped
  `SpanProtocol`, so call sites can write:
    with tracer.start_span("compute_jt"):
        ...
- All protocols are `runtime_checkable` so the conformance tool
  (`check_protocols.py`) can statically verify the adapters.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LoggerProtocol(Protocol):
    """Structured logger surface for core modules."""

    def debug(self, msg: str, **fields: Any) -> None: ...
    def info(self, msg: str, **fields: Any) -> None: ...
    def warning(self, msg: str, **fields: Any) -> None: ...
    def error(self, msg: str, **fields: Any) -> None: ...


@runtime_checkable
class MetricsRecorderProtocol(Protocol):
    """Lightweight counter / histogram / gauge surface.

    Tags are string-valued for compatibility with both Prometheus labels
    and OTel attributes. Numeric tag values are the caller's job to
    stringify -- the contract stays narrow on purpose.
    """

    def incr(self, name: str, value: float = 1.0, **tags: str) -> None: ...
    def observe(self, name: str, value: float, **tags: str) -> None: ...
    def gauge(self, name: str, value: float, **tags: str) -> None: ...


@runtime_checkable
class SpanProtocol(Protocol):
    """Active span surface; doubles as a context manager."""

    def set_attr(self, key: str, value: Any) -> None: ...
    def finish(self) -> None: ...
    def __enter__(self) -> "SpanProtocol": ...
    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None: ...


@runtime_checkable
class TracerProtocol(Protocol):
    """Tracer surface; adapters wrap OTel `Tracer` or a no-op."""

    def start_span(self, name: str, **attrs: Any) -> SpanProtocol: ...
