"""
OpenTelemetry Setup for HCIE System
Configures distributed tracing and metrics collection
"""

import os
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
import logging

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

def _initialize_metrics():
    """Initialize all metrics after provider is set"""
    global meter, request_counter, request_duration, kafka_events_counter
    global postgres_operations_counter, redis_operations_counter
    global interaction_counter, interaction_reward_sum, submission_counter
    global transfer_events_counter, mastery_updates_counter, interaction_reward_histogram
    
    meter = metrics.get_meter(__name__)
    
    # Request metrics
    request_counter = meter.create_counter(
        "hcie_requests_total",
        description="Total number of HTTP requests"
    )
    
    request_duration = meter.create_histogram(
        "hcie_request_duration_seconds",
        description="HTTP request duration in seconds"
    )
    
    # Event metrics
    kafka_events_counter = meter.create_counter(
        "hcie_kafka_events_total",
        description="Total number of Kafka events"
    )
    
    # Database metrics
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
    # Get configuration from environment
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    otlp_protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    
    # Create resource with service information
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("ENVIRONMENT", "production"),
    })
    
    # Setup Tracing
    logger.info(f"Setting up OpenTelemetry tracing for {service_name}")
    
    trace_provider = TracerProvider(resource=resource)
    
    # Set up OTLP exporter for traces
    if otlp_protocol == "grpc":
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    else:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPOtlpSpanExporter
        otlp_exporter = HTTPOtlpSpanExporter(endpoint=otlp_endpoint)
    
    # Add batch processor for better performance
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace_provider.add_span_processor(span_processor)
    
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
    
    # NOW initialize metrics after provider is set
    _initialize_metrics()
    
    # Instrument common libraries
    logger.info("Setting up OpenTelemetry instrumentation")
    
    # FastAPI instrumentation
    try:
        FastAPIInstrumentor().instrument()
        logger.info("FastAPI instrumentation enabled")
    except Exception as e:
        logger.warning(f"FastAPI instrumentation failed: {e}")
    
    # PostgreSQL instrumentation
    try:
        Psycopg2Instrumentor().instrument()
        logger.info("PostgreSQL instrumentation enabled")
    except Exception as e:
        logger.warning(f"PostgreSQL instrumentation failed: {e}")
    
    # Redis instrumentation
    try:
        RedisInstrumentor().instrument()
        logger.info("Redis instrumentation enabled")
    except Exception as e:
        logger.warning(f"Redis instrumentation failed: {e}")
    
    logger.info("OpenTelemetry setup complete")

# Convenience functions for creating metrics
def get_tracer(name: str = __name__):
    """Get a tracer instance"""
    return trace.get_tracer(name)

def get_meter(name: str = __name__):
    """Get a meter instance"""
    return metrics.get_meter(name)

# Global tracer and meter instances (initialized after setup)
tracer = None
meter = None

def _get_tracer():
    """Get tracer instance (lazy initialization)"""
    global tracer
    if tracer is None:
        tracer = get_tracer()
    return tracer

def _get_meter():
    """Get meter instance (lazy initialization)"""
    global meter
    if meter is None:
        meter = get_meter()
    return meter
