"""
Kafka Event Consumer for HCIE System
Handles consuming events from Kafka topics
"""

import json
import time
import logging
from datetime import datetime
from typing import Callable, Dict, Any, Optional, List
from kafka import KafkaConsumer

from ..schema.events import BaseEvent, EventType

logger = logging.getLogger(__name__)

class HCIEKafkaConsumer:
    """
    Kafka consumer for HCIE system events
    Consumes events from multiple topics
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092",
                 topic_prefix: str = "hcie",
                 group_id: str = "hcie-consumer",
                 auto_offset_reset: str = "earliest",
                 topics: Optional[List[str]] = None):
        """
        Initialize HCIE Kafka consumer
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic_prefix: Prefix for default HCIE topics (ignored if topics provided)
            group_id: Consumer group ID
            auto_offset_reset: Auto offset reset policy
            topics: Optional list of topics to subscribe to (overrides default HCIE topics)
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic_prefix = topic_prefix
        self.group_id = group_id
        self.auto_offset_reset = auto_offset_reset
        self.consumer = None
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.custom_topics = topics
        self._running = False
        self._closed = False
        # reconnect/backoff state — prevents a tight error-spam loop when the broker is
        # briefly unavailable at startup (the old code init'd once, set consumer=None on
        # failure, never retried, and logged on every poll -> 100k+ "Cannot poll" lines).
        self._reconnect_backoff = 5.0   # seconds, grows to a cap on repeated failure
        self._last_reconnect = 0.0
        self._last_poll_warn = 0.0
        self._initialize_consumer()
    
    def _initialize_consumer(self):
        """Initialize Kafka consumer"""
        try:
            # Use custom topics if provided, otherwise use default HCIE topics
            if self.custom_topics:
                topics = self.custom_topics
                logger.info(f"Using custom topics: {topics}")
            else:
                # Subscribe to all HCIE topics
                topics = [
                    f"{self.topic_prefix}.tasks",
                    f"{self.topic_prefix}.submissions", 
                    f"{self.topic_prefix}.mastery",
                    f"{self.topic_prefix}.policies",
                    f"{self.topic_prefix}.rewards",
                    f"{self.topic_prefix}.sessions",
                    f"{self.topic_prefix}.health",
                    f"{self.topic_prefix}.auth",  # Auth events
                    f"{self.topic_prefix}.events"
                ]
                logger.info(f"Using default HCIE topics with prefix '{self.topic_prefix}'")
            
            self.consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset=self.auto_offset_reset,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: m.decode('utf-8') if m else None,
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                # 🔥 FIX REBALANCE LOOP: Increase timeouts to prevent heartbeat failures during initialization
                session_timeout_ms=30000,  # 30 seconds (default is 10 seconds)
                heartbeat_interval_ms=10000,  # 10 seconds (default is 3 seconds)
                max_poll_interval_ms=300000,  # 5 minutes (default is 5 minutes)
                max_poll_records=500  # Process up to 500 records per poll
            )
            
            self.consumer.subscribe(topics)
            logger.info(f"Kafka consumer initialized for topics: {topics}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            self.consumer = None
    
    def subscribe(self, topics):
        """
        Subscribe to specific topics (expose underlying consumer method)
        
        Args:
            topics: List of topic names to subscribe to
        """
        if self.consumer:
            self.consumer.subscribe(topics)
            logger.info(f"Subscribed to topics: {topics}")
        else:
            logger.error("Cannot subscribe: consumer not initialized")
    
    def _ensure_consumer(self) -> bool:
        """Re-initialize the underlying consumer if it is down, throttled by backoff.

        Returns True if a live consumer is available. On repeated failure the backoff
        grows (capped at 60s) so we neither hot-spin nor flood the logs.
        """
        if self.consumer is not None:
            return True
        if self._closed:
            return False
        now = time.monotonic()
        if now - self._last_reconnect < self._reconnect_backoff:
            return False
        self._last_reconnect = now
        self._initialize_consumer()
        if self.consumer is None:
            self._reconnect_backoff = min(self._reconnect_backoff * 2, 60.0)
            return False
        self._reconnect_backoff = 5.0  # recovered — reset backoff
        logger.info("Kafka consumer re-initialized after prior failure")
        return True

    def poll(self, timeout_ms=None, max_records=None):
        """
        Poll for messages (expose underlying consumer method)

        Args:
            timeout_ms: Timeout in milliseconds (None for default)
            max_records: Maximum number of records to return (None for unlimited)

        Returns:
            Dictionary of TopicPartition to list of ConsumerRecord
        """
        if self._ensure_consumer():
            return self.consumer.poll(timeout_ms=timeout_ms, max_records=max_records)
        # Not initialized: log at most once per 60s (was: every call -> log flood) and
        # sleep for the backoff so a caller without its own sleep doesn't hot-spin.
        now = time.monotonic()
        if now - self._last_poll_warn > 60:
            logger.warning("Kafka consumer not initialized; retrying with backoff")
            self._last_poll_warn = now
        time.sleep(min(self._reconnect_backoff, 5.0))
        return {}

    def __iter__(self):
        """Resilient iteration for workers that do `for message in consumer:`.

        Ensures the underlying consumer is up (with backoff) before yielding, and
        re-initializes instead of raising `TypeError: NoneType is not iterable` when
        init failed at startup.
        """
        while not self._closed:
            if not self._ensure_consumer():
                time.sleep(min(self._reconnect_backoff, 5.0))
                continue
            try:
                for message in self.consumer:
                    yield message
            except Exception as e:
                logger.error(f"Consumer iteration error, will re-initialize: {e}")
                self.consumer = None
                time.sleep(min(self._reconnect_backoff, 5.0))
    
    def register_handler(self, event_type: EventType, handler: Callable[[Dict[str, Any]], None]):
        """
        Register a handler for specific event type
        
        Args:
            event_type: Event type to handle
            handler: Handler function that receives event data
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type}")
    
    def register_task_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Register handler for task events"""
        self.register_handler(EventType.TASK_GENERATED, handler)
        self.register_handler(EventType.TASK_SUBMITTED, handler)
    
    def register_mastery_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Register handler for mastery events"""
        self.register_handler(EventType.MASTERY_UPDATED, handler)
    
    def register_system_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Register handler for system events"""
        self.register_handler(EventType.SYSTEM_HEALTH_CHECK, handler)
    
    def _handle_event(self, event_data: Dict[str, Any]):
        """Handle incoming event"""
        try:
            event_type = event_data.get('event_type')
            if not event_type:
                logger.warning(f"Event missing event_type: {event_data}")
                return
            
            # Convert string to EventType enum
            try:
                event_type = EventType(event_type)
            except ValueError:
                logger.warning(f"Unknown event type: {event_type}")
                return
            
            # Get handlers for this event type
            handlers = self.event_handlers.get(event_type, [])
            if not handlers:
                logger.debug(f"No handlers registered for {event_type}")
                return
            
            # Call all handlers
            for handler in handlers:
                try:
                    handler(event_data)
                except Exception as e:
                    logger.error(f"Handler error for {event_type}: {e}")
                    
        except Exception as e:
            logger.error(f"Error handling event: {e}")
    
    def consume_messages(self, timeout_ms: int = 1000, max_messages: int = 10):
        """
        Consume messages from Kafka
        
        Args:
            timeout_ms: Timeout in milliseconds
            max_messages: Maximum messages to consume
        """
        if not self.consumer:
            logger.warning("Kafka consumer not available")
            return
        
        try:
            message_count = 0
            for message in self.consumer:
                if message_count >= max_messages:
                    break
                
                logger.debug(f"Received message from {message.topic} [{message.partition}:{message.offset}]")
                self._handle_event(message.value)
                message_count += 1
                
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
    
    def start_consuming(self, timeout_ms: int = 1000):
        """
        Start continuous message consumption
        This is a blocking call
        """
        if not self.consumer:
            logger.error("Cannot start consuming - consumer not initialized")
            return
        
        self._running = True
        logger.info("Starting continuous Kafka consumption...")
        try:
            while self._running:
                self.consume_messages(timeout_ms=timeout_ms)
        except KeyboardInterrupt:
            logger.info("Consumption stopped by user")
        except Exception as e:
            logger.error(f"Error in continuous consumption: {e}")
        finally:
            self.close()
    
    def stop(self):
        """Stop the consumer"""
        self._running = False
        self.close()
    
    def is_running(self):
        """Check if consumer is running"""
        return self._running
    
    def close(self):
        """Close the consumer"""
        self._running = False
        self._closed = True
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")

# Event handler decorators
def task_event_handler(event_type: EventType):
    """Decorator for task event handlers"""
    def decorator(func):
        def wrapper(event_data):
            func(event_data)
        return wrapper
    return decorator

def mastery_event_handler(event_type: EventType):
    """Decorator for mastery event handlers"""
    def decorator(func):
        def wrapper(event_data):
            func(event_data)
        return wrapper
    return decorator

def system_event_handler(event_type: EventType):
    """Decorator for system event handlers"""
    def decorator(func):
        def wrapper(event_data):
            func(event_data)
        return wrapper
    return decorator
