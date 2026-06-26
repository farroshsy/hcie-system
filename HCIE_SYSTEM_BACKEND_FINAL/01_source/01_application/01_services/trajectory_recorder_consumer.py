"""
Trajectory Recorder Consumer Service

Separate Kafka consumer for recording temporal governance trajectories.
Consumes learning events and writes to trajectory_events table for time-series analysis.

Design Principles:
- Separate from UnifiedBrain (not integrated)
- Consumes from existing Kafka topics
- Writes to trajectory_events table (time-series optimized)
- Records JT trajectory, learner contributions, state evolution
- V3 Integration: Sends trajectory data to V3 trajectory API
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from storage.postgres_store.interaction_store import PostgresInteractionStore

logger = logging.getLogger(__name__)


class TrajectoryRecorderConsumer:
    """
    Kafka consumer for recording trajectory events
    
    RESPONSIBILITIES:
    - Consume learning events from Kafka
    - Extract governance signals (JT, learner contributions)
    - Record to trajectory_events table (time-series)
    - Support temporal analysis and trend detection
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "trajectory_recorder_group",
        input_topics: list = None,
        enable_v3_integration: bool = True
    ):
        """
        Initialize trajectory recorder consumer
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            group_id: Consumer group ID
            input_topics: List of Kafka topics to consume from
            enable_v3_integration: Enable V3 trajectory API integration
        """
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.input_topics = input_topics or ["learning_analytics", "cognition_updated"]
        self.consumer = None
        self.db_store = PostgresInteractionStore()
        self.enable_v3_integration = enable_v3_integration
        
        # V3 API client for trajectory recording
        self.v3_client = None
        if self.enable_v3_integration:
            try:
                from app.infrastructure.v3.v3_client import V3APIClient
                self.v3_client = V3APIClient()
                logger.info("V3 API client initialized for trajectory recorder")
            except ImportError:
                logger.warning("V3 API client not available - V3 integration disabled")
                self.enable_v3_integration = False
        
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
            
            logger.info(f"Trajectory recorder consumer started on topics: {self.input_topics}")
            
            # Process messages
            for message in self.consumer.consumer:
                self._process_message(message)
                
        except Exception as e:
            logger.error(f"Failed to start trajectory recorder consumer: {e}")
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
                self._record_trajectory_event(event_data)
                
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
    
    def _record_trajectory_event(self, event_data: Dict[str, Any]):
        """
        Record trajectory event to database
        
        Args:
            event_data: Event data from Kafka
        """
        try:
            # Extract relevant fields
            user_id = event_data.get("user_id")
            concept = event_data.get("concept")
            interaction_number = event_data.get("interaction_number", 0)
            event_id = event_data.get("event_id", str(uuid.uuid4()))
            experiment_run_id = event_data.get("experiment_run_id")
            
            # Extract governance signals
            jt_value = event_data.get("jt_value")
            jt_weights = event_data.get("jt_weights", {})
            jt_components = event_data.get("jt_components", {})
            
            # Extract learner contributions
            lyapunov_weight = event_data.get("lyapunov_weight")
            bayesian_weight = event_data.get("bayesian_weight")
            kalman_weight = event_data.get("kalman_weight")
            learner_contributions = event_data.get("learner_contributions", {})
            
            # Extract state evolution
            mastery_delta = event_data.get("mastery_delta")
            uncertainty_delta = event_data.get("uncertainty_delta")
            zpd_delta = event_data.get("zpd_delta")
            
            # Extract transfer signals
            transfer_sources = event_data.get("transfer_sources", [])
            transfer_amounts = event_data.get("transfer_amounts", {})
            transfer_efficiency = event_data.get("transfer_efficiency")
            
            # Extract exploration
            exploration_pressure = event_data.get("exploration_pressure")
            action_selected = event_data.get("action_selected")
            action_distribution = event_data.get("action_distribution", {})
            
            # Insert into trajectory_events table
            query = """
                INSERT INTO trajectory_events (
                    event_id, user_id, concept, interaction_number, timestamp,
                    jt_value, jt_weights, jt_components,
                    lyapunov_weight, bayesian_weight, kalman_weight, learner_contributions,
                    mastery_delta, uncertainty_delta, zpd_delta,
                    transfer_sources, transfer_amounts, transfer_efficiency,
                    exploration_pressure, action_selected, action_distribution,
                    experiment_run_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                event_id, user_id, concept, interaction_number, datetime.now(),
                jt_value, json.dumps(jt_weights), json.dumps(jt_components),
                lyapunov_weight, bayesian_weight, kalman_weight, json.dumps(learner_contributions),
                mastery_delta, uncertainty_delta, zpd_delta,
                transfer_sources, json.dumps(transfer_amounts), transfer_efficiency,
                exploration_pressure, action_selected, json.dumps(action_distribution),
                experiment_run_id
            )
            
            self.db_store.execute_write(query, params)
            
            logger.debug(f"Recorded trajectory event for user {user_id}, concept {concept}")
            
            # V3 Integration: Send trajectory data to V3 trajectory API
            if self.enable_v3_integration and self.v3_client:
                self._send_v3_trajectory_data(event_data, jt_value, jt_weights, jt_components, lyapunov_weight, bayesian_weight, kalman_weight)
            
        except Exception as e:
            logger.error(f"Failed to record trajectory event: {e}")
    
    def _send_v3_trajectory_data(
        self,
        event_data: Dict[str, Any],
        jt_value: Optional[float],
        jt_weights: Dict[str, float],
        jt_components: Dict[str, float],
        lyapunov_weight: Optional[float],
        bayesian_weight: Optional[float],
        kalman_weight: Optional[float]
    ):
        """
        Send trajectory data to V3 trajectory API.
        
        Args:
            event_data: Event data from Kafka
            jt_value: J-value (objective function)
            jt_weights: J-value component weights
            jt_components: J-value components
            lyapunov_weight: Lyapunov learner weight
            bayesian_weight: Bayesian learner weight
            kalman_weight: Kalman learner weight
        """
        try:
            trajectory_data = {
                "user_id": event_data.get("user_id"),
                "concept": event_data.get("concept"),
                "interaction_number": event_data.get("interaction_number"),
                "timestamp": datetime.now().isoformat(),
                "governance_signals": {
                    "jt_value": jt_value,
                    "jt_weights": jt_weights,
                    "jt_components": jt_components
                },
                "learner_contributions": {
                    "lyapunov_weight": lyapunov_weight,
                    "bayesian_weight": bayesian_weight,
                    "kalman_weight": kalman_weight,
                    "learner_contributions": event_data.get("learner_contributions", {})
                },
                "state_evolution": {
                    "mastery_delta": event_data.get("mastery_delta"),
                    "uncertainty_delta": event_data.get("uncertainty_delta"),
                    "zpd_delta": event_data.get("zpd_delta")
                },
                "experiment_run_id": event_data.get("experiment_run_id")
            }
            
            result = self.v3_client.call_trajectory_api(event_data.get("user_id"), trajectory_data)
            if result:
                logger.debug("V3 trajectory data sent successfully")
            else:
                logger.warning("V3 trajectory data send failed")
                
        except Exception as e:
            logger.warning(f"Failed to send V3 trajectory data: {e}")
    
    def stop(self):
        """Stop the Kafka consumer"""
        if self.consumer:
            self.consumer.close()
        if self.v3_client:
            self.v3_client.close()
        logger.info("Trajectory recorder consumer stopped")


def main():
    """Main entry point for trajectory recorder consumer"""
    import os
    
    # Get configuration from environment
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    group_id = os.getenv("TRAJECTORY_RECORDER_GROUP", "trajectory_recorder_group")
    
    # Create and start consumer
    consumer = TrajectoryRecorderConsumer(
        bootstrap_servers=bootstrap_servers,
        group_id=group_id
    )
    
    try:
        consumer.start()
    except KeyboardInterrupt:
        logger.info("Shutting down trajectory recorder consumer")
        consumer.stop()


if __name__ == "__main__":
    main()
