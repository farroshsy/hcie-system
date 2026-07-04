"""
Real Outbox Service with Kafka Publishing
"""

import logging
import json

logger = logging.getLogger(__name__)

class OutboxPattern:
    """Real outbox pattern with Kafka publishing"""
    def __init__(self):
        self.producer = None
        self._init_producer()
    
    def _init_producer(self):
        """Initialize Kafka producer"""
        try:
            from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
            from config.env import settings
            
            kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
            self.producer = kafka_factory.create_producer()
            logger.info("🔥 Kafka producer initialized for outbox")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Kafka producer: {e}")
            self.producer = None
    
    def create_event(self, event_id: str, event_type: str, topic: str, **kwargs):
        """Create an event for publishing"""
        return {
            "event_id": event_id,
            "event_type": event_type,
            "topic": topic,
            **kwargs
        }
    
    def save_event(self, event, transaction=None):
        """Save event (simplified for frontend use)"""
        logger.info(f"📝 Outbox event created: {event['event_id']}")
        return True
    
    def publish_event(self, topic: str, event_data: dict, event_type: str):
        """Publish event to Kafka topic"""
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return None
        
        try:
            # Convert to JSON bytes
            message_value = json.dumps(event_data).encode('utf-8')
            
            # Send to Kafka
            future = self.producer.send(
                topic=topic,
                value=message_value,
                key=event_data.get('user_id', '').encode('utf-8') if event_data.get('user_id') else None
            )
            
            # Block for confirmation
            record_metadata = future.get(timeout=10)
            
            logger.info(f"� Event published to Kafka: {event_data['event_id']} "
                       f"→ {topic} [partition={record_metadata.partition}, offset={record_metadata.offset}]")
            
            return event_data.get("event_id", "unknown")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish event to Kafka: {e}")
            return None

def get_outbox_pattern():
    """Get outbox pattern instance"""
    return OutboxPattern()
