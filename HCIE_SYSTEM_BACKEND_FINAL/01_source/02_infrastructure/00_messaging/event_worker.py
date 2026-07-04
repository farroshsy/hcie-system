"""
HCIE Event Worker
Background worker that processes Kafka events
"""

import logging
import time
import threading
from typing import Dict, Any
from datetime import datetime

from .consumer.kafka_consumer import HCIEKafkaConsumer, EventType
from .producer.kafka_producer import get_kafka_producer
from storage.redis_store.redis_store import create_redis_feature_store
from config.env import settings

logger = logging.getLogger(__name__)

class HCIEEventWorker:
    """
    Background worker that processes HCIE events from Kafka
    Handles analytics, monitoring, and async processing
    """
    
    def __init__(self):
        self.consumer = None
        self.producer = None
        self.redis_store = None
        self.running = False
        self.worker_thread = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize Kafka consumer, producer, and Redis store"""
        try:
            # Initialize consumer
            self.consumer = HCIEKafkaConsumer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                topic_prefix=settings.kafka_topic_prefix,
                group_id=settings.kafka_consumer_group,
                auto_offset_reset=settings.kafka_auto_offset_reset
            )
            
            # Initialize producer
            self.producer = get_kafka_producer()
            
            # Initialize Redis store
            self.redis_store = create_redis_feature_store(settings.redis_host)
            
            # Register event handlers
            self._register_event_handlers()
            
            logger.info("Event worker components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize event worker: {e}")
    
    def _register_event_handlers(self):
        """Register handlers for different event types"""
        # Task event handlers
        self.consumer.register_task_handler(self._handle_task_event)
        
        # Mastery event handlers
        self.consumer.register_mastery_handler(self._handle_mastery_event)
        
        # System event handlers
        self.consumer.register_system_handler(self._handle_system_event)
    
    def _handle_task_event(self, event_data: Dict[str, Any]):
        """Handle task-related events"""
        event_type = event_data.get('event_type')
        user_id = event_data.get('user_id')
        
        if event_type == EventType.TASK_GENERATED:
            self._process_task_generated(event_data)
        elif event_type == EventType.TASK_SUBMITTED:
            self._process_task_submitted(event_data)
    
    def _process_task_generated(self, event_data: Dict[str, Any]):
        """Process task generated event"""
        user_id = event_data.get('user_id')
        concept_id = event_data.get('concept_id')
        difficulty = event_data.get('difficulty')
        policy_mode = event_data.get('policy_mode')
        
        logger.info(f"Task generated for user {user_id}: {concept_id} (difficulty: {difficulty})")
        
        # Store in Redis for analytics
        if self.redis_store and self.redis_store.redis_available:
            try:
                # Store task generation analytics
                analytics_key = f"analytics:task_generation:{datetime.utcnow().strftime('%Y-%m-%d')}"
                self.redis_store.redis_client.hincrby(analytics_key, "tasks_generated", 1)
                self.redis_store.redis_client.hincrby(analytics_key, f"policy:{policy_mode}", 1)
                self.redis_store.redis_client.hincrby(analytics_key, f"concept:{concept_id}", 1)
                self.redis_store.redis_client.expire(analytics_key, 86400)  # 24 hours
            except Exception as e:
                logger.error(f"Error storing task analytics: {e}")
    
    def _process_task_submitted(self, event_data: Dict[str, Any]):
        """Process task submitted event"""
        user_id = event_data.get('user_id')
        concept_id = event_data.get('concept_id')
        correct = event_data.get('correct')
        response_time = event_data.get('response_time')
        reward = event_data.get('reward')
        
        logger.info(f"Task submitted by user {user_id}: {concept_id} (correct: {correct}, reward: {reward})")
        
        # Store in Redis for analytics
        if self.redis_store and self.redis_store.redis_available:
            try:
                # Store submission analytics
                analytics_key = f"analytics:task_submissions:{datetime.utcnow().strftime('%Y-%m-%d')}"
                self.redis_store.redis_client.hincrby(analytics_key, "submissions", 1)
                self.redis_store.redis_client.hincrby(analytics_key, "correct" if correct else "incorrect", 1)
                self.redis_store.redis_client.expire(analytics_key, 86400)
                
                # Store user session data
                session_key = f"session:{user_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
                self.redis_store.redis_client.hincrby(session_key, "interactions", 1)
                self.redis_store.redis_client.hincrbyfloat(session_key, "total_response_time", response_time)
                self.redis_store.redis_client.hincrbyfloat(session_key, "total_reward", reward)
                self.redis_store.redis_client.expire(session_key, 86400)
                
            except Exception as e:
                logger.error(f"Error storing submission analytics: {e}")
    
    def _handle_mastery_event(self, event_data: Dict[str, Any]):
        """Handle mastery-related events"""
        user_id = event_data.get('user_id')
        concept_id = event_data.get('concept_id')
        mastery_change = event_data.get('mastery_change')
        new_mastery = event_data.get('new_mastery')
        
        logger.info(f"Mastery updated for user {user_id}: {concept_id} (change: {mastery_change}, new: {new_mastery})")
        
        # Store mastery analytics
        if self.redis_store and self.redis_store.redis_available:
            try:
                analytics_key = f"analytics:mastery_updates:{datetime.utcnow().strftime('%Y-%m-%d')}"
                self.redis_store.redis_client.hincrby(analytics_key, "updates", 1)
                self.redis_store.redis_client.hincrbyfloat(analytics_key, "total_mastery_change", mastery_change)
                self.redis_store.redis_client.expire(analytics_key, 86400)
                
                # NOTE: Event worker does NOT update mastery state - only analytics
                
            except Exception as e:
                logger.error(f"Error storing mastery analytics: {e}")
    
    def _handle_system_event(self, event_data: Dict[str, Any]):
        """Handle system-related events"""
        event_type = event_data.get('event_type')
        service_name = event_data.get('service_name')
        status = event_data.get('status')
        
        if event_type == EventType.SYSTEM_HEALTH_CHECK:
            logger.info(f"Health check for {service_name}: {status}")
            
            # Store health metrics
            if self.redis_store and self.redis_store.redis_available:
                try:
                    health_key = f"health:{service_name}:{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
                    self.redis_store.redis_client.hset(health_key, "status", status)
                    self.redis_store.redis_client.hset(health_key, "timestamp", datetime.utcnow().isoformat())
                    self.redis_store.redis_client.expire(health_key, 3600)  # 1 hour
                    
                except Exception as e:
                    logger.error(f"Error storing health metrics: {e}")
    
    def start(self):
        """Start the event worker"""
        if self.running:
            logger.warning("Event worker is already running")
            return
        
        if not self.consumer:
            logger.error("Cannot start event worker - consumer not initialized")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self.worker_thread.start()
        logger.info("Event worker started")
    
    def _run_worker(self):
        """Run the worker thread"""
        logger.info("Event worker thread started")
        
        while self.running:
            try:
                self.consumer.consume_messages(timeout_ms=1000, max_messages=50)
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                logger.error(f"Error in event worker: {e}")
                time.sleep(1)  # Wait before retrying
        
        logger.info("Event worker thread stopped")
    
    def stop(self):
        """Stop the event worker"""
        if not self.running:
            logger.warning("Event worker is not running")
            return
        
        self.running = False
        
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        
        self.close()
        logger.info("Event worker stopped")
    
    def close(self):
        """Close all components"""
        if self.consumer:
            self.consumer.close()
        
        if self.producer:
            self.producer.close()
        
        logger.info("Event worker components closed")

# Global worker instance
_worker_instance: HCIEEventWorker = None

def get_event_worker() -> HCIEEventWorker:
    """Get global event worker instance"""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = HCIEEventWorker()
    return _worker_instance

def start_event_worker():
    """Start the global event worker"""
    worker = get_event_worker()
    worker.start()
    return worker

def stop_event_worker():
    """Stop the global event worker"""
    global _worker_instance
    if _worker_instance:
        _worker_instance.stop()
        _worker_instance = None
