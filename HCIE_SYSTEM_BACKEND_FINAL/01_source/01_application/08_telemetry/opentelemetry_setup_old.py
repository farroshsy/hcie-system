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

def setup_opentelemetry(service_name: str = "hcie-api"):
    """
    Setup OpenTelemetry for distributed tracing and metrics
    
    Args:
        service_name: Name of the service being instrumented
    """
    
    # Get configuration from environment
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    otlp_protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    prometheus_endpoint = os.getenv("OTEL_EXPORTER_PROMETHEXPORT_ENDPOINT", "http://otel-collector:8889")
    
    # Create resource with service information
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
        "environment": os.getenv("OTEL_RESOURCE_ATTRIBUTES", "environment=production").split(",")[0].split("=")[1],
        "deployment.environment": os.getenv("OTEL_RESOURCE_ATTRIBUTES", "environment=production").split(",")[0].split("=")[1],
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
    
    metrics.set_meter_provider(meter_provider)
    
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
    
    logger.info(f"OpenTelemetry setup complete for {service_name}")
    return trace_provider, meter_provider

def get_tracer(name: str):
    """Get a tracer for the specified name"""
    return trace.get_tracer(name)

def get_meter(name: str):
    """Get a meter for the specified name"""
    return metrics.get_meter(name)

# Create global tracer and meter
tracer = get_tracer("hcie-tracer")
meter = get_meter("hcie-meter")

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
