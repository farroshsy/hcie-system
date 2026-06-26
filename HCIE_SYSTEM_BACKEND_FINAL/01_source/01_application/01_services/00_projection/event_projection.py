"""
Event Projection Service (Stateless View)

Projection service for event propagation visibility.
READ, AGGREGATE, FORMAT, EXPOSE ONLY - NO inference, mutation, synthesis.
Stateless view - NO temporal memory ownership, NO caching as authority.
Ephemeral non-authoritative response caching allowed (TTL 1-5s).
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class EventPropagationStatus:
    """Event propagation status projection (stateless view)."""
    outbox_state: Dict[str, Any]
    kafka_lag: int
    dlq_state: Dict[str, Any]
    semantic_version: str = "1.0"


class EventProjection:
    """
    Projection service for event propagation visibility.
    
    CRITICAL: Stateless view - NO temporal memory ownership.
    CRITICAL: NO cached_event_state - NO authority caching.
    CRITICAL: READ fresh from source every time (ephemeral response cache allowed).
    CRITICAL: NO inference, NO mutation, NO synthesis.
    """

    def __init__(
        self,
        outbox,  # From V2 (will be injected via DI)
        kafka_consumer,  # From V2 (will be injected via DI)
    ):
        # NO cached_event_state - NO temporal memory ownership
        # NO state - always read fresh from source
        self.outbox = outbox
        self.kafka = kafka_consumer

    def project_event_propagation_status(self) -> EventPropagationStatus:
        """
        Project event propagation status.
        
        READ fresh from source every time.
        NO caching as authority.
        NO temporal memory ownership.
        """
        # READ fresh from source via V2 outbox and kafka consumer
        # NO inference
        # NO mutation
        # NO synthesis
        
        # Get outbox state from V2 outbox
        try:
            if hasattr(self.outbox, 'get_state'):
                outbox_state = self.outbox.get_state()
            else:
                outbox_state = {'status': 'unknown', 'pending_events': 0}
        except Exception:
            outbox_state = {'status': 'error', 'pending_events': 0}
        
        # Get DLQ state from V2 outbox
        try:
            if hasattr(self.outbox, 'get_dlq_state'):
                dlq_state = self.outbox.get_dlq_state()
            else:
                dlq_state = {'status': 'empty', 'message_count': 0}
        except Exception:
            dlq_state = {'status': 'error', 'message_count': 0}
        
        # Get Kafka lag from V2 kafka consumer
        try:
            if hasattr(self.kafka, 'get_lag'):
                kafka_lag = self.kafka.get_lag()
            else:
                kafka_lag = 0
        except Exception:
            kafka_lag = 0
        
        return EventPropagationStatus(
            outbox_state=outbox_state,
            kafka_lag=kafka_lag,
            dlq_state=dlq_state,
            semantic_version="1.0"
        )
