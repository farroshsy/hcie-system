"""
Prometheus Metrics Middleware
Collects application metrics for monitoring
"""

import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ROUTE_CUTOVER_REQUESTS = Counter(
    'hcie_route_cutover_requests_total',
    'Requests grouped by canonical V3 vs transitional V2 surface for Phase 14h cutover tracking',
    ['method', 'surface', 'route_family', 'status_code']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Active connections',
    ['service']
)

KAFKA_EVENTS_PRODUCED = Counter(
    'kafka_events_produced_total',
    'Total Kafka events produced',
    ['topic', 'event_type']
)

KAFKA_EVENTS_CONSUMED = Counter(
    'kafka_events_consumed_total',
    'Total Kafka events consumed',
    ['topic', 'event_type']
)

POSTGRES_OPERATIONS = Counter(
    'postgres_operations_total',
    'Total PostgreSQL operations',
    ['operation', 'table', 'status']
)

REDIS_OPERATIONS = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status']
)

# Runtime metrics
RUNTIME_INTERACTIONS_TOTAL = Counter(
    'runtime_interactions_total',
    'Total runtime interactions processed'
)

RUNTIME_USERS_ACTIVE = Gauge(
    'runtime_users_active',
    'Number of active users in runtime'
)

RUNTIME_PROCESSING_TIME = Histogram(
    'runtime_processing_time_seconds',
    'Runtime processing time in seconds'
)


def _classify_cutover_route(path: str) -> tuple[str, str]:
    """Return low-cardinality route labels for V2 retirement decisions."""
    if path in {"/", "/healthz", "/readyz"}:
        return "probe", "health"
    if path in {"/metrics", "/docs", "/openapi.json"}:
        return "internal", path.strip("/") or "root"
    if path.startswith("/v3/learner"):
        return "canonical_v3", "learner"
    if path.startswith("/v3/research"):
        return "canonical_v3", "research"
    if path.startswith("/v3/experiments"):
        return "canonical_v3", "experiments"
    if path.startswith("/v3/admin"):
        return "canonical_v3", "admin"
    if path.startswith("/v3/service"):
        return "canonical_v3", "service"
    if path.startswith("/v3/runtime"):
        return "canonical_v3", "runtime"
    if path.startswith("/v3"):
        return "canonical_v3", "other"
    return "transitional_v2", "legacy"


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Prometheus metrics collection middleware"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Increment active connections
        ACTIVE_CONNECTIONS.labels(service='api').inc()
        
        try:
            response = await call_next(request)
            
            # Record request metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(time.time() - start_time)

            surface, route_family = _classify_cutover_route(request.url.path)
            ROUTE_CUTOVER_REQUESTS.labels(
                method=request.method,
                surface=surface,
                route_family=route_family,
                status_code=response.status_code,
            ).inc()
            
            return response
        
        finally:
            # Decrement active connections
            ACTIVE_CONNECTIONS.labels(service='api').dec()

class MetricsService:
    """Service for collecting custom metrics"""
    
    @staticmethod
    def record_kafka_event_produced(topic: str, event_type: str):
        """Record Kafka event produced"""
        KAFKA_EVENTS_PRODUCED.labels(topic=topic, event_type=event_type).inc()
    
    @staticmethod
    def record_kafka_event_consumed(topic: str, event_type: str):
        """Record Kafka event consumed"""
        KAFKA_EVENTS_CONSUMED.labels(topic=topic, event_type=event_type).inc()
    
    @staticmethod
    def record_postgres_operation(operation: str, table: str, status: str):
        """Record PostgreSQL operation"""
        POSTGRES_OPERATIONS.labels(operation=operation, table=table, status=status).inc()
    
    @staticmethod
    def record_redis_operation(operation: str, status: str):
        """Record Redis operation"""
        REDIS_OPERATIONS.labels(operation=operation, status=status).inc()

    @staticmethod
    def record_runtime_interaction():
        """Record runtime interaction processed"""
        RUNTIME_INTERACTIONS_TOTAL.inc()

    @staticmethod
    def set_active_users(count: int):
        """Set number of active users"""
        RUNTIME_USERS_ACTIVE.set(count)

    @staticmethod
    def observe_runtime_processing_time(seconds: float):
        """Observe runtime processing time"""
        RUNTIME_PROCESSING_TIME.observe(seconds)

# Export metrics endpoint
from fastapi import FastAPI

def add_metrics_endpoint(app: FastAPI):
    """Add Prometheus metrics endpoint to FastAPI app"""
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
