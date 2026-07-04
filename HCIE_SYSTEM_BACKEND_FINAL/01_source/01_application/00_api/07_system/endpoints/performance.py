"""
System Performance API - Performance metrics and monitoring
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/performance")
async def get_system_performance() -> Dict[str, Any]:
    """Get comprehensive system performance metrics"""
    try:
        from app.services import get_service_factory
        sf = get_service_factory()
        
        # Get tiered reconstructor for performance metrics
        task_service = sf.get_task_service()
        
        if not hasattr(task_service, 'tiered_reconstructor') or not task_service.tiered_reconstructor:
            logger.warning("⚠️ Tiered reconstructor not available for performance metrics")
            return {
                "status": "limited",
                "message": "Tiered reconstructor not initialized",
                "basic_metrics": {
                    "timestamp": "2026-04-27T00:00:00Z",
                    "services": {
                        "task_service": "available",
                        "tiered_reconstruction": "unavailable"
                    }
                }
            }
        
        reconstructor = task_service.tiered_reconstructor
        stats = reconstructor.get_system_stats()
        
        # Build comprehensive performance report
        performance_data = {
            "timestamp": "2026-04-27T00:00:00Z",
            "status": "healthy",
            "tiered_system": stats,
            "infrastructure": {
                "cache_hit_rate_percent": stats.get('performance', {}).get('cache_hit_rate_percent', 0),
                "memory_usage_mb": stats.get('memory_usage_mb', 0),
                "hot_capacity_utilization": stats.get('hot_capacity', '0/1000'),
                "total_tracked_users": stats.get('total_tracked', 0),
                "total_users_in_db": stats.get('total_users_in_db', 0)
            },
            "latency_metrics": stats.get('performance', {}),
            "efficiency": {
                "hot_users_per_mb": 0,
                "cache_efficiency": "high" if stats.get('performance', {}).get('cache_hit_rate_percent', 0) > 90 else "medium",
                "memory_efficiency": "excellent" if stats.get('memory_usage_mb', 0) < 100 else "good"
            }
        }
        
        # Calculate derived metrics
        memory_usage = stats.get('memory_usage_mb', 0)
        hot_users = stats.get('hot_users', 0)
        if memory_usage > 0:
            performance_data["efficiency"]["hot_users_per_mb"] = hot_users / memory_usage
        
        logger.info("📊 Retrieved system performance metrics")
        return performance_data
        
    except Exception as e:
        logger.error(f"❌ Failed to get system performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")

@router.get("/performance/latency")
async def get_latency_metrics() -> Dict[str, Any]:
    """Get detailed latency metrics by tier"""
    try:
        from app.services import get_service_factory
        sf = get_service_factory()
        
        task_service = sf.get_task_service()
        
        if not hasattr(task_service, 'tiered_reconstructor') or not task_service.tiered_reconstructor:
            raise HTTPException(status_code=404, detail="Tiered reconstructor not available")
        
        reconstructor = task_service.tiered_reconstructor
        metrics = reconstructor.metrics
        
        def _avg(lst):
            return sum(lst) / len(lst) if lst else 0
        
        latency_data = {
            "timestamp": "2026-04-27T00:00:00Z",
            "tier_latency": {
                "hot": {
                    "avg_ms": round(_avg(metrics['hot_access_time_ms']), 3),
                    "min_ms": min(metrics['hot_access_time_ms']) if metrics['hot_access_time_ms'] else 0,
                    "max_ms": max(metrics['hot_access_time_ms']) if metrics['hot_access_time_ms'] else 0,
                    "samples": len(metrics['hot_access_time_ms'])
                },
                "warm": {
                    "avg_ms": round(_avg(metrics['warm_reconstruction_time_ms']), 3),
                    "min_ms": min(metrics['warm_reconstruction_time_ms']) if metrics['warm_reconstruction_time_ms'] else 0,
                    "max_ms": max(metrics['warm_reconstruction_time_ms']) if metrics['warm_reconstruction_time_ms'] else 0,
                    "samples": len(metrics['warm_reconstruction_time_ms'])
                },
                "cold": {
                    "avg_ms": round(_avg(metrics['cold_reconstruction_time_ms']), 3),
                    "min_ms": min(metrics['cold_reconstruction_time_ms']) if metrics['cold_reconstruction_time_ms'] else 0,
                    "max_ms": max(metrics['cold_reconstruction_time_ms']) if metrics['cold_reconstruction_time_ms'] else 0,
                    "samples": len(metrics['cold_reconstruction_time_ms'])
                }
            },
            "performance_classification": {
                "excellent": "<1ms",
                "good": "1-5ms", 
                "acceptable": "5-20ms",
                "slow": ">20ms"
            }
        }
        
        logger.info("⚡ Retrieved latency metrics")
        return latency_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get latency metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve latency metrics")
