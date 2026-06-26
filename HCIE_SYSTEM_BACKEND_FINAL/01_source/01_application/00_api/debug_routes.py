"""
Debug API Routes for Phase 0 Testing
Provides visibility into system internals for end-to-end testing
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(tags=["debug"])

@router.get("/outbox/events")
async def get_outbox_events(limit: int = 10) -> Dict[str, Any]:
    """Get recent outbox events with full envelope for debugging"""
    try:
        from app.infrastructure.unit_of_work import get_transaction
        from app.infrastructure.outbox.outbox_pattern import OutboxEventStatus
        
        # This would need to be injected properly
        from config.env import settings
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        
        postgres_store = PostgresInteractionStore()
        
        # Test database connection using execute_read method
        postgres_store.execute_read("SELECT 1", fetch_one=True)
        
        with get_transaction(postgres_store) as tx:
            events = tx.db_store.execute_read(
                """
                SELECT id, event_id, event_type, topic, status, retry_count, 
                       error_message, created_at, published_at, envelope
                FROM outbox_event_envelopes
                ORDER BY created_at DESC
                LIMIT %s
                FOR UPDATE SKIP LOCKED
                """,
                (limit,)
            )
        
        return {
            "status": "success",
            "data": [
                {
                    "id": event["id"],
                    "event_id": event["event_id"],
                    "event_type": event["event_type"],
                    "topic": event["topic"],
                    "status": event["status"],
                    "retry_count": event["retry_count"],
                    "error_message": event["error_message"],
                    "created_at": event["created_at"].isoformat() if event["created_at"] else None,
                    "published_at": event["published_at"].isoformat() if event["published_at"] else None,
                    "envelope": event["envelope"] if isinstance(event["envelope"], dict) else json.loads(event["envelope"])
                }
                for event in events
            ]
        }
    except Exception as e:
        logger.error(f"❌ Failed to get outbox events: {e}")
        raise HTTPException(status_code=500, detail="Failed to get outbox events")

@router.get("/kafka/topics")
async def get_kafka_topics() -> Dict[str, Any]:
    """Get Kafka topics for debugging"""
    try:
        from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
        from config.env import settings
        
        kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
        
        # This would need to be implemented in KafkaFactory
        # For now, return known topics
        topics = [
            "hcie.auth.user_registered",
            "hcie.auth.user_logged_in",
            "hcie.auth.token_refreshed",
            "hcie.auth.user_profile_updated",
            "hcie.auth.user_logged_out",
            "hcie.auth.password_changed"
        ]
        
        return {
            "status": "success",
            "data": {
                "topics": topics,
                "bootstrap_servers": settings.kafka_bootstrap_servers
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to get Kafka topics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Kafka topics")

@router.get("/redis/processed-events")
async def get_processed_events_count() -> Dict[str, Any]:
    """Get count of processed events in Redis"""
    try:
        from storage.redis_store.redis_store import RedisFeatureStore
        from config.env import settings
        
        redis_store = RedisFeatureStore(settings)
        
        # Count processed events
        pattern = "processed_events:*"
        keys = redis_store.redis_client.keys(pattern)
        
        return {
            "status": "success",
            "data": {
                "processed_events_count": len(keys),
                "sample_keys": [key.decode() for key in keys[:5]] if keys else []
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to get processed events count: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processed events count")

@router.get("/system/health-detailed")
async def get_detailed_health() -> Dict[str, Any]:
    """Get detailed system health for debugging"""
    try:
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Check API
        try:
            health_status["components"]["api"] = {"status": "healthy", "message": "API is running"}
        except Exception as e:
            health_status["components"]["api"] = {"status": "unhealthy", "message": str(e)}
        
        # Check Database
        try:
            from app.infrastructure.unit_of_work import get_transaction
            from storage.postgres_store.interaction_store import PostgresInteractionStore
            from config.env import settings
            
            postgres_store = PostgresInteractionStore()
            with get_transaction(postgres_store) as tx:
                tx.db_store.execute_read("SELECT 1")
            
            health_status["components"]["database"] = {"status": "healthy", "message": "Database is accessible"}
        except Exception as e:
            health_status["components"]["database"] = {"status": "unhealthy", "message": str(e)}
        
        # Check Redis
        try:
            from storage.redis_store.redis_store import RedisFeatureStore
            from config.env import settings
            
            redis_store = RedisFeatureStore(settings)
            redis_store.redis_client.ping()
            
            health_status["components"]["redis"] = {"status": "healthy", "message": "Redis is accessible"}
        except Exception as e:
            health_status["components"]["redis"] = {"status": "unhealthy", "message": str(e)}
        
        # Check Kafka
        try:
            from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
            from config.env import settings
            
            kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
            producer = kafka_factory.create_producer()
            
            health_status["components"]["kafka"] = {"status": "healthy", "message": "Kafka is accessible"}
        except Exception as e:
            health_status["components"]["kafka"] = {"status": "unhealthy", "message": str(e)}
        
        # Overall status
        unhealthy_components = [name for name, comp in health_status["components"].items() if comp["status"] == "unhealthy"]
        
        if unhealthy_components:
            health_status["overall_status"] = "unhealthy"
            health_status["unhealthy_components"] = unhealthy_components
        else:
            health_status["overall_status"] = "healthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Failed to get detailed health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get detailed health")

@router.post("/test/event")
async def create_test_event(event_type: str = "user_registered") -> Dict[str, Any]:
    """Create a test event for debugging"""
    try:
        import uuid
        from app.infrastructure.outbox.outbox_pattern import OutboxPattern, OutboxEvent
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        from config.env import settings
        
        # Create test event
        test_event = OutboxEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            payload={
                "user_id": f"test-user-{int(datetime.utcnow().timestamp())}",
                "email": f"test-{int(datetime.utcnow().timestamp())}@example.com",
                "test": True
            },
            topic=f"hcie.auth.{event_type}"
        )
        
        # Save to outbox
        postgres_store = PostgresStore(settings.database_url)
        outbox_pattern = OutboxPattern(postgres_store)
        
        event_id = outbox_pattern.save_event(test_event)
        
        logger.info(f"🧪 Created test event: {event_id}")
        
        return {
            "status": "success",
            "data": {
                "event_id": event_id,
                "event_type": event_type,
                "message": "Test event created in outbox"
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to create test event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create test event")

@router.delete("/debug/clean")
async def clean_test_data() -> Dict[str, Any]:
    """Clean test data (for testing only)"""
    try:
        from app.infrastructure.unit_of_work import get_transaction
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        from config.env import settings
        
        postgres_store = PostgresInteractionStore()
        
        with get_transaction(postgres_store) as tx:
            # Clean test events
            result = tx.db_store.execute_write(
                """
                DELETE FROM outbox_event_envelopes
                WHERE event_type LIKE '%test%'
                OR payload::text LIKE '%test%'
                """
            )
        
        # Clean Redis test data
        try:
            from storage.redis_store.redis_store import RedisFeatureStore
            redis_store = RedisFeatureStore(settings)
            
            # Delete test processed events
            pattern = "processed_events:*"
            keys = redis_store.redis_client.keys(pattern)
            for key in keys:
                if b'test' in key:
                    redis_store.redis_client.delete(key)
        except Exception as e:
            logger.warning(f"⚠️ Failed to clean Redis test data: {e}")
        
        logger.info(f"🧹 Cleaned {result} test events")
        
        return {
            "status": "success",
            "data": {
                "cleaned_events": result,
                "message": "Test data cleaned"
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to clean test data: {e}")
        raise HTTPException(status_code=500, detail="Failed to clean test data")

# ===== RESEARCH DEBUG ENDPOINTS (from old debug.py) =====

class ResetUserRequest(BaseModel):
    user_id: str

@router.post("/reset_user")
async def reset_user_state(request: ResetUserRequest):
    """Reset a user's state in Redis for clean experiments"""
    try:
        from app.services.service_factory import get_service_factory
        service_factory = get_service_factory()
        task_service = service_factory.get_task_service()
        
        # Delete user's mastery data from Redis
        user_id = request.user_id
        redis_store = task_service.redis_store
        
        # Try to delete the user's mastery keys
        try:
            # Delete Lyapunov state
            lyapunov_key = f"lyapunov:{user_id}:*"
            redis_store.redis.delete(*redis_store.redis.keys(lyapunov_key))
            
            # Delete Bayesian state  
            bayesian_key = f"bayesian:{user_id}:*"
            redis_store.redis.delete(*redis_store.redis.keys(bayesian_key))
            
            # Delete Kalman state
            kalman_key = f"kalman:{user_id}:*"
            redis_store.redis.delete(*redis_store.redis.keys(kalman_key))
            
            # Reset bandit cumulative regret
            if hasattr(task_service, 'bandit'):
                task_service.bandit.reset_cumulative_regret(user_id)
            
            logger.info(f"✅ Reset state for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Partial reset for user {user_id}: {e}")
        
        return {"success": True, "message": f"Reset state for {user_id}"}
        
    except Exception as e:
        logger.error(f"Failed to reset user {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bandit_state/{user_id}")
