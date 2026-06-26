"""
Kafka Event Producer for HCIE System
Handles publishing events to Kafka topics
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError

from ..schema.events import BaseEvent, EventType

logger = logging.getLogger(__name__)

class HCIEKafkaProducer:
    """
    Kafka producer for HCIE system events
    Publishes events to appropriate topics based on event type
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092", 
                 topic_prefix: str = "hcie",
                 client_id: str = "hcie-producer"):
        self.bootstrap_servers = bootstrap_servers
        self.topic_prefix = topic_prefix
        self.client_id = client_id
        self.producer = None
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                retry_backoff_ms=100,
                request_timeout_ms=30000
            )
            logger.info(f"Kafka producer initialized for {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None
    
    def get_topic_name(self, event_type: EventType) -> str:
        """Get topic name for event type"""
        topic_mapping = {
            EventType.TASK_GENERATED: f"{self.topic_prefix}.tasks",
            EventType.TASK_SUBMITTED: f"{self.topic_prefix}.submissions",
            EventType.MASTERY_UPDATED: f"{self.topic_prefix}.mastery",
            EventType.POLICY_EXECUTED: f"{self.topic_prefix}.policies",
            EventType.REWARD_CALCULATED: f"{self.topic_prefix}.rewards",
            EventType.USER_SESSION_STARTED: f"{self.topic_prefix}.sessions",
            EventType.USER_SESSION_ENDED: f"{self.topic_prefix}.sessions",
            EventType.SYSTEM_HEALTH_CHECK: f"{self.topic_prefix}.health",
            # Auth events
            EventType.USER_REGISTERED: f"{self.topic_prefix}.auth",
            EventType.USER_LOGGED_IN: f"{self.topic_prefix}.auth",
            EventType.TOKEN_REFRESHED: f"{self.topic_prefix}.auth",
            EventType.USER_PROFILE_UPDATED: f"{self.topic_prefix}.auth",
            EventType.USER_LOGGED_OUT: f"{self.topic_prefix}.auth",
            EventType.PASSWORD_CHANGED: f"{self.topic_prefix}.auth"
        }
        return topic_mapping.get(event_type, f"{self.topic_prefix}.events")
    
    def publish_event(self, event: BaseEvent, key: Optional[str] = None) -> bool:
        """
        Publish an event to Kafka
        
        Args:
            event: Event to publish
            key: Partition key (optional)
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.producer:
            logger.warning("Kafka producer not available, event not published")
            return False
        
        try:
            # Generate event ID if not provided
            if not hasattr(event, 'event_id') or not event.event_id:
                event.event_id = str(uuid.uuid4())
            
            # Set timestamp if not provided
            if not hasattr(event, 'timestamp') or not event.timestamp:
                event.timestamp = datetime.utcnow()
            
            # Convert to dict and publish
            topic = self.get_topic_name(event.event_type)
            event_dict = event.dict()
            
            # Use user_id as key for user-related events
            partition_key = key or (event.user_id if event.user_id else None)
            
            # Send to Kafka
            future = self.producer.send(
                topic=topic,
                value=event_dict,
                key=partition_key
            )
            
            # Get record metadata
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Event published to {topic} [{record_metadata.partition}:{record_metadata.offset}]")
            return True
            
        except KafkaError as e:
            logger.error(f"Kafka error publishing event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            return False
    
    def publish_event_direct(self, topic: str, event_type: str, payload: Dict[str, Any], key: Optional[str] = None) -> bool:
        """
        Publish an event directly to Kafka with explicit topic and payload
        
        Args:
            topic: Kafka topic to publish to
            event_type: Type of event
            payload: Event payload data
            key: Optional partition key
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False
        
        try:
            # Publish payload directly (consumer expects unwrapped data)
            future = self.producer.send(
                topic=topic,
                value=payload,
                key=key
            )
            
            # Wait for acknowledgment
            record_metadata = future.get(timeout=10)
            
            logger.debug(f"Event published to {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing event directly: {e}")
            return False
    
    def publish_task_generated(self, user_id: str, task_id: str, concept_id: str,
                             representation: str, difficulty: float, policy_mode: str,
                             selection_metrics: Dict[str, Any], processing_time_ms: float) -> bool:
        """Publish task generated event"""
        from ..schema.events import TaskGeneratedEvent
        
        event = TaskGeneratedEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.TASK_GENERATED,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            source="hcie-engine",
            task_id=task_id,
            concept_id=concept_id,
            representation=representation,
            difficulty=difficulty,
            policy_mode=policy_mode,
            selection_metrics=selection_metrics,
            processing_time_ms=processing_time_ms
        )
        
        return self.publish_event(event, key=user_id)
    
    def publish_task_submitted(self, user_id: str, task_id: str, concept_id: str,
                             representation: str, answer: str, correct_answer: str,
                             correct: bool, response_time: float, difficulty: float,
                             reward: float) -> bool:
        """Publish task submitted event"""
        from ..schema.events import TaskSubmittedEvent
        
        event = TaskSubmittedEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.TASK_SUBMITTED,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            source="hcie-api",
            task_id=task_id,
            concept_id=concept_id,
            representation=representation,
            answer=answer,
            correct_answer=correct_answer,
            correct=correct,
            response_time=response_time,
            difficulty=difficulty,
            reward=reward
        )
        
        return self.publish_event(event, key=user_id)
    
    def publish_mastery_updated(self, user_id: str, concept_id: str, previous_mastery: float,
                               new_mastery: float, mastery_change: float,
                               uncertainty: float, transferred_nodes: int) -> bool:
        """Publish mastery updated event"""
        from ..schema.events import MasteryUpdatedEvent
        
        event = MasteryUpdatedEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MASTERY_UPDATED,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            source="hcie-engine",
            concept_id=concept_id,
            previous_mastery=previous_mastery,
            new_mastery=new_mastery,
            mastery_change=mastery_change,
            uncertainty=uncertainty,
            transferred_nodes=transferred_nodes
        )
        
        return self.publish_event(event, key=user_id)
    
    def publish_system_health(self, service_name: str, status: str, 
                            metrics: Dict[str, Any], checks: Dict[str, bool]) -> bool:
        """Publish system health event"""
        from ..schema.events import SystemHealthCheckEvent
        
        event = SystemHealthCheckEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SYSTEM_HEALTH_CHECK,
            timestamp=datetime.utcnow(),
            source="hcie-api",
            service_name=service_name,
            status=status,
            metrics=metrics,
            checks=checks
        )
        
        return self.publish_event(event, key=service_name)
    
    def close(self):
        """Close the producer"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer closed")

# Global producer instance
_producer_instance: Optional[HCIEKafkaProducer] = None

def get_kafka_producer() -> Optional[HCIEKafkaProducer]:
    """Get global Kafka producer instance"""
    global _producer_instance
    if _producer_instance is None:
        from config.env import settings
        _producer_instance = HCIEKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            topic_prefix=settings.kafka_topic_prefix
        )
    return _producer_instance

def close_kafka_producer():
    """Close global Kafka producer"""
    global _producer_instance
    if _producer_instance:
        _producer_instance.close()
        _producer_instance = None
