"""
Task-related API endpoints
Handles task generation and submission
"""

import logging
from fastapi import APIRouter, HTTPException, Depends

from app.models.requests import TaskSubmission
from app.models.responses import TaskResponse
from app.services.task import TaskService
from app.services.kafka import KafkaService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

# Dependency injection
def get_task_service():
    # 🔥 RUNTIME CONVERGENCE: Use ServiceFactory for canonical authority
    from app.services.service_factory import ServiceFactory
    factory = ServiceFactory()
    return factory.get_task_service()

def get_kafka_service() -> KafkaService:
    """Get KafkaService with proper producer injection"""
    # Try DI first
    try:
        from app.infrastructure.di.dependency_injection import get_di_container
        from config.env import settings
        container = get_di_container()
        if container:
            try:
                messaging_deps = container.get_messaging_dependencies()
                if messaging_deps and messaging_deps.kafka_producer:
                    from app.services.kafka import KafkaService
                    return KafkaService(settings=settings, producer=messaging_deps.kafka_producer)
            except RuntimeError:
                logger.warning("DI Container not initialized, using fallback")
    except Exception as e:
        logger.warning(f"Failed to get KafkaService from DI: {e}")
    
    # Simple fallback: create producer directly
    try:
        from config.env import settings
        from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
        
        kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
        producer = kafka_factory.create_producer()
        
        if producer:
            from app.services.kafka import KafkaService
            return KafkaService(settings=settings, producer=producer)
    except Exception as e:
        logger.error(f"Failed to create KafkaService fallback: {e}")
        import traceback
        logger.error(f"Full error: {traceback.format_exc()}")
    
    raise RuntimeError("❌ Kafka producer not available - check configuration")

@router.get("/{user_id}", response_model=TaskResponse)
async def get_next_task(
    user_id: str,
    mode: str = "hcie",
    task_service: TaskService = Depends(get_task_service),
    kafka_service: KafkaService = Depends(get_kafka_service)
):
    """
    Get next task for user using HCIE engine with dual-mode support (CT/EdNet)
    """
    try:
        # Generate task using service with mode
        task_result = task_service.generate_task(user_id, policy_mode=mode)
        
        # Publish Kafka event
        kafka_service.publish_task_generated_event(
            user_id=user_id,
            task_data=task_result
        )
        
        # Convert to response model
        return TaskResponse(
            user_id=task_result["user_id"],
            task_id=task_result["task_id"],
            node_id=task_result["concept_id"],
            representation=task_result["representation"],
            question=f"Practice {task_result['concept_id']} with {task_result['representation']} format",
            difficulty=task_result["difficulty"],
            selection_metrics=task_result.get("selection_metrics", {}),
            timestamp=task_result["timestamp"],
            real_data=True
        )
        
    except Exception as e:
        logger.error(f"Error getting task for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate task")

@router.post("/submit")
async def submit_task(
    submission: TaskSubmission,
    task_service: TaskService = Depends(get_task_service),
    kafka_service: KafkaService = Depends(get_kafka_service)
):
    """
    Submit task and update mastery using HCIE engine with EdNet data
    """
    try:
        # Process submission using service
        result = task_service.process_submission(submission)
        
        # Publish Kafka events
        kafka_service.publish_task_submitted_event(
            user_id=submission.user_id,
            submission_data=submission,
            result_data=result
        )
        
        kafka_service.publish_mastery_updated_event(
            user_id=submission.user_id,
            concept_id=submission.node_id,
            learning_metrics=result.get("learning_metrics", {})
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit task")

@router.get("/history/{user_id}")
async def get_task_history(
    user_id: str,
    limit: int = 10,
    task_service: TaskService = Depends(get_task_service)
):
    """
    Get task history for a user
    """
    try:
        history = task_service.get_task_history(user_id, limit)
        return {"user_id": user_id, "history": history, "total": len(history)}
    except Exception as e:
        logger.error(f"Error getting task history for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task history")