async def debug_bandit_state(user_id: str):
    """Debug bandit algorithm state - Returns alpha/beta parameters, regret, and selection metrics"""
    try:
        from app.services.service_factory import get_service_factory
        service_factory = get_service_factory()
        debug_service = service_factory.get_debug_service()
        
        return debug_service.get_bandit_state(user_id)
        
    except Exception as e:
        logger.error(f"Error debugging bandit state: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging bandit state: {str(e)}")

@router.get("/signals/{user_id}")
async def debug_signals(user_id: str, limit: int = 10):
    """Debug signal extraction for recent interactions"""
    try:
        from app.services.service_factory import get_service_factory
        service_factory = get_service_factory()
        debug_service = service_factory.get_debug_service()
        
        return debug_service.get_signal_state(user_id, limit)
        
    except Exception as e:
        logger.error(f"Error debugging signals: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging signals: {str(e)}")

@router.get("/state/{user_id}")
async def debug_complete_state(user_id: str):
    """Complete debug state for a user - Combines bandit, mastery, and signals"""
    try:
        from app.services.service_factory import get_service_factory
        service_factory = get_service_factory()
        debug_service = service_factory.get_debug_service()
        
        return debug_service.get_complete_state(user_id)
        
    except Exception as e:
        logger.error(f"Error getting complete state: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting complete state: {str(e)}")

