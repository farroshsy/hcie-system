"""
Prometheus Middleware for HCIE System
Exposes Prometheus metrics at /metrics endpoint
"""

import logging
import time
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry

logger = logging.getLogger(__name__)

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to expose Prometheus metrics"""

    # Class-level registry to prevent duplication across instances
    _registry = None
    _metrics_initialized = False

    def __init__(self, app, app_name: str = "hcie-api"):
        super().__init__(app)
        self.app_name = app_name

        # Use class-level registry to prevent duplication
        if PrometheusMiddleware._registry is None:
            PrometheusMiddleware._registry = CollectorRegistry()
        self.registry = PrometheusMiddleware._registry

        # Initialize metrics only once
        if not PrometheusMiddleware._metrics_initialized:
            self._initialize_metrics(app_name)
            PrometheusMiddleware._metrics_initialized = True
        else:
            # Reuse existing metrics
            self._get_existing_metrics(app_name)

    def _initialize_metrics(self, app_name: str):
        """Initialize metrics with custom registry"""
        # Initialize metrics with custom registry
        self.request_count = Counter(
            f'{app_name}_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )

        self.request_duration = Histogram(
            f'{app_name}_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint', 'status_code'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )

        self.active_connections = Gauge(
            f'{app_name}_active_connections',
            'Number of active connections',
            registry=self.registry
        )

        self.kafka_events_produced = Counter(
            f'{app_name}_kafka_events_produced_total',
            'Total Kafka events produced',
            ['topic', 'event_type'],
            registry=self.registry
        )

        self.kafka_events_consumed = Counter(
            f'{app_name}_kafka_events_consumed_total',
            'Total Kafka events consumed',
            ['topic', 'event_type'],
            registry=self.registry
        )

        self.outbox_events_total = Counter(
            f'{app_name}_outbox_events_total',
            'Total outbox events',
            ['event_type', 'status'],
            registry=self.registry
        )

        self.outbox_events_pending = Gauge(
            f'{app_name}_outbox_events_pending',
            'Number of pending outbox events',
            registry=self.registry
        )

        # 🔥 OBSERVABILITY: Add canonical state metrics for research validity
        self.canonical_state_reads = Counter(
            f'{app_name}_canonical_state_reads_total',
            'Total canonical state reads from Postgres',
            registry=self.registry
        )

        self.canonical_state_misses = Counter(
            f'{app_name}_canonical_state_misses_total',
            'Total canonical state misses (cold starts)',
            registry=self.registry
        )

        self.canonical_state_miss_rate = Gauge(
            f'{app_name}_canonical_state_miss_rate',
            'Canonical state miss rate (misses / reads)',
            registry=self.registry
        )

        # 🔥 OBSERVABILITY: Add state source tracking for research validity
        self.learning_state_source = Counter(
            f'{app_name}_learning_state_source_total',
            'Total learning operations by state source',
            ['state_source'],
            registry=self.registry
        )

        logger.info(f"✅ PrometheusMiddleware metrics initialized for {app_name}")

    def _get_existing_metrics(self, app_name: str):
        """Get references to existing metrics from registry"""
        # Get existing metrics from registry
        for metric in self.registry.collect():
            metric_name = metric.name
            if metric_name == f'{app_name}_http_requests_total':
                self.request_count = metric
            elif metric_name == f'{app_name}_http_request_duration_seconds':
                self.request_duration = metric
            elif metric_name == f'{app_name}_active_connections':
                self.active_connections = metric
            elif metric_name == f'{app_name}_kafka_events_produced_total':
                self.kafka_events_produced = metric
            elif metric_name == f'{app_name}_kafka_events_consumed_total':
                self.kafka_events_consumed = metric
            elif metric_name == f'{app_name}_outbox_events_total':
                self.outbox_events_total = metric
            elif metric_name == f'{app_name}_outbox_events_pending':
                self.outbox_events_pending = metric
            elif metric_name == f'{app_name}_canonical_state_reads_total':
                self.canonical_state_reads = metric
            elif metric_name == f'{app_name}_canonical_state_misses_total':
                self.canonical_state_misses = metric
            elif metric_name == f'{app_name}_canonical_state_miss_rate':
                self.canonical_state_miss_rate = metric
            elif metric_name == f'{app_name}_learning_state_source_total':
                self.learning_state_source = metric

        logger.debug(f"✅ PrometheusMiddleware reused existing metrics for {app_name}")
        
        logger.info(f"✅ PrometheusMiddleware initialized for {app_name}")
    
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Record metrics
        end_time = time.time()
        
        # Record request metrics
        self.request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()
        
        # Record request duration
        self.request_duration.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).observe(end_time - start_time)
        
        # Update active connections (this is a simple approximation)
        self.active_connections.set(1)
        
        return response
    
    async def metrics(self, request: Request):
        """Expose Prometheus metrics"""
        if request.method != "GET":
            return Response("Method Not Allowed", status_code=405)
        
        # Generate latest metrics using custom registry
        try:
            metrics_data = generate_latest(self.registry)
            
            return Response(
                metrics_data,
                media_type=CONTENT_TYPE_LATEST,
                headers={"Content-Type": "text/plain; version=0.0.4"}
            )
        except Exception as e:
            logger.error(f"❌ Failed to generate metrics: {e}")
            return Response("Internal Server Error", status_code=500)
    
    def increment_kafka_events_produced(self, topic: str, event_type: str):
        """Increment Kafka events produced counter"""
        self.kafka_events_produced.labels(topic=topic, event_type=event_type).inc()
    
    def increment_kafka_events_consumed(self, topic: str, event_type: str):
        """Increment Kafka events consumed counter"""
        self.kafka_events_consumed.labels(topic=topic, event_type=event_type).inc()
    
    def increment_outbox_events_total(self, event_type: str, status: str):
        """Increment outbox events total counter"""
        self.outbox_events_total.labels(event_type=event_type, status=status).inc()
    
    def update_outbox_events_pending(self, count: int):
        """Update outbox events pending gauge"""
        self.outbox_events_pending.set(count)
    
    def increment_canonical_state_reads(self):
        """Increment canonical state reads counter"""
        self.canonical_state_reads.inc()
    
    def increment_canonical_state_misses(self):
        """Increment canonical state misses counter"""
        self.canonical_state_misses.inc()
    
    def update_canonical_state_miss_rate(self, miss_rate: float):
        """Update canonical state miss rate gauge"""
        self.canonical_state_miss_rate.set(miss_rate)
    
    def increment_learning_state_source(self, state_source: str):
        """Increment learning state source counter"""
        self.learning_state_source.labels(state_source=state_source).inc()
