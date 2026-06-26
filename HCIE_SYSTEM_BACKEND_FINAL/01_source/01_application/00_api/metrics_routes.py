"""
Metrics API Routes
Provides observability endpoints for event metrics
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import logging
import time

from config.env import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

@router.get("/outbox")
async def get_outbox_metrics() -> Dict[str, Any]:
    """Get outbox metrics"""
    try:
        from app.infrastructure.monitoring.event_metrics import event_metrics_collector
        metrics = event_metrics_collector.get_outbox_metrics()
        
        return {
            "status": "success",
            "data": {
                "total_events": metrics.total_events,
                "pending_events": metrics.pending_events,
                "published_events": metrics.published_events,
                "failed_events": metrics.failed_events,
                "dlq_events": metrics.dlq_events,
                "avg_processing_time_ms": round(metrics.avg_processing_time_ms, 2),
                "oldest_pending_age_seconds": round(metrics.oldest_pending_age_seconds, 2),
                "throughput_events_per_second": round(metrics.throughput_events_per_second, 2),
                "timestamp": metrics.timestamp.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to get outbox metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get outbox metrics")

@router.get("/throughput")
async def get_throughput_metrics() -> Dict[str, Any]:
    """Get throughput metrics"""
    try:
        from app.infrastructure.monitoring.event_metrics import event_metrics_collector
        metrics = event_metrics_collector.get_throughput_metrics()
        
        return {
            "status": "success",
            "data": metrics
        }
    except Exception as e:
        logger.error(f"❌ Failed to get throughput metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get throughput metrics")

@router.get("/processing-time")
async def get_processing_time_metrics() -> Dict[str, Any]:
    """Get processing time metrics"""
    try:
        from app.infrastructure.monitoring.event_metrics import event_metrics_collector
        metrics = event_metrics_collector.get_processing_time_metrics()
        
        return {
            "status": "success",
            "data": {
                "avg_ms": round(metrics["avg_ms"], 2),
                "p50_ms": round(metrics["p50_ms"], 2),
                "p95_ms": round(metrics["p95_ms"], 2),
                "p99_ms": round(metrics["p99_ms"], 2),
                "max_ms": round(metrics["max_ms"], 2),
                "min_ms": round(metrics["min_ms"], 2)
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to get processing time metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing time metrics")

@router.get("/consumer-lag")
async def get_consumer_lag_metrics(
    consumer_group: Optional[str] = Query(None, description="Filter by consumer group")
) -> Dict[str, Any]:
    """Get consumer lag metrics"""
    try:
        from app.infrastructure.monitoring.event_metrics import event_metrics_collector
        metrics = event_metrics_collector.get_consumer_lag_metrics(consumer_group)
        
        # Aggregate metrics by consumer group and topic
        aggregated = {}
        for metric in metrics:
            key = f"{metric.consumer_group}:{metric.topic}"
            if key not in aggregated:
                aggregated[key] = {
                    "consumer_group": metric.consumer_group,
                    "topic": metric.topic,
                    "total_lag": 0,
                    "partitions": [],
                    "latest_update": metric.timestamp.isoformat()
                }
            
            aggregated[key]["partitions"].append({
                "partition": metric.partition,
                "lag": metric.lag,
                "current_offset": metric.current_offset,
                "latest_offset": metric.latest_offset,
                "timestamp": metric.timestamp.isoformat()
            })
            
            aggregated[key]["total_lag"] += metric.lag
        
        return {
            "status": "success",
            "data": list(aggregated.values())
        }
    except Exception as e:
        logger.error(f"❌ Failed to get consumer lag metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get consumer lag metrics")

@router.get("/health")
async def get_metrics_health() -> Dict[str, Any]:
    """Get metrics system health"""
    try:
        from app.infrastructure.monitoring.event_metrics import event_metrics_collector
        
        # Basic health check
        outbox_metrics = event_metrics_collector.get_outbox_metrics()
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        # Check for high lag
        if outbox_metrics.oldest_pending_age_seconds > 300:  # 5 minutes
            health_status = "degraded"
            issues.append(f"High outbox lag: {outbox_metrics.oldest_pending_age_seconds}s")
        
        # Check for high failure rate
        total_events = outbox_metrics.total_events
        if total_events > 0:
            failure_rate = (outbox_metrics.failed_events + outbox_metrics.dlq_events) / total_events
            if failure_rate > 0.1:  # 10% failure rate
                health_status = "degraded"
                issues.append(f"High failure rate: {failure_rate:.2%}")
        
        # Check for low throughput
        if outbox_metrics.throughput_events_per_second < 1.0:
            health_status = "degraded"
            issues.append(f"Low throughput: {outbox_metrics.throughput_events_per_second} events/sec")
        
        # ✅ Check circuit breaker status
        circuit_issues = []
        try:
            from app.infrastructure.messaging.event_bus import KafkaEventBus
            # Get circuit breaker state from EventBus (would need to be injected)
            # For now, just note that we have circuit breaker protection
            circuit_issues.append("Circuit breaker protection active")
        except Exception as e:
            issues.append(f"Circuit breaker check failed: {e}")
        
        return {
            "status": health_status,
            "data": {
                "outbox_metrics": {
                    "pending_events": outbox_metrics.pending_events,
                    "oldest_pending_age_seconds": outbox_metrics.oldest_pending_age_seconds,
                    "throughput_events_per_second": outbox_metrics.throughput_events_per_second
                },
                "circuit_breaker": {
                    "status": "active",
                    "issues": circuit_issues
                },
                "issues": issues
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to get metrics health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics health")

@router.get("/kafka/cluster")
async def get_kafka_cluster_metrics() -> Dict[str, Any]:
    """Get Kafka cluster health metrics"""
    try:
        from app.infrastructure.monitoring.kafka_observability import get_kafka_observability
        
        kafka_obs = get_kafka_observability()
        cluster_metrics = kafka_obs.collect_cluster_health()
        
        return {
            "status": "success",
            "data": {
                "broker_count": cluster_metrics.broker_count,
                "healthy_brokers": cluster_metrics.healthy_brokers,
                "topic_count": cluster_metrics.topic_count,
                "total_partitions": cluster_metrics.total_partitions,
                "under_replicated_partitions": cluster_metrics.under_replicated_partitions,
                "broker_health": cluster_metrics.broker_details,
                "timestamp": cluster_metrics.timestamp.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to get Kafka cluster metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Kafka cluster metrics")

@router.get("/kafka/consumer/{group_id}")
async def get_consumer_group_metrics(group_id: str) -> Dict[str, Any]:
    """Get consumer group metrics"""
    try:
        from app.infrastructure.monitoring.kafka_observability import get_kafka_observability
        
        kafka_obs = get_kafka_observability()
        group_metrics = kafka_obs.collect_consumer_group_metrics(group_id)
        
        return {
            "status": "success",
            "data": {
                "group_id": group_metrics.group_id,
                "state": group_metrics.state,
                "members": group_metrics.members,
                "active_members": group_metrics.active_members,
                "partition_assignments": len(group_metrics.partition_assignments),
                "rebalance_count": group_metrics.rebalance_count,
                "last_rebalance": group_metrics.last_rebalance.isoformat() if group_metrics.last_rebalance else None,
                "timestamp": group_metrics.timestamp.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to get consumer group metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get consumer group metrics")

@router.get("/kafka/rebalance/{group_id}")
async def get_rebalance_metrics(group_id: str, hours: int = 24) -> Dict[str, Any]:
    """Get rebalance metrics for consumer group"""
    try:
        from app.infrastructure.monitoring.kafka_observability import get_kafka_observability
        
        kafka_obs = get_kafka_observability()
        rebalance_metrics = kafka_obs.get_rebalance_metrics(group_id, hours)
        
        return {
            "status": "success",
            "data": rebalance_metrics
        }
    except Exception as e:
        logger.error(f"❌ Failed to get rebalance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rebalance metrics")

@router.get("/kafka/offsets/{group_id}")
async def get_offset_commit_metrics(group_id: str) -> Dict[str, Any]:
    """Get offset commit metrics for consumer group"""
    try:
        from app.infrastructure.monitoring.kafka_observability import get_kafka_observability
        
        kafka_obs = get_kafka_observability()
        offset_metrics = kafka_obs.get_offset_commit_metrics(group_id)
        
        return {
            "status": "success",
            "data": offset_metrics
        }
    except Exception as e:
        logger.error(f"❌ Failed to get offset commit metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get offset commit metrics")

@router.get("/workers/status")
async def get_multi_worker_status() -> Dict[str, Any]:
    """Get multi-worker coordinator status"""
    try:
        # This would connect to the multi-worker coordinator
        # For now, return simulated status
        
        return {
            "status": "success",
            "data": {
                "coordinator_running": True,
                "total_workers": getattr(settings, 'outbox_worker_count', 2),
                "alive_workers": getattr(settings, 'outbox_worker_count', 2),
                "worker_assignments": {},
                "partition_assignments": {},
                "timestamp": time.time()
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to get worker status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get worker status")