@router.get("/mastery/{user_id}")
async def debug_mastery_state(user_id: str):
    """Debug endpoint to inspect user mastery state"""
    try:
        from app.services.service_factory import get_service_factory
        service_factory = get_service_factory()
        debug_service = service_factory.get_debug_service()
        
        return debug_service.get_mastery_state(user_id)
        
    except Exception as e:
        logger.error(f"Error debugging mastery state: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging mastery state: {str(e)}")

@router.get("/learner/{user_id}")
async def debug_learner_state(user_id: str):
    """Debug endpoint to inspect learner state"""
    try:
        from app.services.service_factory import get_service_factory
        service_factory = get_service_factory()
        debug_service = service_factory.get_debug_service()
        
        return debug_service.get_learner_state(user_id)
        
    except Exception as e:
        logger.error(f"Error debugging learner state: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging learner state: {str(e)}")

class TestTaskAttemptRequest(BaseModel):
    user_id: str
    session_id: str
    task_id: str
    concept_id: str
    response: str
    correct: bool

@router.post("/test/task-attempt")
async def test_task_attempt(request: TestTaskAttemptRequest):
    """Test endpoint for B3.1a: Submit task attempt via outbox-backed cognition"""
    try:
        from core.session.brain_bridge_service import BrainBridgeService
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        from config.env import settings
        
        # B3.6: Generate trace context at API entry point
        try:
            from core.telemetry.trace_context import create_trace_context, TraceContext
            trace_context = create_trace_context(
                user_id=request.user_id,
                session_id=request.session_id,
                source="api",
                component="debug_endpoint"
            )
            logger.info(f"🔍 Generated trace context: {trace_context.trace_id}")
        except ImportError:
            trace_context = None
            logger.warning("⚠️ Trace context not available")
        
        # Initialize database store
        postgres_store = PostgresInteractionStore()
        
        # Initialize BrainBridgeService with outbox support (B3.1a: db_store required)
        brain_bridge = BrainBridgeService(
            db_store=postgres_store,
            event_bus=None  # Will use outbox pattern without event bus for now
        )
        
        # Process interaction via outbox with trace context
        result = brain_bridge.process_interaction(
            user_id=request.user_id,
            concept_id=request.concept_id,
            correct=request.correct,
            response_time=1.0,
            trace_context=trace_context
        )
        
        logger.info(f"🧪 Test task attempt processed: {result}")
        
        return {
            "status": "success",
            "data": {
                "user_id": request.user_id,
                "task_id": request.task_id,
                "concept_id": request.concept_id,
                "correct": request.correct,
                "cognition_result": result,
                "trace_id": result.get("trace_id") if result else None
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to test task attempt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test task attempt: {str(e)}")
