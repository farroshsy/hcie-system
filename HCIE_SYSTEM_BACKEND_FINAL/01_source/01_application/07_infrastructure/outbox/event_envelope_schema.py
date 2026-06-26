"""
EventEnvelope Schema for Outbox Persistence
Defines how to store complete event envelopes in database
"""

from sqlalchemy import Column, String, DateTime, Integer, Index, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

Base = declarative_base()

class OutboxEventEnvelope(Base):
    """Complete event envelope storage in outbox with PostgreSQL JSONB"""
    __tablename__ = 'outbox_event_envelopes'
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), nullable=False, unique=True, index=True)  # ✅ Unique constraint
    event_type = Column(String(255), nullable=False, index=True)
    topic = Column(String(255), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # ✅ PostgreSQL JSONB for native JSON support
    envelope = Column(JSONB, nullable=False)
    
    # ✅ Removed compression - let PostgreSQL handle large JSON with TOAST
    
    # ✅ Metadata columns (derived from envelope, validated)
    correlation_id = Column(String(255), nullable=True, index=True)
    causation_id = Column(String(255), nullable=True, index=True)
    source_service = Column(String(255), nullable=True, index=True)
    
    # 🔥 DETERMINISTIC RUNTIME: Deterministic replay metadata
    deterministic_mode = Column(Boolean, nullable=True, index=True)
    deterministic_seed = Column(Integer, nullable=True, index=True)
    
    # 🔥 TRAFFIC CLASSIFICATION: Traffic type for separation
    traffic_type = Column(String(50), nullable=False, default='research', index=True)
    
    # ✅ Indexes for common queries
    __table_args__ = (
        Index('idx_outbox_event_envelopes_event_type_topic', 'event_type', 'topic'),
        Index('idx_outbox_event_envelopes_timestamp', 'timestamp'),
        Index('idx_outbox_event_envelopes_correlation', 'correlation_id'),
        # ✅ CRITICAL: Optimize worker query performance
        Index('idx_outbox_pending_created', 'status', 'created_at'),
    )
    
    # Processing metadata
    status = Column(String(50), nullable=False, default='pending', index=True)
    retry_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    
    @classmethod
    def from_envelope(cls, envelope, status='pending'):
        """Create from EventEnvelope with validation"""
        # ✅ Validate consistency between envelope and columns
        if not envelope.event_id:
            raise ValueError("Event envelope must have event_id")
        if not envelope.event_type:
            raise ValueError("Event envelope must have event_type")
        if not envelope.topic:
            raise ValueError("Event envelope must have topic")
        if not envelope.timestamp:
            raise ValueError("Event envelope must have timestamp")
        
        # ✅ Validate version
        if envelope.version != 1:
            raise ValueError(f"Unsupported event version: {envelope.version}. Current version: 1")
        
        # ✅ Create with proper JSONB serialization
        envelope_dict = envelope.to_dict()
        
        # ✅ Extract metadata for derived columns
        metadata = envelope_dict.get('metadata', {})
        payload = envelope_dict.get('payload', {})
        
        # 🔥 TRAFFIC CLASSIFICATION: Extract traffic_type from payload or metadata
        traffic_type = payload.get('traffic_type') or metadata.get('traffic_type') or 'research'
        
        return cls(
            event_id=envelope.event_id,
            event_type=envelope.event_type,
            topic=envelope.topic,
            version=envelope.version,
            timestamp=envelope.timestamp,
            envelope=envelope_dict,  # ✅ Store as JSONB
            correlation_id=metadata.get('correlation_id'),
            causation_id=metadata.get('causation_id'),
            source_service=metadata.get('source_service'),
            traffic_type=traffic_type,
            status=status
        )
    
    def to_envelope(self):
        """Convert back to EventEnvelope with proper error handling"""
        envelope_data = self.envelope
        
        if isinstance(envelope_data, str):
            logger.warning("⚠️ Legacy TEXT envelope detected - migrating to JSONB")
            try:
                envelope_data = json.loads(envelope_data)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse legacy envelope: {e}")
                raise ValueError(f"Invalid legacy envelope format: {e}")
        elif not isinstance(envelope_data, dict):
            raise ValueError(f"Invalid envelope type: {type(envelope_data)}")

        # Local import mirrors outbox_pattern.py (avoids circular import with event_bus)
        from app.infrastructure.messaging.event_bus import EventEnvelope
        return EventEnvelope.from_dict(envelope_data)
    
    @classmethod
    def create_from_dict(cls, data: Dict[str, Any], status='pending'):
        """Create from dictionary with validation"""
        from app.infrastructure.messaging.event_bus import EventEnvelope
        envelope = EventEnvelope.from_dict(data)
        return cls.from_envelope(envelope, status)
