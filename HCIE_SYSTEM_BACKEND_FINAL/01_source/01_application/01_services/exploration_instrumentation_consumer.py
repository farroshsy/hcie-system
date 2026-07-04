"""
Exploration Instrumentation Consumer Service

Separate Kafka consumer for instrumenting exploration behavior.
Consumes learning events and writes to exploration_events table for exploration analysis.

Design Principles:
- Separate from UnifiedBrain (not integrated)
- Consumes from existing Kafka topics
- Writes to exploration_events table
- Tracks exploration behavior metrics
- V3 Integration: Sends telemetry to V3 research policy API
"""

import json
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime
import uuid

from storage.postgres_store.interaction_store import PostgresInteractionStore

logger = logging.getLogger(__name__)


class ExplorationInstrumentationConsumer:
    """
    Kafka consumer for exploration instrumentation
    
    RESPONSIBILITIES:
    - Consume learning events from Kafka
    - Extract exploration behavior metrics
    - Record to exploration_events table
    - Track action selection distribution
    - Track exploration vs exploitation ratio
    - Track JT volatility correlation
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "exploration_instrumentation_group",
        input_topics: list = None,
        enable_v3_integration: bool = True
    ):
        """
        Initialize exploration instrumentation consumer
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            group_id: Consumer group ID
            input_topics: List of Kafka topics to consume from
            enable_v3_integration: Enable V3 research policy API integration
        """
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.input_topics = input_topics or ["learning_analytics", "cognition_updated"]
        self.consumer = None
        self.db_store = PostgresInteractionStore()
        self.enable_v3_integration = enable_v3_integration
        
        # V3 API client for research telemetry
        self.v3_client = None
        if self.enable_v3_integration:
            try:
                from app.infrastructure.v3.v3_client import V3APIClient
                self.v3_client = V3APIClient()
                logger.info("V3 API client initialized for exploration instrumentation")
            except ImportError:
                logger.warning("V3 API client not available - V3 integration disabled")
                self.enable_v3_integration = False
        
        # Track action coverage per user
        self.user_action_coverage: Dict[str, Set[str]] = {}

        # V3 telemetry rate-throttle: at most one call per 10 seconds to avoid
        # hammering the research policy API during high-throughput backlog drain.
        self._last_v3_telemetry_ts: float = 0.0
        self._v3_telemetry_min_interval: float = 10.0
    
    def start(self):
        """Start the Kafka consumer"""
        try:
            from messaging import HCIEKafkaConsumer
            
            self.consumer = HCIEKafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset='latest',
                topics=self.input_topics
            )
            
            logger.info(f"Exploration instrumentation consumer started on topics: {self.input_topics}")

            # Process messages (iterate the wrapper, not the raw inner consumer, so a
            # failed/None init retries with backoff instead of crashing with NoneType).
            for message in self.consumer:
                self._process_message(message)
                
        except Exception as e:
            logger.error(f"Failed to start exploration instrumentation consumer: {e}")
            raise
    
    def _process_message(self, message):
        """
        Process a single Kafka message
        
        Args:
            message: Kafka message
        """
        try:
            event_data = message.value
            event_type = event_data.get("event_type")
            
            # Only process relevant event types
            if event_type in ["LearningProcessed", "CognitionUpdated"]:
                self._record_exploration_event(event_data)
                
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
    
    def _record_exploration_event(self, event_data: Dict[str, Any]):
        """
        Record exploration event to database
        
        Args:
            event_data: Event data from Kafka
        """
        try:
            # Extract relevant fields
            user_id = event_data.get("user_id")
            interaction_number = event_data.get("interaction_number", 0)
            event_id = event_data.get("event_id", str(uuid.uuid4()))
            experiment_run_id = event_data.get("experiment_run_id")
            
            # Extract action selection
            action_selected = event_data.get("action_selected")
            action_distribution = event_data.get("action_distribution", {})
            
            # Extract exploration metrics
            exploration_pressure = event_data.get("exploration_pressure")
            
            # Calculate exploration ratio (exploration vs exploitation)
            exploration_ratio = self._calculate_exploration_ratio(action_distribution)
            
            # Track action coverage
            action_coverage = self._update_action_coverage(user_id, action_selected)
            
            # Extract JT correlation
            jt_value = event_data.get("jt_value")
            jt_volatility = event_data.get("jt_volatility")
            exploration_multiplier = event_data.get("exploration_multiplier")
            
            # Insert into exploration_events table
            query = """
                INSERT INTO exploration_events (
                    event_id, user_id, interaction_number, timestamp,
                    action_selected, action_distribution,
                    exploration_pressure, exploration_ratio, action_coverage,
                    jt_value, jt_volatility, exploration_multiplier,
                    experiment_run_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                event_id, user_id, interaction_number, datetime.now(),
                action_selected, json.dumps(action_distribution),
                exploration_pressure, exploration_ratio, action_coverage,
                jt_value, jt_volatility, exploration_multiplier,
                experiment_run_id
            )
            
            self.db_store.execute_write(query, params)
            
            logger.debug(f"Recorded exploration event for user {user_id}")
            
            # V3 Integration: Send telemetry to V3 research policy API
            # Throttled to at most once per _v3_telemetry_min_interval seconds so
            # the research policy endpoint is not hammered during backlog drain.
            import time as _time
            if self.enable_v3_integration and self.v3_client:
                now = _time.monotonic()
                if now - self._last_v3_telemetry_ts >= self._v3_telemetry_min_interval:
                    self._send_v3_policy_telemetry(event_data, exploration_ratio, action_coverage, jt_value, jt_volatility)
                    self._last_v3_telemetry_ts = now
            
        except Exception as e:
            logger.error(f"Failed to record exploration event: {e}")
    
    def _send_v3_policy_telemetry(
        self,
        event_data: Dict[str, Any],
        exploration_ratio: float,
        action_coverage: int,
        jt_value: Optional[float],
        jt_volatility: Optional[float]
    ):
        """
        Send exploration telemetry to V3 research policy API.
        
        Args:
            event_data: Event data from Kafka
            exploration_ratio: Exploration vs exploitation ratio
            action_coverage: Number of unique actions selected
            jt_value: J-value (objective function)
            jt_volatility: J-value volatility
        """
        try:
            telemetry_data = {
                "user_id": event_data.get("user_id"),
                "interaction_number": event_data.get("interaction_number"),
                "timestamp": datetime.now().isoformat(),
                "exploration_metrics": {
                    "exploration_ratio": exploration_ratio,
                    "action_coverage": action_coverage,
                    "exploration_pressure": event_data.get("exploration_pressure"),
                    "exploration_multiplier": event_data.get("exploration_multiplier")
                },
                "policy_metrics": {
                    "jt_value": jt_value,
                    "jt_volatility": jt_volatility,
                    "action_selected": event_data.get("action_selected"),
                    "action_distribution": event_data.get("action_distribution")
                },
                "experiment_run_id": event_data.get("experiment_run_id")
            }
            
            result = self.v3_client.call_research_policy_api(telemetry_data)
            if result:
                logger.debug("V3 research policy telemetry sent successfully")
            else:
                logger.warning("V3 research policy telemetry send failed")
                
        except Exception as e:
            logger.warning(f"Failed to send V3 policy telemetry: {e}")
    
    def _calculate_exploration_ratio(self, action_distribution: Dict[str, float]) -> float:
        """
        Calculate exploration vs exploitation ratio
        
        Args:
            action_distribution: Probability distribution over actions
            
        Returns:
            Exploration ratio (0-1, higher = more exploration)
        """
        if not action_distribution:
            return 0.5  # Default to balanced
        
        # Exploration ratio = entropy of distribution / max possible entropy
        # This measures how evenly distributed the actions are
        import math
        from scipy.stats import entropy
        
        values = list(action_distribution.values())
        if len(values) <= 1:
            return 0.0
        
        # Calculate normalized entropy
        max_entropy = math.log(len(values))
        actual_entropy = entropy(values)
        exploration_ratio = actual_entropy / max_entropy if max_entropy > 0 else 0.0
        
        return exploration_ratio
    
    def _update_action_coverage(self, user_id: str, action_selected: str) -> int:
        """
        Update and return action coverage for user
        
        Args:
            user_id: User identifier
            action_selected: Action selected in this interaction
            
        Returns:
            Number of unique actions selected so far
        """
        if user_id not in self.user_action_coverage:
            self.user_action_coverage[user_id] = set()
        
        if action_selected:
            self.user_action_coverage[user_id].add(action_selected)
        
        return len(self.user_action_coverage[user_id])
    
    def stop(self):
        """Stop the Kafka consumer"""
        if self.consumer:
            self.consumer.close()
        if self.v3_client:
            self.v3_client.close()
        logger.info("Exploration instrumentation consumer stopped")


def main():
    """Main entry point for exploration instrumentation consumer"""
    import os
    
    # Get configuration from environment
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    group_id = os.getenv("EXPLORATION_INSTRUMENTATION_GROUP", "exploration_instrumentation_group")
    
    # Create and start consumer
    consumer = ExplorationInstrumentationConsumer(
        bootstrap_servers=bootstrap_servers,
        group_id=group_id
    )
    
    try:
        consumer.start()
    except KeyboardInterrupt:
        logger.info("Shutting down exploration instrumentation consumer")
        consumer.stop()


if __name__ == "__main__":
    main()
