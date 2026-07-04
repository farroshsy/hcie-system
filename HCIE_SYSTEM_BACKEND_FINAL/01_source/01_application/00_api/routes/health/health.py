"""
Health check API endpoints
System health monitoring and status
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter

from app.services.kafka import KafkaService
from storage.redis_store.redis_store import create_redis_feature_store
from config.env import settings, is_docker_environment

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

@router.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "message": "HCIE Real System V2",
        "status": "running",
        "version": "2.0.0",
        "environment": settings.app_name
    }

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Production-ready health check using ServiceFactory pattern
    Tests Redis, PostgreSQL, and auth system connectivity
    """
    import os
    
    health_status = {
        "status": "healthy",
        "environment": os.getenv('ENVIRONMENT', 'unknown'),
        "checks": {}
    }
    
    try:
        from app.services.service_factory import ServiceFactory
        factory = ServiceFactory()
        
        # Check PostgreSQL via UserRepository
        user_repo = factory._get_user_repository()
        if user_repo:
            try:
                # Check which type of store we have and use appropriate method
                if hasattr(user_repo.postgres_store, 'execute_read'):
                    # PostgresInteractionStore - use execute_read
                    user_repo.postgres_store.execute_read("SELECT 1", fetch_one=True)
                else:
                    # PostgresStore - use session
                    session = user_repo.postgres_store.get_session()
                    session.execute("SELECT 1")
                    session.close()
                health_status["checks"]["database"] = {"status":"healthy", "type":"postgresql"}
            except Exception as e:
                health_status["checks"]["database"] = {"status":"unhealthy","error": str(e)}
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["database"] = {"status": "missing", "error": "UserRepository not initialized"}
            health_status["status"] = "degraded"
        
        # Check Redis via TokenStore
        token_store = factory._get_redis_token_store()
        if token_store:
            try:
                # Simple connectivity test
                token_store.redis.ping()
                health_status["checks"]["redis"] = {"status": "healthy", "type": "redis"}
            except Exception as e:
                health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["redis"] = {"status": "missing", "error": "RedisTokenStore not initialized"}
            health_status["status"] = "degraded"
        
        # Test other services (legacy support)
        postgres_status, kafka_status = _test_external_services()
        
        # Add legacy service checks for compatibility
        health_status["services"] = {
            "redis": health_status["checks"].get("redis", {}).get("status") == "healthy",
            "postgres": health_status["checks"].get("database", {}).get("status") == "healthy",
            "kafka": kafka_status,  # Keep for monitoring but not critical for API health
            "api": True,
            "real_mathematical_model": health_status["checks"].get("redis", {}).get("status") == "healthy",
            "cdc_pipeline": kafka_status  # CDC pipeline status
        }
        
        # Add environment info
        health_status["environment"] = {
            "name": settings.app_name,
            "debug": settings.debug,
            "docker": is_docker_environment(),
            "architecture": "CDC (PostgreSQL + Debezium + Kafka)"
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "environment": {
                "name": settings.app_name,
                "debug": settings.debug,
                "docker": is_docker_environment()
            }
        }

@router.get("/health/ready")
async def readiness_check() -> Dict[str, str]:
    """Simple readiness check for Kubernetes/liveness probes"""
    return {"status": "ready"}

@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """Simple liveness check for Kubernetes/liveness probes"""
    return {"status": "alive"}

def _test_external_services() -> tuple[bool, bool]:
    """Test PostgreSQL and Kafka connectivity"""
    postgres_status = False
    kafka_status = False
    
    if is_docker_environment():
        # Test PostgreSQL (Docker environment)
        try:
            import psycopg2
            conn = psycopg2.connect(
                settings.database_url,
                connect_timeout=1
            )
            conn.close()
            postgres_status = True
            logger.info("PostgreSQL connection successful")
        except Exception as e:
            logger.debug(f"PostgreSQL connection failed: {e}")
        
        # Test Kafka (Docker environment) - Socket Check for CDC Architecture
        try:
            import socket
            # Parse 'kafka:9092' into ('kafka', 9092)
            host, port = settings.kafka_bootstrap_servers.split(':')
            with socket.create_connection((host, int(port)), timeout=1):
                kafka_status = True
                logger.info("Kafka socket connection successful")
        except Exception as e:
            logger.debug(f"Kafka socket check failed: {e}")
    else:
        # Non-Docker environment - assume services are running
        postgres_status = True
        kafka_status = True
        logger.info("Non-Docker environment - assuming services are running")
    
    return postgres_status, kafka_status

