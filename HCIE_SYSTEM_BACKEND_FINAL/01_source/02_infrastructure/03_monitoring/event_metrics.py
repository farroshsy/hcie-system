"""
Event Metrics and Observability
Provides metrics collection for outbox lag, consumer lag, and event throughput
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class EventMetrics:
    """Event metrics data structure"""
    timestamp: datetime
    event_type: str
    topic: str
    status: str  # published, failed, dlq
    processing_time_ms: float
    retry_count: int = 0

@dataclass
class ConsumerLagMetrics:
    """Consumer lag metrics"""
    consumer_group: str
    topic: str
    partition: int
    current_offset: int
    latest_offset: int
    lag: int
    timestamp: datetime

@dataclass
class OutboxMetrics:
    """Outbox metrics"""
    total_events: int = 0
    pending_events: int = 0
    published_events: int = 0
    failed_events: int = 0
    dlq_events: int = 0
    avg_processing_time_ms: float = 0.0
    oldest_pending_age_seconds: float = 0.0
    throughput_events_per_second: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

class EventMetricsCollector:
    """Collects and manages event metrics"""
    
    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self.event_history = deque(maxlen=max_history_size)
        self.consumer_lag = defaultdict(list)
        self.outbox_metrics = OutboxMetrics()
        self.metrics_lock = threading.Lock()
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        
        # Performance tracking
        self.recent_throughput = deque(maxlen=60)  # Last 60 seconds
        self.recent_processing_times = deque(maxlen=1000)  # Last 1000 events
        
    def record_event(self, event_type: str, topic: str, status: str, 
                    processing_time_ms: float, retry_count: int = 0):
        """Record an event metric"""
        with self.metrics_lock:
            metric = EventMetrics(
                timestamp=datetime.utcnow(),
                event_type=event_type,
                topic=topic,
                status=status,
                processing_time_ms=processing_time_ms,
                retry_count=retry_count
            )
            
            self.event_history.append(metric)
            self.recent_processing_times.append(processing_time_ms)
            self._update_throughput()
            self._update_outbox_metrics()
    
    def record_consumer_lag(self, consumer_group: str, topic: str, partition: int,
                           current_offset: int, latest_offset: int):
        """Record consumer lag metric"""
        lag = latest_offset - current_offset
        
        with self.metrics_lock:
            lag_metric = ConsumerLagMetrics(
                consumer_group=consumer_group,
                topic=topic,
                partition=partition,
                current_offset=current_offset,
                latest_offset=latest_offset,
                lag=lag,
                timestamp=datetime.utcnow()
            )
            
            self.consumer_lag[f"{consumer_group}:{topic}:{partition}"].append(lag_metric)
            
            # Keep only recent metrics
            if len(self.consumer_lag[f"{consumer_group}:{topic}:{partition}"]) > 100:
                self.consumer_lag[f"{consumer_group}:{topic}:{partition}"].pop(0)
    
    def _update_throughput(self):
        """Update throughput calculation"""
        current_time = time.time()
        
        # Count events in last second
        recent_events = [m for m in self.event_history 
                         if current_time - m.timestamp.timestamp() < 1.0]
        
        self.recent_throughput.append(len(recent_events))
        
        # Keep only last 60 seconds
        if len(self.recent_throughput) > 60:
            self.recent_throughput.popleft()
    
    def _update_outbox_metrics(self):
        """Update outbox metrics"""
        current_time = datetime.utcnow()
        
        # Count events by status
        status_counts = defaultdict(int)
        total_processing_time = 0
        
        # Count events in last minute for throughput calculation
        recent_events = [m for m in self.event_history 
                         if (current_time - m.timestamp).total_seconds() < 60]
        
        for metric in self.event_history:
            status_counts[metric.status] += 1
            total_processing_time += metric.processing_time_ms
        
        total_events = sum(status_counts.values())
        
        # Calculate averages
        avg_processing_time = (total_processing_time / total_events 
                              if total_events > 0 else 0.0)
        
        # Calculate throughput (events per second in last minute)
        throughput = len(recent_events) / 60.0 if recent_events else 0.0
        
        # Find oldest pending event age
        pending_events = [m for m in self.event_history if m.status == "pending"]
        oldest_age = 0.0
        if pending_events:
            oldest_event = min(pending_events, key=lambda x: x.timestamp)
            oldest_age = (current_time - oldest_event.timestamp).total_seconds()
        
        self.outbox_metrics = OutboxMetrics(
            total_events=total_events,
            pending_events=status_counts.get("pending", 0),
            published_events=status_counts.get("published", 0),
            failed_events=status_counts.get("failed", 0),
            dlq_events=status_counts.get("dlq", 0),
            avg_processing_time_ms=avg_processing_time,
            oldest_pending_age_seconds=oldest_age,
            throughput_events_per_second=throughput,
            timestamp=current_time
        )
    
    def get_outbox_metrics(self) -> OutboxMetrics:
        """Get current outbox metrics"""
        with self.metrics_lock:
            return self.outbox_metrics
    
    def get_consumer_lag_metrics(self, consumer_group: Optional[str] = None) -> List[ConsumerLagMetrics]:
        """Get consumer lag metrics"""
        with self.metrics_lock:
            if consumer_group:
                # Return metrics for specific consumer group
                results = []
                for key, metrics in self.consumer_lag.items():
                    if key.startswith(f"{consumer_group}:"):
                        results.extend(metrics)
                return results
            else:
                # Return all metrics
                all_metrics = []
                for metrics in self.consumer_lag.values():
                    all_metrics.extend(metrics)
                return all_metrics
    
    def get_throughput_metrics(self) -> Dict[str, Any]:
        """Get throughput metrics"""
        with self.metrics_lock:
            if not self.recent_throughput:
                return {"current_throughput": 0.0, "avg_throughput": 0.0}
            
            current_throughput = self.recent_throughput[-1] if self.recent_throughput else 0.0
            avg_throughput = sum(self.recent_throughput) / len(self.recent_throughput)
            
            return {
                "current_throughput": current_throughput,
                "avg_throughput": avg_throughput,
                "peak_throughput": max(self.recent_throughput),
                "min_throughput": min(self.recent_throughput)
            }
    
    def get_processing_time_metrics(self) -> Dict[str, Any]:
        """Get processing time metrics"""
        with self.metrics_lock:
            if not self.recent_processing_times:
                return {"avg_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}
            
            sorted_times = sorted(self.recent_processing_times)
            count = len(sorted_times)
            
            return {
                "avg_ms": sum(sorted_times) / count,
                "p50_ms": sorted_times[int(count * 0.5)],
                "p95_ms": sorted_times[int(count * 0.95)],
                "p99_ms": sorted_times[int(count * 0.99)],
                "max_ms": max(sorted_times),
                "min_ms": min(sorted_times)
            }
    
    def cleanup_old_metrics(self):
        """Clean up old metrics to prevent memory leaks"""
        current_time = time.time()
        
        if current_time - self.last_cleanup > self.cleanup_interval:
            with self.metrics_lock:
                # Clean up old consumer lag metrics
                for key in list(self.consumer_lag.keys()):
                    # Keep only metrics from last hour
                    cutoff_time = datetime.utcnow() - timedelta(hours=1)
                    self.consumer_lag[key] = [
                        m for m in self.consumer_lag[key] 
                        if m.timestamp > cutoff_time
                    ]
                    
                    # Remove empty lists
                    if not self.consumer_lag[key]:
                        del self.consumer_lag[key]
            
            self.last_cleanup = current_time
            logger.debug("🧹 Cleaned up old metrics")

# Global metrics collector
event_metrics_collector = EventMetricsCollector()
