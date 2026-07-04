"""
Kafka Factory - Centralized Kafka component creation
Moves construction logic out of main.py
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class KafkaProducerFactory:
    """Factory interface for creating Kafka producers"""
    
    def create_producer(self):
        """Create Kafka producer"""
        raise NotImplementedError("Producer factory must be implemented")

class DefaultKafkaProducerFactory(KafkaProducerFactory):
    """Default implementation of Kafka producer factory"""
    
    def create_producer(self):
        """Create Kafka producer via messaging module"""
        try:
            from messaging import get_kafka_producer
            producer = get_kafka_producer()
            
            if not producer:
                raise RuntimeError("❌ Kafka producer not available")
            
            logger.info("✅ Created Kafka producer via default factory")
            return producer
            
        except ImportError as e:
            logger.error(f"❌ Failed to import messaging module: {e}")
            raise RuntimeError("❌ Messaging module not available")
        except Exception as e:
            logger.error(f"❌ Failed to create Kafka producer: {e}")
            raise

class KafkaFactory:
    """Factory for creating Kafka components with proper configuration"""
    
    def __init__(self, settings, producer_factory: Optional[KafkaProducerFactory] = None):
        """Initialize factory with settings and optional producer factory"""
        self.settings = settings
        self.producer_factory = producer_factory
    
    def create_consumer(self, group_id: str, topics: Optional[list] = None) -> object:
        """
        Create Kafka consumer with proper configuration
        
        Args:
            group_id: Consumer group ID
            topics: Optional list of topics to subscribe to (overrides default HCIE topics)
            
        Returns:
            HCIEKafkaConsumer instance
        """
        try:
            from messaging import HCIEKafkaConsumer
            
            consumer = HCIEKafkaConsumer(
                bootstrap_servers=self.settings.kafka_bootstrap_servers,
                group_id=group_id,
                auto_offset_reset=self.settings.kafka_auto_offset_reset,
                topics=topics  # Pass topics to HCIEKafkaConsumer
            )
            
            logger.info(f"✅ Created HCIEKafkaConsumer for group: {group_id}, topics: {topics or 'default HCIE topics'}")
            return consumer
            
        except Exception as e:
            logger.error(f"❌ Failed to create Kafka consumer: {e}")
            raise
    
    def create_producer(self):
        """Create Kafka producer via factory (no fallback)"""
        if not self.producer_factory:
            raise RuntimeError("❌ Kafka producer factory must be provided")
        
        producer = self.producer_factory.create_producer()
        
        if not producer:
            raise RuntimeError("❌ Kafka producer factory returned None")
        
        logger.info("✅ Created Kafka producer via factory")
        return producer
