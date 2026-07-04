"""
Kafka Partitioning Strategy
Ensures ordering guarantees for related events using explicit mapping
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class KafkaPartitioningStrategy:
    """Kafka partitioning strategy for event ordering"""
    
    # ✅ Explicit schema-driven partitioning rules
    PARTITION_KEYS = {
        # User events - partition by user_id for user context ordering
        "user_registered": "user_id",
        "user_logged_in": "user_id",
        "user_logged_out": "user_id",
        "user_profile_updated": "user_id",
        "password_changed": "user_id",
        "token_refreshed": "user_id",
        
        # Task events - partition by user_id to maintain user context
        "TaskAttemptSubmitted": "user_id",  # Canonical: Learner submitted attempt
        "task_generated": "user_id",
        "task_submitted": "user_id",
        "task_completed": "user_id",
        
        # Learning events - partition by user_id for learning analytics
        "learning_interaction": "user_id",  # UX API learning events (F-002 fix)
        "LearningProcessed": "user_id",   # Canonical: Cognition processed by UnifiedBrain
        "CognitionUpdated": "user_id",    # Canonical: Cognitive state updated for projections
        "ProjectionUpdated": "user_id",   # Canonical: Projection materialized for frontend
        "AdaptationGenerated": "user_id", # Canonical: Adaptation derived for projection enrichment (B3.3 Phase A)
        "RecommendationGenerated": "user_id", # Canonical: single recommendation authority (P2 fix — was missing, blocked outbox persistence)

        # Analytics events - partition by session_id or user_id
        "user_session_started": "session_id",
        "user_session_ended": "session_id",
        
        # System events - no ordering requirement (round-robin)
        "system_health_check": None,
    }
    
    @staticmethod
    def get_partition_key(event: Dict[str, Any]) -> Optional[str]:
        """
        Get partition key for event using explicit mapping
        
        Strategy:
        - Use explicit mapping for known event types
        - Validate partition key presence
        - Fail fast for missing keys
        """
        event_type = event.get('event_type', '')
        payload = event.get('payload', {})
        
        # ✅ Use explicit mapping
        partition_key_field = KafkaPartitioningStrategy.PARTITION_KEYS.get(event_type)
        
        if partition_key_field:
            # ✅ Validate partition key presence - fail fast
            value = payload.get(partition_key_field)
            if not value:
                raise ValueError(
                    f"Missing partition key '{partition_key_field}' for event '{event_type}'. "
                    f"Payload: {list(payload.keys())}"
                )
            return value
        
        # ✅ Fail fast for unknown events - no silent degradation
        raise ValueError(f"No partition rule for event_type: {event_type}. "
                        f"Known types: {list(KafkaPartitioningStrategy.PARTITION_KEYS.keys())}")
    
    @staticmethod
    def should_preserve_order(event_type: str) -> bool:
        """
        Determine if event type requires ordering guarantees
        """
        return event_type in KafkaPartitioningStrategy.PARTITION_KEYS and \
               KafkaPartitioningStrategy.PARTITION_KEYS[event_type] is not None
    
    @staticmethod
    def get_partitioning_rules() -> Dict[str, Optional[str]]:
        """
        Get all partitioning rules for monitoring and debugging
        Rules are version-controlled in code, not runtime mutable
        """
        return KafkaPartitioningStrategy.PARTITION_KEYS.copy()
    
    # ✅ Removed add_partition_rule - rules are version-controlled in code
    # Runtime mutation causes inconsistency across instances

# ✅ Remove ordering validator - rely on Kafka partition ordering
# Kafka guarantees order within partition, not timestamp ordering
# Distributed timestamp validation is fundamentally flawed
