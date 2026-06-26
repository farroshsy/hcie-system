"""
Kafka Analytics Worker
Consumes LearningProcessed events from learning_analytics topic and performs analytics, stores to PostgreSQL
"""

import logging
import time
import threading
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from storage.postgres_store.interaction_store import get_postgres_interaction_store

# Import configuration
try:
    from config.env import settings
except ImportError:
    settings = None

logger = logging.getLogger(__name__)

class AnalyticsWorker:
    """Kafka worker for analytics and data processing"""
    
    def __init__(self):
        self.consumer = None
        self.postgres_store = get_postgres_interaction_store()
        self.running = False
        self.thread = None
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="analytics")
    
    def start(self):
        """Start the analytics worker"""
        if self.running:
            logger.warning("Analytics worker already running")
            return
        
        try:
            # Use KafkaFactory for consistent consumer creation
            if settings:
                from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
                kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
                
                self.consumer = kafka_factory.create_consumer(
                    group_id='analytics_group',
                    topics=['learning_analytics']
                )
            else:
                # Fallback for testing without settings
                from messaging import HCIEKafkaConsumer
                self.consumer = HCIEKafkaConsumer(
                    bootstrap_servers='kafka:9092',
                    group_id='analytics_group',
                    auto_offset_reset='latest',
                    topics=['learning_analytics']
                )
            
            self.running = True
            self.thread = threading.Thread(target=self._run_worker, daemon=True)
            self.thread.start()
            logger.info("Analytics worker started on topic: learning_analytics")
        except Exception as e:
            logger.error(f"Failed to start analytics worker: {e}")
    
    def stop(self):
        """Stop the analytics worker"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        if self.consumer:
            self.consumer.close()
        self.executor.shutdown(wait=True)
        logger.info("Analytics worker stopped")
    
    def _run_worker(self):
        """Main worker loop"""
        logger.info("Analytics worker loop started")
        
        try:
            while self.running:
                if self.consumer:
                    # Process messages with timeout
                    for message in self.consumer:
                        if not self.running:
                            break
                        self._process_message(message)
                time.sleep(0.1)  # Small delay to prevent busy waiting
        except Exception as e:
            logger.error(f"Analytics worker error: {e}")
        finally:
            logger.info("Analytics worker loop ended")
    
    def _process_message(self, message):
        """Process a single Kafka message"""
        try:
            event_data = message.value
            event_type = event_data.get("event_type")
            
            # Only process LearningProcessed events
            if event_type == "LearningProcessed":
                self._handle_learning_processed(event_data)
            elif event_type == "CognitionUpdated":
                self._handle_cognition_updated(event_data)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _handle_learning_processed(self, event_data: Dict[str, Any]):
        """Handle LearningProcessed event"""
        logger.info("🔬 ANALYTICS: Processing LearningProcessed event for analytics")
        try:
            # Submit to thread pool for async processing
            self.executor.submit(self._process_learning_processed, event_data)
        except Exception as e:
            logger.error(f"Error handling LearningProcessed event: {e}")
    
    def _handle_cognition_updated(self, event_data: Dict[str, Any]):
        """Handle CognitionUpdated event"""
        try:
            # Submit to thread pool for async processing
            self.executor.submit(self._process_cognition_updated, event_data)
        except Exception as e:
            logger.error(f"Error handling CognitionUpdated event: {e}")
    
    def _process_learning_processed(self, event_data: Dict[str, Any]):
        """Process LearningProcessed event asynchronously"""
        try:
            logger.debug(f"Processing LearningProcessed event for user {event_data.get('user_id')}")
            
            # Extract Tier A cognitive signals from LearningProcessed event
            result = event_data.get("result", {})
            
            analytics_data = {
                "event_type": "learning_processed",
                "user_id": event_data.get('user_id'),
                "concept_id": event_data.get('concept_id'),
                "original_event_id": event_data.get('original_event_id'),
                
                # Tier A cognitive signals
                "mastery": result.get('mastery'),
                "mastery_before": result.get('mastery_before'),
                "uncertainty": result.get('uncertainty'),
                "zpd_score": result.get('zpd_score'),
                "confidence": result.get('confidence'),
                
                # Multi-learner signals
                "lyapunov_mastery": result.get('lyapunov_mastery'),
                "bayesian_alpha": result.get('bayesian_alpha'),
                "bayesian_beta": result.get('bayesian_beta'),
                "kalman_mastery": result.get('kalman_mastery'),
                "kalman_covariance": result.get('kalman_covariance'),
                
                # Policy signals
                "selected_concept": result.get('selected_concept'),
                "is_exploration": result.get('is_exploration'),
                "processing_mode": result.get('processing_mode'),
                
                # Metadata
                "timestamp": event_data.get('timestamp'),
                "causation_id": event_data.get('causation_id'),
                "correlation_id": event_data.get('correlation_id'),
                "processing_time": time.time()
            }
            
            # Store analytics data
            self._store_analytics(analytics_data)
            
        except Exception as e:
            logger.error(f"Error processing LearningProcessed: {e}")
    
    def _process_cognition_updated(self, event_data: Dict[str, Any]):
        """Process CognitionUpdated event asynchronously"""
        try:
            logger.debug(f"Processing CognitionUpdated event for user {event_data.get('user_id')}")
            
            # Extract cognitive state from CognitionUpdated event
            result = event_data.get("result", {})
            
            analytics_data = {
                "event_type": "cognition_updated",
                "user_id": event_data.get('user_id'),
                "concept_id": event_data.get('concept_id'),
                
                # Canonical cognitive state
                "mastery": result.get('mastery'),
                "uncertainty": result.get('uncertainty'),
                "zpd_score": result.get('zpd_score'),
                "confidence": result.get('confidence'),
                
                # Multi-learner state
                "lyapunov_mastery": result.get('lyapunov_mastery'),
                "bayesian_alpha": result.get('bayesian_alpha'),
                "bayesian_beta": result.get('bayesian_beta'),
                "kalman_mastery": result.get('kalman_mastery'),
                "kalman_covariance": result.get('kalman_covariance'),
                
                # Experiment lineage
                "experiment_id": event_data.get('experiment_id'),
                "policy_version": event_data.get('policy_version'),
                "cohort_id": event_data.get('cohort_id'),
                "assignment_hash": event_data.get('assignment_hash'),
                
                # Metadata
                "timestamp": event_data.get('timestamp'),
                "causation_id": event_data.get('causation_id'),
                "correlation_id": event_data.get('correlation_id'),
                "processing_time": time.time()
            }
            
            # Store analytics data
            self._store_analytics(analytics_data)
            
        except Exception as e:
            logger.error(f"Error processing CognitionUpdated: {e}")
    
    def _store_analytics(self, analytics_data: Dict[str, Any]):
        """Store analytics data to PostgreSQL"""
        try:
            event_type = analytics_data.get('event_type')
            user_id = analytics_data.get('user_id')
            
            logger.info(f"Analytics stored: {event_type} for user {user_id}")
            
            # NOTE: This worker intentionally does NOT write the `interactions`
            # table. It consumes cognitive-OUTPUT events (LearningProcessed /
            # CognitionUpdated), whose payload carries mastery / Bayesian / Kalman
            # signals but NOT the raw interaction fields (representation, correct,
            # difficulty). The prior implementation inserted a placeholder row with
            # representation='unknown', correct=None, difficulty=None — which:
            #   (1) silently failed the NOT NULL `difficulty` constraint on EVERY
            #       event (so this path never populated the table at all), and
            #   (2) is now redundant and would be HARMFUL: the canonical writer is
            #       ItsRuntimeService.submit_attempt, which records the REAL
            #       (representation, correct, difficulty, response_time) synchronously
            #       per attempt. A second writer here would DUPLICATE those rows and
            #       double-count in state reconstruction (bandit α/β + interaction_count).
            # The rich cognitive signals in `analytics_data` are not yet persisted by a
            # dedicated sink (interactions has no mastery/Bayesian/Kalman columns); a
            # future analytics table is the right home for them, not `interactions`.
            if event_type == 'learning_processed':
                logger.debug(
                    "analytics_worker: cognitive event observed for user %s; "
                    "interactions write delegated to ItsRuntimeService.submit_attempt",
                    user_id,
                )

            # Could implement additional analytics here:
            # - Learning curves (mastery over time)
            # - Drift detection (uncertainty spikes)
            # - User clustering (based on learning patterns)
            # - Performance metrics (response time, accuracy)
            # - Tier A signal aggregation for experiment analysis
            
        except Exception as e:
            logger.error(f"Error storing analytics: {e}")
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        return {
            "running": self.running,
            "thread_alive": self.thread.is_alive() if self.thread else False,
            "consumer_connected": self.consumer is not None,
            "postgres_available": self.postgres_store is not None
        }

# Global instance
_analytics_worker: Optional[AnalyticsWorker] = None

def get_analytics_worker() -> AnalyticsWorker:
    """Get global analytics worker instance"""
    global _analytics_worker
    if _analytics_worker is None:
        _analytics_worker = AnalyticsWorker()
    return _analytics_worker

def start_analytics_worker():
    """Start the global analytics worker"""
    worker = get_analytics_worker()
    worker.start()
    return worker

def stop_analytics_worker():
    """Stop the global analytics worker"""
    worker = get_analytics_worker()
    worker.stop()
