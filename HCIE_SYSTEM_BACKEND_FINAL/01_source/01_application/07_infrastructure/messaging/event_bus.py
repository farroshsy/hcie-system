"""
Event Bus Interface - Abstract transport layer
Decouples Outbox from specific transport implementations
"""

import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class EventEnvelope:
    """Strongly-typed event envelope for EventBus with metadata and partitioning"""
    event_id: str
    event_type: str
    payload: Dict[str, Any]
    topic: str
    version: int = 1
    timestamp: Optional[datetime] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    source_service: Optional[str] = None
    partition_key: Optional[str] = None  # ✅ Pre-computed partition key
    metadata: Optional[Dict[str, Any]] = None  # ✅ B3.6: Trace context and other metadata
    
    # 🔥 DETERMINISTIC RUNTIME: Deterministic replay metadata
    deterministic_mode: Optional[bool] = None  # Whether event was generated in deterministic mode
    deterministic_seed: Optional[int] = None  # Seed used for deterministic generation
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "topic": self.topic,
            "version": self.version,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "source_service": self.source_service,
            "partition_key": self.partition_key,
            "metadata": self.metadata,
            # 🔥 DETERMINISTIC RUNTIME: Include deterministic metadata
            "deterministic_mode": self.deterministic_mode,
            "deterministic_seed": self.deterministic_seed
        }
    
    def to_compressed_json(self) -> str:
        """Convert to compressed JSON for storage"""
        import json
        import gzip
        return gzip.compress(json.dumps(self.to_dict()).encode('utf-8')).decode('latin1')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventEnvelope':
        """Create from dictionary"""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)
        
        metadata = data.get('metadata', {})
        
        return cls(
            event_id=data['event_id'],
            event_type=data['event_type'],
            payload=data['payload'],
            topic=data['topic'],
            version=data.get('version', 1),
            timestamp=timestamp,
            correlation_id=metadata.get('correlation_id'),
            causation_id=metadata.get('causation_id'),
            source_service=metadata.get('source_service'),
            partition_key=data.get('partition_key'),  # ✅ Read from top level, not metadata
            metadata=metadata,
            # 🔥 DETERMINISTIC RUNTIME: Read deterministic metadata
            deterministic_mode=data.get('deterministic_mode'),
            deterministic_seed=data.get('deterministic_seed')
        )

class EventBus(ABC):
    """Abstract event bus interface for transport-agnostic event publishing"""
    
    @abstractmethod
    def publish(self, event: EventEnvelope) -> bool:
        """Publish event to transport"""
        pass
    
    @abstractmethod
    def publish_batch(self, events: list[EventEnvelope]) -> Dict[str, Any]:
        """Publish multiple events in batch"""
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if event bus is healthy"""
        pass
    
    # Backward compatibility
    def publish_dict(self, event: Dict[str, Any]) -> bool:
        """Publish dict event (backward compatibility)"""
        envelope = EventEnvelope(
            event_id=event.get('event_id', 'unknown'),
            event_type=event.get('event_type', 'unknown'),
            payload=event.get('payload', {}),
            topic=event.get('topic', 'unknown')
        )
        return self.publish(envelope)
    
    def publish_schema_event(self, event_type: str, payload: Dict[str, Any], 
                           topic: str, event_id: Optional[str] = None) -> bool:
        """Publish event with schema validation"""
        from .event_schema import event_schema_manager
        
        # Validate event against schema
        if not event_schema_manager.validate_event(event_type, payload):
            logger.error(f"❌ Event validation failed for {event_type}")
            return False
        
        # Create envelope
        if not event_id:
            import uuid
            event_id = str(uuid.uuid4())
        
        envelope = EventEnvelope(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            topic=topic
        )
        
        return self.publish(envelope)

class KafkaEventBus(EventBus):
    """Kafka implementation of event bus with circuit breaker"""
    
    def __init__(self, kafka_producer):
        self.kafka_producer = kafka_producer
        self.circuit_breaker = None
        
        # Initialize circuit breaker
        from .circuit_breaker import get_circuit_breaker, CircuitBreakerConfig
        self.circuit_breaker = get_circuit_breaker(CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        ))
    
    def publish(self, event: EventEnvelope) -> bool:
        """Publish event via Kafka with circuit breaker protection and strict partitioning"""
        def _publish():
            # ✅ Require pre-computed partition key - no recomputation
            if event.partition_key is None:
                raise RuntimeError(
                    f"Partition key must be precomputed for event {event.event_id}. "
                    f"EventBus is a transport layer, not a partitioning service."
                )
            
            # ✅ Publish with partition key (let Kafka handle partitioning)
            return self.kafka_producer.publish_event_direct(
                topic=event.topic,
                event_type=event.event_type,
                payload=event.payload,
                key=event.partition_key  # Pre-computed partition key
            )
        
        try:
            return self.circuit_breaker.call(_publish)
        except Exception as e:
            logger.error(f"❌ Failed to publish event via Kafka: {e}")
            return False
    
    def publish_batch(self, events: list[EventEnvelope]) -> Dict[str, Any]:
        """Publish multiple events via Kafka"""
        results = {"published": 0, "failed": 0, "errors": []}
        
        for event in events:
            success = self.publish(event)
            if success:
                results["published"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"Event {event.event_id}")
        
        return results
    
    def is_healthy(self) -> bool:
        """Check if Kafka producer and circuit breaker are healthy"""
        kafka_healthy = self.kafka_producer is not None
        
        if self.circuit_breaker:
            circuit_state = self.circuit_breaker.get_state()
            circuit_healthy = circuit_state["state"] != "open"
        else:
            circuit_healthy = True
        
        return kafka_healthy and circuit_healthy
    
    def get_circuit_state(self) -> Dict[str, Any]:
        """Get circuit breaker state for monitoring"""
        if self.circuit_breaker:
            return self.circuit_breaker.get_state()
        return {"state": "no_circuit_breaker"}

class HTTPOutboxEventBus(EventBus):
    """HTTP fallback implementation for event bus"""
    
    def __init__(self, http_client=None):
        self.http_client = http_client
    
    def publish(self, event: Dict[str, Any]) -> bool:
        """Publish event via HTTP"""
        # TODO: Implement HTTP event publishing
        logger.warning("⚠️ HTTP EventBus not implemented yet")
        return False
    
    def publish_batch(self, events: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Publish multiple events via HTTP"""
        # TODO: Implement HTTP batch publishing
        logger.warning("⚠️ HTTP EventBus batch not implemented yet")
        return {"published": 0, "failed": len(events), "errors": []}
    
    def is_healthy(self) -> bool:
        """Check if HTTP client is healthy"""
        return self.http_client is not None
