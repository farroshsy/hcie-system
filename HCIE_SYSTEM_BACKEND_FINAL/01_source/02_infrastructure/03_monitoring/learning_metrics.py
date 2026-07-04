#!/usr/bin/env python3
"""
Prometheus Metrics for Learning System
Tracks events processed, failures, and DLQ usage
"""

import time
import logging
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from threading import Lock

logger = logging.getLogger(__name__)

class LearningMetrics:
    """
    Centralized metrics collection for the learning system
    """
    
    def __init__(self, metrics_port: int = 8002):
        self.metrics_port = metrics_port
        self._lock = Lock()
        
        # Event processing metrics
        self.events_processed_total = Counter(
            'learning_events_processed_total',
            'Total number of learning events processed',
            ['event_type', 'concept']
        )
        
        self.events_failed_total = Counter(
            'learning_events_failed_total',
            'Total number of learning events that failed',
            ['failure_type', 'event_type']
        )
        
        self.events_dlq_total = Counter(
            'learning_events_dlq_total',
            'Total number of events sent to DLQ',
            ['error_reason', 'event_type']
        )
        
        # Performance metrics
        self.event_processing_duration = Histogram(
            'learning_event_processing_seconds',
            'Time spent processing learning events',
            ['event_type']
        )
        
        self.db_transaction_duration = Histogram(
            'learning_db_transaction_seconds',
            'Time spent in database transactions'
        )
        
        # System metrics
        self.active_connections = Gauge(
            'learning_active_connections',
            'Number of active database connections'
        )
        
        self.consumer_lag = Gauge(
            'learning_consumer_lag',
            'Consumer lag in messages',
            ['partition']
        )
        
        self.learning_state_size = Gauge(
            'learning_state_size_bytes',
            'Size of learning state in bytes',
            ['user_id']
        )
        
        # Learning component metrics
        self.mastery_updates = Counter(
            'learning_mastery_updates_total',
            'Total number of mastery updates',
            ['concept']
        )
        
        self.transfer_applications = Counter(
            'learning_transfer_applications_total',
            'Total number of transfer applications',
            ['source_concept', 'target_concept']
        )
        
        self.bandit_decisions = Counter(
            'learning_bandit_decisions_total',
            'Total number of bandit decisions',
            ['action', 'exploration']
        )
        
    def start_metrics_server(self):
        """Start the Prometheus metrics HTTP server"""
        try:
            start_http_server(self.metrics_port)
            logger.info(f"✅ Prometheus metrics server started on port {self.metrics_port}")
        except Exception as e:
            logger.error(f"❌ Failed to start metrics server: {e}")
    
    def record_event_processed(self, event_type: str, concept: str, processing_time: float):
        """Record a successfully processed event"""
        with self._lock:
            self.events_processed_total.labels(event_type=event_type, concept=concept).inc()
            self.event_processing_duration.labels(event_type=event_type).observe(processing_time)
    
    def record_event_failed(self, failure_type: str, event_type: str):
        """Record a failed event"""
        with self._lock:
            self.events_failed_total.labels(failure_type=failure_type, event_type=event_type).inc()
    
    def record_dlq_event(self, error_reason: str, event_type: str):
        """Record an event sent to DLQ"""
        with self._lock:
            self.events_dlq_total.labels(error_reason=error_reason, event_type=event_type).inc()
    
    def record_db_transaction(self, duration: float):
        """Record database transaction duration"""
        with self._lock:
            self.db_transaction_duration.observe(duration)
    
    def update_active_connections(self, count: int):
        """Update active connections count"""
        with self._lock:
            self.active_connections.set(count)
    
    def update_consumer_lag(self, partition: int, lag: int):
        """Update consumer lag"""
        with self._lock:
            self.consumer_lag.labels(partition=str(partition)).set(lag)
    
    def update_learning_state_size(self, user_id: str, size_bytes: int):
        """Update learning state size"""
        with self._lock:
            self.learning_state_size.labels(user_id=user_id).set(size_bytes)
    
    def record_mastery_update(self, concept: str):
        """Record mastery update"""
        with self._lock:
            self.mastery_updates.labels(concept=concept).inc()
    
    def record_transfer_application(self, source_concept: str, target_concept: str):
        """Record transfer application"""
        with self._lock:
            self.transfer_applications.labels(source_concept=source_concept, target_concept=target_concept).inc()
    
    def record_bandit_decision(self, action: str, exploration: bool):
        """Record bandit decision"""
        with self._lock:
            exploration_str = "true" if exploration else "false"
            self.bandit_decisions.labels(action=action, exploration=exploration_str).inc()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics"""
        try:
            # This would typically be scraped by Prometheus, but we provide a summary for debugging
            return {
                "events_processed": self.events_processed_total._value.get(),
                "events_failed": self.events_failed_total._value.get(),
                "events_dlq": self.events_dlq_total._value.get(),
                "active_connections": self.active_connections._value.get(),
                "last_updated": time.time()
            }
        except Exception as e:
            logger.error(f"❌ Failed to get metrics summary: {e}")
            return {}

# Global metrics instance
_metrics = None

def get_metrics() -> LearningMetrics:
    """Get global metrics instance (singleton)"""
    global _metrics
    if _metrics is None:
        _metrics = LearningMetrics()
    return _metrics

def record_event_processed(event_type: str, concept: str, processing_time: float):
    """Convenience function for recording processed events"""
    get_metrics().record_event_processed(event_type, concept, processing_time)

def record_event_failed(failure_type: str, event_type: str):
    """Convenience function for recording failed events"""
    get_metrics().record_event_failed(failure_type, event_type)

def record_dlq_event(error_reason: str, event_type: str):
    """Convenience function for recording DLQ events"""
    get_metrics().record_dlq_event(error_reason, event_type)

def record_learning_components(learner_result: Dict[str, Any], transfer_result: Dict[str, Any], bandit_result: Dict[str, Any]):
    """Record learning component metrics"""
    metrics = get_metrics()
    
    # Record mastery update
    if 'concept' in learner_result:
        metrics.record_mastery_update(learner_result['concept'])
    
    # Record transfer application
    if transfer_result.get('applied'):
        source = transfer_result.get('concept', 'unknown')
        target = learner_result.get('concept', 'unknown')
        metrics.record_transfer_application(source, target)
    
    # Record bandit decision
    if 'action' in bandit_result:
        exploration = bandit_result.get('exploration', False)
        metrics.record_bandit_decision(bandit_result['action'], exploration)
