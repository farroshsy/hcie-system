"""
UX Learning API - User-friendly learning endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging

from app.utils.api_responses.response_translator import ResponseTranslator
from app.api.dependencies.learning import get_task_service
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/learning", tags=["ux"])

class SubmitAnswerRequest(BaseModel):
    """UX-friendly answer submission"""
    task_id: str
    answer: str
    response_time: Optional[float] = None


@router.get("/next-task")
async def get_next_task(
    user_id: str = Depends(lambda: "current_user"),  # TODO: Replace with real auth
    task_service = Depends(get_task_service)  # MIGRATION: Explicit dependency (was inline ServiceFactory)
) -> Dict[str, Any]:
    """
    Get next recommended task in UX-friendly format
    """
    try:
        # Use existing decision endpoint but simplify response
        decision_result = task_service.generate_task(user_id=user_id)
        
        # Translate to UX-friendly format
        return {
            "task_id": decision_result.get("task_id", "task_123"),
            "concept": decision_result.get("concept_id", "k2_algorithms"),
            "difficulty": decision_result.get("difficulty", 0.5),
            "question": decision_result.get("question", "What is an algorithm?"),
            "type": "multiple_choice",
            "options": decision_result.get("options", ["A", "B", "C", "D"]),
            "estimated_time": decision_result.get("estimated_time", 5.0)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting next task: {e}")
        raise HTTPException(status_code=500, detail="Failed to get next task")

@router.post("/submit")
async def submit_answer(
    request: SubmitAnswerRequest,
    user_id: str = Depends(lambda: "current_user"),  # TODO: Replace with real auth
    task_service = Depends(get_task_service)  # MIGRATION: Explicit dependency (was inline ServiceFactory)
) -> Dict[str, Any]:
    """
    Submit answer and get UX-friendly feedback
    """
    try:
        
        # 🚀 PHASE 1: Convert to event emission (async processing)
        import uuid
        import time
        
        learning_event = {
            "event_id": str(uuid.uuid4()),
            "user_id": user_id,
            "concept": "k2_algorithms",  # TODO: Extract from task
            "interaction": {
                "correct": request.answer == "A",  # TODO: Real answer checking
                "response_time": request.response_time or 5.0
            },
            "timestamp": time.time(),
            "task_id": request.task_id,
            "source": "api_submit"
        }
        
        # 🔥 Use outbox pattern for atomic event publishing
        try:
            from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
            from app.infrastructure.unit_of_work import get_transaction
            
            # Get outbox instance
            outbox = get_outbox_pattern(task_service.postgres_store)
            
            # Atomic transaction: save event to outbox
            with get_transaction(task_service.postgres_store) as tx:
                event_id = outbox.save_event(
                    outbox.create_event(
                        event_id=learning_event["event_id"],
                        event_type="learning_interaction",
                        topic="learning_events",
                        payload=learning_event,
                        partition_key=f"{user_id}_k2_algorithms"
                    ),
                    transaction=tx
                )
            
            logger.info(f"🚀 Learning event accepted: {learning_event['event_id']}")
            
            # ✅ ASYNC RESPONSE: Return acceptance, not result
            ux_response = {
                "status": "accepted",
                "event_id": learning_event["event_id"],
                "message": "Learning event submitted for processing",
                "processing": "async",
                "estimated_completion": "2-5 seconds"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to submit learning event: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit learning event")
        
        return ux_response
        
    except Exception as e:
        logger.error(f"❌ Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit answer")
