"""
Kafka service layer
Handles Kafka event publishing with dual-mode support (CT Avro + EdNet JSON)
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any

# Try to import messaging, but don't fail if not available
try:
    from messaging import get_kafka_producer
except ImportError:
    # Fallback for when messaging module is not available
    def get_kafka_producer():
        return None

from app.models.requests import TaskSubmission

logger = logging.getLogger(__name__)

class KafkaService:
    """Service layer for Kafka operations with dual-mode support"""
    
    def __init__(self, settings=None, producer=None):
        """Initialize Kafka service with settings and producer injection"""
        self.settings = settings
        
        # ✅ Strict producer injection - no fallback
        if not producer:
            raise RuntimeError("❌ Kafka producer must be injected")
        
        self.producer = producer
        self.enabled = True
        
        if self.enabled:
            logger.info("KafkaService initialized with producer")
        else:
            logger.warning("KafkaService initialized without producer - events will not be published")
    
    def publish_task_generated_event(self, user_id: str, task_data: Dict[str, Any]) -> bool:
        """
        Publish task generated event to Kafka
        
        Args:
            user_id: User identifier
            task_data: Task generation result
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Kafka not available - skipping task generated event")
            return False
        
        try:
            success = self.producer.publish_task_generated(
                user_id=user_id,
                task_id=task_data["task_id"],
                concept_id=task_data["concept_id"],
                representation=task_data["representation"],
                difficulty=task_data["difficulty"],
                policy_mode=task_data["policy_mode"],
                selection_metrics=task_data["selection_metrics"],
                processing_time_ms=task_data.get("selection_time_ms", 0)
            )
            
            if success:
                logger.info(f"Published task generated event for {user_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to publish task generated event: {e}")
            return False
    
    def publish_answer_event(self, user_id: str, task_id: str, answer: str, result: Dict[str, Any]) -> bool:
        """
        Publish answer event to Kafka with dual-mode support
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            answer: User's answer
            result: Processing result
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.warning("Kafka not available - event not published")
            return False
        
        try:
            # Publish answer event as JSON.
            # (Legacy CT-Avro branch removed: app.services.kafka_avro no longer exists and
            #  policy_mode 'ct' is retired, so that branch was dead — fell back to JSON anyway.)
            event = {
                "event_type": "answer_submitted",
                "user_id": user_id,
                "task_id": task_id,
                "answer": answer,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }

            self.producer.produce(
                topic="hcie.submissions",
                key=user_id,
                value=json.dumps(event),
                callback=self._delivery_report
            )

            logger.info(f"Published answer event for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish answer event: {e}")
            return False
    
    def publish_task_submitted_event(self, user_id: str, submission_data: TaskSubmission, 
                                    result_data) -> bool:
        """
        Publish task submitted event to Kafka
        
        Args:
            user_id: User identifier
            submission_data: Task submission
            result_data: Processing result
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Kafka not available - skipping task submitted event")
            return False
        
        try:
            # Publish task submitted event
            success1 = self.producer.publish_task_submitted(
                user_id=user_id,
                task_id=submission_data.task_id,
                concept_id=submission_data.node_id,
                representation=submission_data.representation,
                answer=submission_data.answer,
                correct_answer=result_data.get("correct_answer", ""),
                correct=result_data.get("correct", False),
                response_time=result_data.get("response_time", 0.0),
                difficulty=result_data.get("difficulty", 0.5),
                reward=result_data.get("reward", 0.0)
            )
            
            # Publish mastery updated event
            learning_metrics = result_data.get("learning_metrics", {})
            mastery_before = result_data.get("mastery_before", 0)
            mastery_after = result_data.get("mastery_after", 0)
            mastery_change = result_data.get("mastery_change", 0)
            
            success2 = self.producer.publish_mastery_updated(
                user_id=user_id,
                concept_id=submission_data.node_id,
                previous_mastery=mastery_before,
                new_mastery=mastery_after,
                mastery_change=mastery_change,
                uncertainty=learning_metrics.get('uncertainty', 0),
                transferred_nodes=learning_metrics.get('transferred_nodes', 0)
            )
            
            if success1 and success2:
                logger.info(f"Published submission events for {user_id}")
            return success1 and success2
            
        except Exception as e:
            logger.error(f"Failed to publish submission events: {e}")
            return False
    
    def publish_mastery_updated_event(self, user_id: str, concept_id: str, 
                                     learning_metrics: Dict[str, Any]) -> bool:
        """
        Publish mastery updated event to Kafka
        
        Args:
            user_id: User identifier
            concept_id: Concept identifier
            learning_metrics: Learning metrics
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Kafka not available - skipping mastery updated event")
            return False
        
        try:
            success = self.producer.publish_mastery_updated(
                user_id=user_id,
                concept_id=concept_id,
                previous_mastery=learning_metrics.get("mastery_before", 0.3),
                new_mastery=learning_metrics.get("mastery_after", 0.3),
                mastery_change=learning_metrics.get("mastery_change", 0.0),
                uncertainty=learning_metrics.get("uncertainty", 0),
                transferred_nodes=learning_metrics.get("transferred_nodes", 0)
            )
            
            if success:
                logger.info(f"Published mastery updated event for {user_id}: {concept_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to publish mastery updated event: {e}")
            return False
    
    def publish_system_health_event(self, service_name: str, status: str, 
                                  metrics: Dict[str, Any], checks: Dict[str, bool]) -> bool:
        """
        Publish system health event to Kafka
        
        Args:
            service_name: Service name
            status: Service status
            metrics: Health metrics
            checks: Individual check results
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Kafka not available - skipping health event")
            return False
        
        try:
            success = self.producer.publish_system_health(
                service_name=service_name,
                status=status,
                metrics=metrics,
                checks=checks
            )
            
            if success:
                logger.info(f"Published health event for {service_name}: {status}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to publish health event: {e}")
            return False
    
    def publish_user_session_event(self, event_type: str, user_id: str, 
                                 session_data: Dict[str, Any]) -> bool:
        """
        Publish user session event to Kafka
        
        Args:
            event_type: Event type (started/ended)
            user_id: User identifier
            session_data: Session data
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Kafka not available - skipping session event")
            return False
        
        try:
            if event_type == "started":
                success = self.producer.publish_user_session_started(
                    user_id=user_id,
                    user_agent=session_data.get("user_agent"),
                    ip_address=session_data.get("ip_address"),
                    initial_context=session_data.get("context", {})
                )
            elif event_type == "ended":
                success = self.producer.publish_user_session_ended(
                    user_id=user_id,
                    session_duration=session_data.get("duration", 0),
                    total_interactions=session_data.get("interactions", 0),
                    final_context=session_data.get("context", {})
                )
            else:
                logger.warning(f"Unknown session event type: {event_type}")
                return False
            
            if success:
                logger.info(f"Published {event_type} session event for {user_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to publish session event: {e}")
            return False
    
    def get_producer_status(self) -> Dict[str, Any]:
        """
        Get Kafka producer status
        
        Returns:
            Producer status information
        """
        return {
            "enabled": self.enabled,
            "bootstrap_servers": self.producer.bootstrap_servers if self.enabled else None,
            "client_id": self.producer.client_id if self.enabled else None
        }
    
    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.close()
            logger.info("KafkaService closed")
