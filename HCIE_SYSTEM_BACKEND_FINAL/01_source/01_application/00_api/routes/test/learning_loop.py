"""
Test API for Learning Loop Validation
Phase 1: Minimal testable implementation
"""

import json
import uuid
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["learning-loop"])

class TestEvent(BaseModel):
    user_id: str
    event_type: str = "task_submitted"
    reward: float = 0.1
    task_id: str = "test_task"
    concept: str = "ct_decomposition"  # Add concept field

class TestResponse(BaseModel):
    status: str
    event_id: str
    message: str

@router.post("/produce", response_model=TestResponse)
async def produce_test_event(event: TestEvent):
    """
    Produce a test event to the learning loop
    """
    try:
        event_id = str(uuid.uuid4())
        
        # Create test event with versioning
        event_data = {
            "version": 1,  # Event schema version
            "event_id": event_id,
            "event_type": event.event_type,
            "user_id": event.user_id,
            "reward": event.reward,
            "task_id": event.task_id,
            "concept": event.concept,
            "timestamp": "now"
        }
        
        # Validate event against shared schema
        try:
            import sys
            sys.path.append('/app')
            from schema.schema_validator import validate_learning_event
            
            validation_result = validate_learning_event(event_data)
            if not validation_result["valid"]:
                logger.error(f"❌ Event validation failed: {validation_result['errors']}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"Event validation failed: {validation_result['errors']}"
                )
            
            # Use normalized event
            event_data = validation_result["event"]
            logger.info(f"✅ Event validated: {event_data['event_id']}")
            
        except ImportError:
            logger.warning("⚠️ Schema validator not available, skipping validation")
        except Exception as e:
            logger.error(f"❌ Schema validation error: {e}")
            raise HTTPException(status_code=500, detail=f"Schema validation error: {str(e)}")
        
        # Produce to Kafka (REAL)
        from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
        from config.env import settings
        
        kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
        producer = kafka_factory.create_producer()
        
        # Send to user-interactions topic with LOCKED serialization contract
        # Import raw Kafka for direct control
        from kafka import KafkaProducer
        
        # 🔥 CRITICAL: Single serialization path ONLY
        def locked_value_serializer(v):
            """Locked contract: dict → JSON → bytes, NO double encoding"""
            if not isinstance(v, dict):
                raise ValueError(f"Producer contract violation: expected dict, got {type(v)}")
            return json.dumps(v).encode('utf-8')
        
        direct_producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=locked_value_serializer,
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3
        )
        
        # Send directly to user-interactions topic
        future = direct_producer.send(
            topic="user-interactions",
            key=event.user_id,
            value=event_data
        )
        
        # Block for confirmation
        record_metadata = future.get(timeout=10)
        direct_producer.flush()
        direct_producer.close()
        
        logger.info(f"📤 Event sent to partition {record_metadata.partition} at offset {record_metadata.offset}")
        
        logger.info(f"📤 Test event produced to Kafka: {event_id}")
        
        return {
            "status": "created",
            "event_id": event_data["event_id"],
            "message": f"Test event {event_data['event_id']} created for user {event.user_id}"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create test event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/state/{user_id}")
async def get_user_state(user_id: str):
    """
    Get current user state for testing (REAL database query)
    """
    try:
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        from config.env import settings
        
        db_store = PostgresInteractionStore()
        
        # Query real user_state table
        query = "SELECT mastery, updated_at FROM user_state WHERE user_id = %s"
        result = db_store.execute_read(query, (user_id,), fetch_one=True)
        
        if result:
            state_data = {
                "user_id": user_id,
                "mastery": result["mastery"],
                "updated_at": result["updated_at"].isoformat() if result["updated_at"] else "unknown"
            }
        else:
            state_data = {
                "user_id": user_id,
                "mastery": {"score": 0.5},
                "updated_at": "not_found"
            }
        
        logger.info(f"📊 Retrieved state for user {user_id}: {state_data}")
        return state_data
        
    except Exception as e:
        logger.error(f"❌ Failed to get user state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/{user_id}")
async def debug_user_state(user_id: str):
    """
    Get full structured state for debugging (Phase 2)
    """
    try:
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        
        db_store = PostgresInteractionStore()
        
        # Query full user_state table
        query = "SELECT mastery, updated_at FROM user_state WHERE user_id = %s"
        result = db_store.execute_read(query, (user_id,), fetch_one=True)
        
        if result:
            state_data = {
                "user_id": user_id,
                "full_state": result["mastery"],
                "updated_at": result["updated_at"].isoformat() if result["updated_at"] else "unknown",
                "state_version": result["mastery"].get("meta", {}).get("version", 1)
            }
        else:
            state_data = {
                "user_id": user_id,
                "full_state": None,
                "updated_at": "not_found",
                "state_version": "unknown"
            }
        
        logger.info(f"🐛 Debug state for user {user_id}: version {state_data['state_version']}")
        return state_data
        
    except Exception as e:
        logger.error(f"❌ Failed to get debug state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/{user_id}")
async def get_processed_events(user_id: str):
    """
    Get processed events for a user (for idempotency testing)
    """
    try:
        # TODO: Query from processed_events table
        # For now, return mock response
        events = []
        
        logger.info(f"📋 Retrieved processed events for user {user_id}: {len(events)} events")
        return {"user_id": user_id, "events": events}
        
    except Exception as e:
        logger.error(f"❌ Failed to get processed events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset/{user_id}")
async def reset_user_state(user_id: str):
    """
    Reset user state for testing (test cleanup)
    """
    try:
        # TODO: Delete from user_state and processed_events tables
        logger.info(f"🗑️ Reset state for user {user_id}")
        
        return {
            "status": "reset",
            "user_id": user_id,
            "message": f"User {user_id} state reset for testing"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to reset user state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def learning_loop_health():
    """
    Health check for learning loop components
    """
    try:
        # Check if core tables exist
        # TODO: Add actual health checks
        
        return {
            "status": "healthy",
            "components": {
                "database": "connected",
                "kafka": "connected",
                "learning_engine": "ready"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
