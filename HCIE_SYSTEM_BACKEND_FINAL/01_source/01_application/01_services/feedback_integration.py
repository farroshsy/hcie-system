"""
Feedback Integration Service
Closes the online learning loop between API decisions and learning updates
"""

import json
import logging
import asyncio
import os
import sys
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable
import redis

from core.reward.reward import RewardCalculator
from storage.postgres_store import PostgresInteractionStore

logger = logging.getLogger(__name__)

# Get Kafka bootstrap servers from environment
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092').split(',')

def wait_for_kafka(max_retries=30, retry_delay=2):
    """Wait for Kafka to be available"""
    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                request_timeout_ms=5000,
                api_version=(0, 10, 1)
            )
            producer.close()
            logger.info(f"Kafka is available after {attempt + 1} attempts")
            return True
        except NoBrokersAvailable:
            logger.warning(f"Kafka not available, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Unexpected error checking Kafka: {e}")
            time.sleep(retry_delay)
    
    logger.error("Kafka not available after maximum retries")
    return False

class FeedbackIntegrationService:
    """
    Integrates user feedback into the learning pipeline
    Provides real-time learning loop closure
    """
    
    def __init__(self):
        logger.info("Initializing Feedback Integration Service...")
        
        # Wait for Kafka to be available
        if not wait_for_kafka():
            raise RuntimeError("Failed to connect to Kafka after multiple retries")
        
        self.redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        self.db_store = PostgresInteractionStore()
        self.reward_calculator = RewardCalculator()
        
        logger.info(f"Connecting to Kafka at: {KAFKA_BOOTSTRAP_SERVERS}")
        
        # Kafka producer for learning events
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            enable_idempotence=True,
            acks='all',
            retries=3,
            request_timeout_ms=10000
        )
        
        # Kafka consumer for feedback events
        self.kafka_consumer = KafkaConsumer(
            'user-feedback',
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            group_id='feedback-processor',
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            session_timeout_ms=30000,
            heartbeat_interval_ms=3000,
            request_timeout_ms=40000
        )
        
        logger.info("Feedback Integration Service initialized successfully")
    
    async def submit_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit user feedback and trigger immediate learning update
        
        Args:
            feedback: User feedback dictionary
            
        Returns:
            Processing result
        """
        try:
            # Validate feedback
            required_fields = ['user_id', 'action_taken', 'outcome']
            for field in required_fields:
                if field not in feedback:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create feedback event
            feedback_event = {
                'event_id': feedback.get('event_id', f"feedback_{datetime.utcnow().isoformat()}"),
                'user_id': feedback['user_id'],
                'event_type': 'task_completed',
                'action_taken': feedback['action_taken'],
                'outcome': feedback['outcome'],
                'correct': feedback.get('correct', False),
                'response_time': feedback.get('response_time', 30.0),
                'difficulty': feedback.get('difficulty', 0.5),
                'consistency': feedback.get('consistency'),
                'timestamp': datetime.utcnow().isoformat(),
                'feedback_source': 'api'
            }
            
            # Calculate reward immediately
            reward_data = self.reward_calculator.compute_detailed_reward(
                correct=feedback_event['correct'],
                time_taken=feedback_event['response_time'],
                difficulty=feedback_event['difficulty'],
                response_consistency=feedback_event.get('consistency')
            )
            
            feedback_event['reward'] = reward_data.get('total_reward', 0.1)
            feedback_event['reward_components'] = reward_data
            
            # Send to Kafka for processing
            future = self.kafka_producer.send(
                'user-interactions',
                key=feedback_event['user_id'],
                value=feedback_event
            )
            
            # Block for confirmation (synchronous for API response)
            record_metadata = future.get(timeout=10)
            
            # Cache immediate feedback for real-time decisions
            cache_key = f"feedback:{feedback['user_id']}"
            self.redis_client.setex(
                cache_key,
                timedelta(minutes=5),
                json.dumps({
                    'action': feedback['action_taken'],
                    'reward': feedback_event['reward'],
                    'timestamp': feedback_event['timestamp']
                })
            )
            
            logger.info(f"📝 Feedback submitted for user {feedback['user_id']}")
            
            return {
                'status': 'submitted',
                'event_id': feedback_event['event_id'],
                'reward': feedback_event['reward'],
                'kafka_offset': record_metadata.offset,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Feedback submission error: {e}")
            raise
    
    async def get_immediate_feedback(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get most recent feedback for user (for real-time decisions)
        
        Args:
            user_id: User identifier
            
        Returns:
            Recent feedback or None
        """
        try:
            cache_key = f"feedback:{user_id}"
            feedback_data = self.redis_client.get(cache_key)
            
            if feedback_data:
                return json.loads(feedback_data)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting immediate feedback: {e}")
            return None
    
    async def process_feedback_loop(self):
        """
        Background process to handle feedback events
        Provides continuous learning loop closure
        """
        logger.info("🔄 Starting feedback processing loop")
        
        try:
            for message in self.kafka_consumer:
                try:
                    feedback_event = message.value
                    
                    # Process feedback event
                    await self._process_feedback_event(feedback_event)
                    
                    # Commit offset after successful processing
                    self.kafka_consumer.commit()
                    
                    logger.info(f"✅ Processed feedback for user {feedback_event.get('user_id')}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing feedback message: {e}")
                    # Don't commit offset on error
                    
        except Exception as e:
            logger.error(f"❌ Feedback loop error: {e}")
    
    async def _process_feedback_event(self, event: Dict[str, Any]):
        """
        Process individual feedback event
        
        Args:
            event: Feedback event data
        """
        user_id = event.get('user_id')
        
        # Update user's recent feedback history
        history_key = f"feedback_history:{user_id}"
        history = self.redis_client.lrange(history_key, 0, 9)  # Last 10 feedbacks
        
        # Add new feedback
        feedback_summary = {
            'action': event.get('action_taken'),
            'reward': event.get('reward'),
            'timestamp': event.get('timestamp'),
            'outcome': event.get('outcome')
        }
        
        self.redis_client.lpush(history_key, json.dumps(feedback_summary))
        self.redis_client.ltrim(history_key, 0, 9)  # Keep only last 10
        self.redis_client.expire(history_key, timedelta(hours=24))
        
        # Trigger immediate state refresh if needed
        await self._trigger_state_refresh(user_id)
    
    async def _trigger_state_refresh(self, user_id: str):
        """
        Trigger immediate state refresh for real-time decisions
        
        Args:
            user_id: User identifier
        """
        try:
            # Get current state from database
            conn = self.db_store._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT mastery FROM user_state 
                WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                state = json.loads(result[0])
                
                # Cache updated state for fast access
                cache_key = f"user_state:{user_id}"
                self.redis_client.setex(
                    cache_key,
                    timedelta(minutes=10),
                    json.dumps(state)
                )
                
                logger.info(f"🔄 State refreshed for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error refreshing state for user {user_id}: {e}")
    
    async def get_learning_loop_metrics(self, user_id: str) -> Dict[str, Any]:
        """
        Get learning loop metrics for monitoring
        
        Args:
            user_id: User identifier
            
        Returns:
            Learning loop metrics
        """
        try:
            # Get feedback history
            history_key = f"feedback_history:{user_id}"
            history_data = self.redis_client.lrange(history_key, 0, -1)
            
            if not history_data:
                return {
                    'total_feedback': 0,
                    'avg_reward': 0.0,
                    'recent_actions': [],
                    'learning_rate': 0.0
                }
            
            # Parse history
            history = [json.loads(item) for item in history_data]
            
            # Calculate metrics
            rewards = [item['reward'] for item in history]
            actions = [item['action'] for item in history]
            
            avg_reward = sum(rewards) / len(rewards) if rewards else 0.0
            action_counts = {}
            for action in actions:
                action_counts[action] = action_counts.get(action, 0) + 1
            
            # Calculate learning rate (improvement over time)
            learning_rate = 0.0
            if len(rewards) >= 2:
                recent_avg = sum(rewards[-3:]) / min(3, len(rewards))
                early_avg = sum(rewards[:3:]) / min(3, len(rewards))
                learning_rate = recent_avg - early_avg
            
            return {
                'total_feedback': len(history),
                'avg_reward': avg_reward,
                'recent_actions': actions[-5:],  # Last 5 actions
                'action_distribution': action_counts,
                'learning_rate': learning_rate,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting learning loop metrics: {e}")
            return {}
    
    async def start_feedback_loop(self):
        """Start the main feedback processing loop"""
        logger.info("Starting feedback processing loop...")
        
        try:
            # Simple health check loop for now
            while True:
                await asyncio.sleep(60)  # Health check every minute
                logger.info("Feedback service is running and healthy")
                
        except Exception as e:
            logger.error(f"Feedback loop error: {e}")
            raise
    
    def close(self):
        """Close connections"""
        if self.kafka_producer:
            self.kafka_producer.close()
        if self.kafka_consumer:
            self.kafka_consumer.close()
        if self.redis_client:
            self.redis_client.close()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        logger.info("Starting Feedback Integration Service...")
        feedback_service = FeedbackIntegrationService()
        
        # Start the feedback processing loop
        asyncio.run(feedback_service.start_feedback_loop())
        
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service failed to start: {e}")
        sys.exit(1)
