"""
OpenTelemetry Setup for HCIE System
Configures distributed tracing and metrics collection
"""

import os
import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
try:
    from opentelemetry.sdk.metrics.export.console import ConsoleMetricReader
except ImportError:
    ConsoleMetricReader = None
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.resources import Resource, ResourceAttributes
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

try:
    from app.infrastructure.di.config_factory import build_config_provider
except Exception:
    build_config_provider = None

logger = logging.getLogger(__name__)

# Global metrics variables (will be initialized after setup)
request_counter = None
request_duration = None
kafka_events_counter = None
postgres_operations_counter = None
redis_operations_counter = None
interaction_counter = None
interaction_reward_sum = None
submission_counter = None
transfer_events_counter = None
mastery_updates_counter = None
interaction_reward_histogram = None
latency_histogram = None

def _get_config_str(key: str, default: str) -> str:
    """Read telemetry config through the Phase 5 provider when available.

    This removes the old BACKENDV2 `from config.settings import settings`
    dependency. If the `hcie/` shim is not importable yet, fall back to
    environment variables so standalone tooling can still import this module.
    """
    if build_config_provider is None:
        return os.getenv(key.upper(), default)
    return build_config_provider().get_str(key, default)

def _initialize_metrics():
    """Initialize all metrics after provider is set"""
    global meter, request_counter, request_duration, kafka_events_counter
    global postgres_operations_counter, redis_operations_counter
    global interaction_counter, interaction_reward_sum, submission_counter
    global transfer_events_counter, mastery_updates_counter, interaction_reward_histogram
    global latency_histogram
    
    meter = metrics.get_meter(__name__)
    
    # Common metrics
    request_counter = meter.create_counter(
        "hcie_requests_total",
        description="Total number of requests"
    )
    
    request_duration = meter.create_histogram(
        "hcie_request_duration_seconds",
        description="Request duration in seconds"
    )
    
    kafka_events_counter = meter.create_counter(
        "hcie_kafka_events_total",
        description="Total number of Kafka events"
    )
    
    postgres_operations_counter = meter.create_counter(
        "hcie_postgres_operations_total",
        description="Total number of PostgreSQL operations"
    )
    
    redis_operations_counter = meter.create_counter(
        "hcie_redis_operations_total",
        description="Total number of Redis operations"
    )
    
    # Research metrics for Grafana Alerting
    interaction_counter = meter.create_counter(
        "hcie_interaction_reward_count",
        description="Total number of interactions",
        unit="1"
    )
    
    interaction_reward_sum = meter.create_counter(
        "hcie_interaction_reward_sum",
        description="Sum of all interaction rewards",
        unit="1"
    )
    
    # Critical alerting metrics for transfer learning
    submission_counter = meter.create_counter(
        "hcie_submissions_total",
        description="Total number of task submissions",
        unit="1"
    )
    
    transfer_events_counter = meter.create_counter(
        "hcie_transfer_events_total",
        description="Total number of transfer events applied",
        unit="1"
    )
    
    mastery_updates_counter = meter.create_counter(
        "hcie_mastery_updates_total",
        description="Total number of mastery updates",
        unit="1"
    )
    
    # Production-grade metrics
    latency_histogram = meter.create_histogram(
        "hcie_response_time_seconds",
        description="API response time in seconds",
        unit="s"
    )
    
    kafka_events_counter = meter.create_counter(
        "hcie_kafka_events_total",
        description="Total number of Kafka events processed",
        unit="1"
    )
    
    interaction_reward_histogram = meter.create_histogram(
        "hcie_interaction_reward",
        description="Reward values for interactions",
        unit="1"
    )

