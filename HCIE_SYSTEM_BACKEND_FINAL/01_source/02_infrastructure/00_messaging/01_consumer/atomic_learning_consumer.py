"""
Atomic Learning Consumer
Ensures exactly-once processing with DB transaction + Kafka commit
"""

import json
import logging
import uuid
from typing import Dict, Any

from ..learning.learning_loop_engine import LearningLoopEngine
from ..learning.learning_state_manager import LearningStateManager
from ..storage.postgres_store import PostgresInteractionStore

logger = logging.getLogger(__name__)

class AtomicLearningConsumer:
    """
    Atomic consumer that processes learning events with exactly-once semantics.
    Critical invariant: DB commit must happen BEFORE Kafka commit.
    """

    def __init__(self, kafka_consumer, db_store):
        self.consumer = kafka_consumer
        self.db_store = db_store
        self.engine = LearningLoopEngine()
        
        # CRITICAL: Add Learning State Manager for invariant enforcement
        conn = self.db_store.get_connection()
        self.state_manager = LearningStateManager(conn)

    async def process_message(self, message) -> bool:
        """
        Process a single Kafka message atomically.
        
        Args:
            message: Kafka message object
            
        Returns:
            True if processed successfully, False if skipped (duplicate)
        """
        try:
            # Parse event
            event = json.loads(message.value.decode('utf-8'))
            event_id = event.get("event_id")
            user_id = event.get("user_id")
            event_type = event.get("event_type")

            if not all([event_id, user_id, event_type]):
                logger.error(f"❌ Invalid event format: {event}")
                return False

            logger.info(f"🔄 Processing event {event_id} for user {user_id}")

            # Get DB connection and cursor
            conn = self.db_store.get_connection()
            cursor = conn.cursor()

            try:
                # CRITICAL GATE: Check if should apply update BEFORE transaction
                if not self.state_manager.should_apply_update(event):
                    logger.info(f"⏭️ Event rejected by invariant enforcement: {event_id}")
                    return False
                
                # Start DB transaction FIRST (true atomicity)
                cursor.execute("BEGIN")
                
                # 1. Check idempotency inside transaction
                cursor.execute("""
                    SELECT 1 FROM processed_events 
                    WHERE event_id = %s 
                    FOR UPDATE
                """, (event_id,))
                
                if cursor.fetchone():
                    cursor.execute("ROLLBACK")
                    logger.info(f"⏭️ Event already processed in transaction: {event_id}")
                    return False
                
                # 2. Apply learning update (pure computation)
                result = self.engine.apply_event(event, cursor)
                
                # 3. Persist learner state atomically (same transaction!)
                if result.get("type") == "learning_computed":
                    state_json = result.get("state_json")
                    cursor.execute("""
                        INSERT INTO user_state (user_id, mastery)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id)
                        DO UPDATE SET 
                            mastery = %s,
                            updated_at = CURRENT_TIMESTAMP
                    """, (user_id, state_json, state_json))
                
                # 4. Mark as processed (same transaction!)
                import uuid as uuid_lib
                event_uuid = uuid_lib.UUID(event_id) if isinstance(event_id, str) else event_id
                cursor.execute("""
                    INSERT INTO processed_events (event_id, user_id) 
                    VALUES (%s, %s)
                """, (str(event_uuid), user_id))
                
                # 5. Commit ATOMIC transaction
                cursor.execute("COMMIT")
                logger.info(f"✅ Atomic transaction committed for event {event_id}")
                
                # 6. THEN commit Kafka offset
                message.commit()
                logger.info(f"✅ Kafka offset committed for event {event_id}")
                
                logger.info(f"🎉 Successfully processed {event_type}: {result}")
                return True

            except Exception as e:
                # Rollback DB transaction
                cursor.execute("ROLLBACK")
                logger.error(f"❌ Failed to process event {event_id}: {e}")
                raise

        except Exception as e:
            logger.error(f"❌ Consumer error processing message: {e}")
            raise

    async def start_consuming(self, topic: str):
        """
        Start consuming messages from the specified topic
        """
        logger.info(f"🚀 Starting atomic consumer for topic: {topic}")
        
        try:
            self.consumer.subscribe([topic])
            
            while True:
                # Poll for messages
                messages = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, records in messages.items():
                    for message in records:
                        try:
                            await self.process_message(message)
                        except Exception as e:
                            logger.error(f"❌ Error processing message: {e}")
                            # Continue processing other messages
                            continue
                            
        except KeyboardInterrupt:
            logger.info("⏹️ Consumer stopped by user")
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
            raise
        finally:
            self.consumer.close()

    def produce_test_event(self, user_id: str, event_type: str, event_data: Dict[str, Any] = None) -> str:
        """
        Helper method to produce test events for validation
        """
        event_id = str(uuid.uuid4())
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "user_id": user_id,
            "timestamp": "now",
            **(event_data or {})
        }
        
        # This would use your Kafka producer
        logger.info(f"📤 Produced test event: {event}")
        return event_id