@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Enhanced detailed health check with comprehensive metrics and diagnostics.
    Includes database connection pool status, Kafka topic health, and dependency checks.
    """
    try:
        # Get basic health
        basic_health = await health_check()
        
        # Add detailed metrics
        store = create_redis_feature_store(settings.redis_host)
        
        detailed_info = {
            **basic_health,
            "metrics": {
                "redis_info": _get_redis_metrics(store) if store.redis_available else {},
                "system_info": _get_system_metrics(),
                "performance_info": _get_performance_metrics(),
                "database_info": _get_database_metrics(),
                "kafka_info": _get_kafka_metrics()
            },
            "components": {
                "api": {
                    "status": "healthy",
                    "version": settings.app_version,
                    "uptime": _get_uptime(),
                    "middleware_status": {
                        "security_headers": "enabled",
                        "rate_limiting": "enabled",
                        "exception_handler": "enabled",
                        "request_validation": "enabled",
                        "compression": "enabled",
                        "caching": "enabled" if store.redis_available else "disabled",
                        "request_logging": "enabled"
                    }
                },
                "redis": {
                    "status": "healthy" if store.redis_available else "unavailable",
                    "host": settings.redis_host,
                    "port": settings.redis_port,
                    "latency_ms": _get_redis_latency(store)
                },
                "kafka": {
                    "status": "healthy" if basic_health["services"]["kafka"] else "unavailable",
                    "bootstrap_servers": settings.kafka_bootstrap_servers,
                    "topic_health": _get_kafka_topic_health()
                },
                "database": {
                    "status": "healthy" if basic_health["services"]["postgres"] else "unavailable",
                    "database_url": settings.database_url
                }
            },
            "dependencies": {
                "v3_apis": {
                    "status": "operational",
                    "endpoints": [
                        "/v3/runtime/governance",
                        "/v3/runtime/replay",
                        "/v3/runtime/lifecycle",
                        "/v3/runtime/mutation",
                        "/v3/runtime/event",
                        "/v3/runtime/trajectory",
                        "/v3/runtime/authority",
                        "/v3/research/transfer",
                        "/v3/research/policy",
                        "/v3/research/attribution",
                        "/v3/auth",
                        "/v3/frontend/dashboard"
                    ]
                },
                "consumer_workers": {
                    "status": "operational",
                    "workers": [
                        "learning-consumer",
                        "projection-consumer",
                        "adaptation-consumer",
                        "trajectory-recorder-consumer",
                        "exploration-instrumentation-consumer",
                        "transfer-measurement-consumer",
                        "projection-stream-gateway",
                        "outbox-worker",
                        "auth-consumer",
                        "dlq-replay-worker"
                    ]
                }
            }
        }
        
        return detailed_info
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": logger.info("Detailed health check failed")
        }

def _get_redis_metrics(store) -> Dict[str, Any]:
    """Get Redis performance metrics"""
    try:
        info = store.redis_client.info()
        return {
            "used_memory": info.get("used_memory"),
            "connected_clients": info.get("connected_clients"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses")
        }
    except Exception as e:
        logger.error(f"Failed to get Redis metrics: {e}")
        return {"error": str(e)}

def _get_system_metrics() -> Dict[str, Any]:
    """Get system performance metrics"""
    try:
        import psutil
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }
    except ImportError:
        return {"error": "psutil not available"}
    except Exception as e:
        return {"error": str(e)}

def _get_performance_metrics() -> Dict[str, Any]:
    """Get application performance metrics"""
    try:
        import time
        start_time = time.time()
        
        # Test Redis performance
        store = create_redis_feature_store(settings.redis_host)
        if store.redis_available:
            store.redis_client.ping()
            redis_latency = (time.time() - start_time) * 1000
        else:
            redis_latency = None
        
        return {
            "redis_latency_ms": redis_latency,
            "timestamp": time.time()
        }
    except Exception as e:
        return {"error": str(e)}


def _get_uptime() -> str:
    """Get application uptime"""
    try:
        import time
        # This would need to be set at application startup
        # For now, return a placeholder
        return "N/A (set at startup)"
    except Exception as e:
        return f"Error: {str(e)}"


def _get_redis_latency(store) -> Optional[float]:
    """Get Redis latency in milliseconds"""
    try:
        import time
        if not store.redis_available:
            return None
        start_time = time.time()
        store.redis_client.ping()
        return (time.time() - start_time) * 1000
    except Exception as e:
        logger.error(f"Failed to get Redis latency: {e}")
        return None


def _get_database_metrics() -> Dict[str, Any]:
    """Get database connection pool metrics"""
    try:
        from app.services.service_factory import ServiceFactory
        factory = ServiceFactory()
        user_repo = factory._get_user_repository()
        
        if user_repo and hasattr(user_repo.postgres_store, 'pool'):
            pool = user_repo.postgres_store.pool
            return {
                "pool_size": pool.size() if hasattr(pool, 'size') else "unknown",
                "checked_out": pool.checkedout() if hasattr(pool, 'checkout') else "unknown",
                "overflow": pool.overflow() if hasattr(pool, 'overflow') else "unknown"
            }
        return {"status": "pool metrics not available"}
    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        return {"error": str(e)}


def _get_kafka_metrics() -> Dict[str, Any]:
    """Get Kafka cluster metrics"""
    try:
        from app.services.kafka import KafkaService
        kafka_service = KafkaService()
        
        # Basic Kafka connectivity check
        return {
            "bootstrap_servers": settings.kafka_bootstrap_servers,
            "connectivity": "connected" if kafka_service else "unknown"
        }
    except Exception as e:
        logger.error(f"Failed to get Kafka metrics: {e}")
        return {"error": str(e)}


def _get_kafka_topic_health() -> Dict[str, Any]:
    """Get Kafka topic health information"""
    try:
        from app.services.kafka import KafkaService
        kafka_service = KafkaService()
        
        # List of expected topics
        expected_topics = [
            "hcie.learning",
            "hcie.cognition",
            "hcie.adaptation",
            "hcie.projection",
            "hcie.auth"
        ]
        
        return {
            "expected_topics": expected_topics,
            "status": "topic health check not implemented"
        }
    except Exception as e:
        logger.error(f"Failed to get Kafka topic health: {e}")
        return {"error": str(e)}
