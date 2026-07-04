"""
Transfer Measurement Consumer Service

Separate Kafka consumer for measuring knowledge transfer across concepts.
Consumes learning events and writes to transfer_events table for transfer propagation analysis.

Design Principles:
- Separate from UnifiedBrain (not integrated)
- Consumes from existing Kafka topics
- Writes to transfer_events table
- Tracks transfer from source → target concepts
- Measures transfer efficiency
- V3 Integration: Sends telemetry to V3 research transfer API
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime
import uuid

from storage.postgres_store.interaction_store import PostgresInteractionStore

logger = logging.getLogger(__name__)


class TransferMeasurementConsumer:
    """
    Kafka consumer for transfer measurement
    
    RESPONSIBILITIES:
    - Consume learning events from Kafka
    - Extract transfer propagation metrics
    - Record to transfer_events table
    - Track transfer from source → target concepts
    - Measure transfer efficiency
    - Track DAG edge utilization
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "transfer_measurement_group",
        input_topics: list = None,
        enable_v3_integration: bool = True
    ):
        """
        Initialize transfer measurement consumer
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            group_id: Consumer group ID
            input_topics: List of Kafka topics to consume from
            enable_v3_integration: Enable V3 research transfer API integration
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
                logger.info("V3 API client initialized for transfer measurement")
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
            
            logger.info(f"Transfer measurement consumer started on topics: {self.input_topics}")

            # Process messages (iterate the wrapper, not the raw inner consumer, so a
            # failed/None init retries with backoff instead of crashing with NoneType).
            for message in self.consumer:
                self._process_message(message)
                
        except Exception as e:
            logger.error(f"Failed to start transfer measurement consumer: {e}")
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
                self._record_transfer_event(event_data)
                
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
    
    def _record_transfer_event(self, event_data: Dict[str, Any]):
        """
        Record transfer event to database
        
        Args:
            event_data: Event data from Kafka
        """
        try:
            # Extract relevant fields
            user_id = event_data.get("user_id")
            target_concept = event_data.get("concept")
            interaction_number = event_data.get("interaction_number", 0)
            event_id = event_data.get("event_id", str(uuid.uuid4()))
            experiment_run_id = event_data.get("experiment_run_id")
            
            # Extract transfer sources
            source_concepts = event_data.get("transfer_sources", [])
            transfer_amounts = event_data.get("transfer_amounts", {})
            total_transfer = event_data.get("transfer_amount", 0.0)
            
            # Extract efficiency metrics
            total_gain = event_data.get("mastery_delta", 0.0)
            transfer_efficiency = event_data.get("transfer_efficiency", 0.0)
            
            # Calculate transfer efficiency if not provided
            if transfer_efficiency == 0.0 and total_gain > 0:
                transfer_efficiency = total_transfer / total_gain if total_transfer > 0 else 0.0
            
            # Extract DAG edge utilization
            dag_edges_used = event_data.get("dag_edges_used", [])
            edge_weights = event_data.get("edge_weights", {})
            
            # Only record if there's transfer activity
            if source_concepts or total_transfer > 0:
                # Insert into transfer_events table
                query = """
                    INSERT INTO transfer_events (
                        event_id, user_id, target_concept, interaction_number, timestamp,
                        source_concepts, transfer_amounts, total_transfer,
                        total_gain, transfer_efficiency,
                        dag_edges_used, edge_weights,
                        experiment_run_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                params = (
                    event_id, user_id, target_concept, interaction_number, datetime.now(),
                    source_concepts, json.dumps(transfer_amounts), total_transfer,
                    total_gain, transfer_efficiency,
                    json.dumps(dag_edges_used), json.dumps(edge_weights),
                    experiment_run_id
                )
                
                self.db_store.execute_write(query, params)
                
                logger.debug(f"Recorded transfer event for user {user_id}, target {target_concept}")
                
                # V3 Integration: Send telemetry to V3 research transfer API
                if self.enable_v3_integration and self.v3_client:
                    self._send_v3_transfer_telemetry(event_data, source_concepts, transfer_amounts, total_transfer, transfer_efficiency, dag_edges_used, edge_weights)
            
        except Exception as e:
            logger.error(f"Failed to record transfer event: {e}")
    
    def _send_v3_transfer_telemetry(
        self,
        event_data: Dict[str, Any],
        source_concepts: List[str],
        transfer_amounts: Dict[str, float],
        total_transfer: float,
        transfer_efficiency: float,
        dag_edges_used: List[str],
        edge_weights: Dict[str, float]
    ):
        """
        Send transfer telemetry to V3 research transfer API.
        
        Args:
            event_data: Event data from Kafka
            source_concepts: List of source concepts
            transfer_amounts: Transfer amounts per source
            total_transfer: Total transfer amount
            transfer_efficiency: Transfer efficiency
            dag_edges_used: DAG edges used in transfer
            edge_weights: Edge weights
        """
        try:
            telemetry_data = {
                "user_id": event_data.get("user_id"),
                "target_concept": event_data.get("concept"),
                "interaction_number": event_data.get("interaction_number"),
                "timestamp": datetime.now().isoformat(),
                "transfer_metrics": {
                    "source_concepts": source_concepts,
                    "transfer_amounts": transfer_amounts,
                    "total_transfer": total_transfer,
                    "transfer_efficiency": transfer_efficiency,
                    "total_gain": event_data.get("mastery_delta", 0.0)
                },
                "dag_metrics": {
                    "dag_edges_used": dag_edges_used,
                    "edge_weights": edge_weights
                },
                "experiment_run_id": event_data.get("experiment_run_id")
            }
            
            result = self.v3_client.call_research_transfer_api(telemetry_data)
            if result:
                logger.debug("V3 research transfer telemetry sent successfully")
            else:
                logger.warning("V3 research transfer telemetry send failed")
                
        except Exception as e:
            logger.warning(f"Failed to send V3 transfer telemetry: {e}")
    
    def stop(self):
        """Stop the Kafka consumer"""
        if self.consumer:
            self.consumer.close()
        if self.v3_client:
            self.v3_client.close()
        logger.info("Transfer measurement consumer stopped")


def main():
    """Main entry point for transfer measurement consumer"""
    import os
    
    # Get configuration from environment
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    group_id = os.getenv("TRANSFER_MEASUREMENT_GROUP", "transfer_measurement_group")
    
    # Create and start consumer
    consumer = TransferMeasurementConsumer(
        bootstrap_servers=bootstrap_servers,
        group_id=group_id
    )
    
    try:
        consumer.start()
    except KeyboardInterrupt:
        logger.info("Shutting down transfer measurement consumer")
        consumer.stop()


if __name__ == "__main__":
    main()