def setup_opentelemetry(service_name: str = "hcie-api"):
    """
    Setup OpenTelemetry for distributed tracing and metrics
    
    Args:
        service_name: Name of the service being instrumented
    """
    
    # Get configuration through the canonical provider. Defaults stay aligned
    # with the old Settings object for Windows host access.
    otlp_endpoint = _get_config_str("otel_exporter_otlp_endpoint", "http://localhost:4317")
    otlp_protocol = _get_config_str("otel_exporter_otlp_protocol", "grpc")
    enable_otlp_exporter = os.getenv("HCIE_ENABLE_OTLP_EXPORTER", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    prometheus_endpoint = os.getenv("OTEL_EXPORTER_PROMETHEXPORT_ENDPOINT", "http://localhost:8889")
    
    # Create resource with service information
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("ENVIRONMENT", "production"),
    })
    
    # Setup Tracing
    logger.info(f"Setting up OpenTelemetry tracing for {service_name}")
    
    trace_provider = TracerProvider(resource=resource)
    
    if enable_otlp_exporter:
        # Set up OTLP exporter for traces
        if otlp_protocol == "grpc":
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        else:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPOtlpSpanExporter
            otlp_exporter = HTTPOtlpSpanExporter(endpoint=otlp_endpoint)

        # Add batch processor for better performance
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace_provider.add_span_processor(span_processor)
    else:
        logger.info("OTLP trace exporter disabled; Prometheus metrics remain available")
    
    # Set as global tracer provider
    trace.set_tracer_provider(trace_provider)
    
    # Setup Metrics
    logger.info(f"Setting up OpenTelemetry metrics for {service_name}")
    
    # Set up Prometheus reader for direct scraping
    prometheus_reader = PrometheusMetricReader()
    
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[prometheus_reader]
    )
    
    # CRITICAL: Set provider BEFORE any metrics are used
    metrics.set_meter_provider(meter_provider)
    
    # CRITICAL: Initialize metrics AFTER provider is set
    _initialize_metrics()
    
    # Instrument common libraries + optional log/profiling sinks (all gated/tolerant).
    _instrument_libraries()
    _setup_otlp_logs(resource, otlp_endpoint, otlp_protocol)
    _setup_pyroscope(service_name)

    logger.info("OpenTelemetry setup complete")


def _instrument_libraries():
    """Best-effort auto-instrumentation of FastAPI / psycopg2 / redis."""
    logger.info("Setting up OpenTelemetry instrumentation")
    for name, instrumentor in (("FastAPI", FastAPIInstrumentor),
                               ("PostgreSQL", Psycopg2Instrumentor),
                               ("Redis", RedisInstrumentor)):
        try:
            instrumentor().instrument()
            logger.info(f"{name} instrumentation enabled")
        except Exception as e:
            logger.warning(f"{name} instrumentation failed: {e}")


def _setup_otlp_logs(resource, otlp_endpoint: str, otlp_protocol: str = "grpc"):
    """Ship application logs to Loki via OTLP -> otel-collector (loki exporter).

    Gated by ENABLE_OTLP_LOGS (default off) so the default stack is unchanged. Uses the
    already-installed opentelemetry-exporter-otlp; no new dependency. Enable alongside the
    `tracing` compose profile (which runs loki + otel-collector's logs pipeline).
    """
    if os.getenv("ENABLE_OTLP_LOGS", "false").lower() not in ("1", "true", "yes"):
        return
    try:
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        if otlp_protocol == "grpc":
            from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
            exporter = OTLPLogExporter(endpoint=otlp_endpoint, insecure=True)
        else:
            from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
            exporter = OTLPLogExporter(endpoint=otlp_endpoint)
        provider = LoggerProvider(resource=resource)
        provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
        set_logger_provider(provider)
        logging.getLogger().addHandler(LoggingHandler(level=logging.INFO, logger_provider=provider))
        logger.info("OTLP log export enabled (-> Loki via otel-collector)")
    except Exception as e:
        logger.warning(f"OTLP log export setup failed: {e}")


def _setup_pyroscope(service_name: str):
    """Continuous profiling to Pyroscope. Gated by PYROSCOPE_SERVER_ADDRESS (off by default).

    Requires the `pyroscope-io` package (installed in the api image). Enable by setting
    PYROSCOPE_SERVER_ADDRESS=http://pyroscope:4040 and running the `tracing` profile.
    """
    addr = os.getenv("PYROSCOPE_SERVER_ADDRESS")
    if not addr:
        return
    try:
        import pyroscope
        pyroscope.configure(
            application_name=os.getenv("PYROSCOPE_APPLICATION_NAME", service_name),
            server_address=addr,
            tags={"service": service_name, "env": os.getenv("ENVIRONMENT", "production")},
        )
        logger.info(f"Pyroscope profiling enabled -> {addr}")
    except Exception as e:
        logger.warning(f"Pyroscope setup failed: {e}")

# Convenience functions for creating metrics
def get_tracer(name: str = __name__):
    """Get a tracer instance"""
    return trace.get_tracer(name)

def get_meter(name: str = __name__):
    """Get a meter instance"""
    return metrics.get_meter(name)

# Create global tracer and meter (after setup)
tracer = None
meter = None

def _get_tracer():
    """Get tracer instance (lazy initialization)"""
    global tracer
    if tracer is None:
        tracer = get_tracer("hcie-tracer")
    return tracer

def _get_meter():
    """Get meter instance (lazy initialization)"""
    global meter
    if meter is None:
        meter = get_meter("hcie-meter")
    return meter
