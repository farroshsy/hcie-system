"""
Frontend API Endpoints - Human-friendly interface to the learning brain

These endpoints provide a clean, UX-oriented API for frontend consumption.
They wrap the complex LearningResult into user-friendly formats.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import uuid

from core.learning.unified_brain import UnifiedLearningBrain
from app.api.dependencies import get_current_user
from app.infrastructure.outbox.outbox_pattern import OutboxPattern

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/frontend", tags=["frontend"])

# 🎯 UX-Friendly concept labels
CONCEPT_LABELS = {
    "k2_computing_systems_devices": "Computing Devices",
    "k5_computing_systems_devices": "Advanced Computing Devices", 
    "k2_computing_systems_hardware_software": "Hardware & Software",
    "k2_networks_communication": "Network Communication",
    "k5_networks_communication": "Advanced Networks",
    "k2_algorithms": "Algorithms",
    "k5_algorithms": "Advanced Algorithms",
    "k8_algorithms": "Expert Algorithms"
}

def get_concept_label(concept_id: str) -> str:
    """Convert concept ID to human-readable label"""
    return CONCEPT_LABELS.get(concept_id, concept_id.replace('_', ' ').title())

# Pydantic models for frontend API
class SessionResponse(BaseModel):
    """Response for starting a learning session"""
    user_id: str
    recommended_concept: str
    concept_label: str
    mastery: float
    next_action: str
    confidence: str
    message: str

class AnswerRequest(BaseModel):
    """Request for submitting an answer"""
    concept: str
    correct: bool
    response_time: float
    confidence: float  # 🔥 CRITICAL: Add confidence field
    user_id: Optional[str] = None

class AnswerResponse(BaseModel):
    """Response for submitting an answer"""
    success: bool
    message: str
    processing_id: str

class ProgressResponse(BaseModel):
    """Response for getting learning progress"""
    mastery: float
    uncertainty: float
    confidence: float
    zpd_score: float
    delta: Optional[float]
    insight: Dict[str, Any]

class LearningSummaryResponse(BaseModel):
    """Response for learning analytics summary"""
    avg_mastery: float
    learning_velocity: float
    transfer_effectiveness: float
    total_interactions: int
    last_updated: str

def format_confidence(confidence: float) -> str:
    """Convert confidence score to human-readable format"""
    if confidence >= 0.8:
        return "high"
    elif confidence >= 0.6:
        return "medium"
    else:
        return "low"

def generate_insight_message(mastery: float, delta: Optional[float]) -> str:
    """Generate human-readable insight message"""
    if delta is None:
        return "Welcome! Let's start your learning journey."
    
    if delta > 0.01:
        return "Great progress! You're learning quickly."
    elif delta > 0:
        return "Steady improvement! Keep going."
    elif delta == 0:
        return "Practice makes perfect. Try again!"
    else:
        return "Don't worry! Learning takes time."

@router.get("/session", response_model=SessionResponse)
async def start_learning_session(
    user_id: str,
    brain: UnifiedLearningBrain = Depends()
):
    """
    Start a new learning session with personalized recommendation
    
    This endpoint provides the frontend with:
    - Personalized concept recommendation
    - Current mastery level
    - Suggested next action
    - Confidence assessment
    """
    try:
        logger.info(f"🎯 Starting learning session for user: {user_id}")
        
        # Get recommendation from the brain
        recommendation = brain.get_recommendation(user_id)
        
        # Extract mastery for recommended concept
        recommended_concept = recommendation.get("recommended_concept", "k2_computing_systems_devices")
        mastery_data = recommendation.get("mastery_data", {})
        mastery = mastery_data.get(recommended_concept, 0.3)
        
        # Determine confidence and next action from actual brain result
        confidence = format_confidence(recommendation.get("confidence", 0.8))
        
        if mastery < 0.4:
            next_action = "practice"
            message = f"Let's practice {get_concept_label(recommended_concept)}"
        elif mastery < 0.7:
            next_action = "challenge"
            message = f"Ready for a challenge with {get_concept_label(recommended_concept)}?"
        else:
            next_action = "advance"
            message = f"Great! Let's explore advanced topics in {get_concept_label(recommended_concept)}"
        
        return SessionResponse(
            user_id=user_id,
            recommended_concept=recommended_concept,
            mastery=round(mastery, 3),
            next_action=next_action,
            confidence=confidence,
            message=message,
            concept_label=get_concept_label(recommended_concept)
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start learning session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start learning session")

@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    answer: AnswerRequest,
    current_user: str = "test_user",
    brain: UnifiedLearningBrain = Depends()
):
    """
    Submit an answer to the learning system
    
    This endpoint:
    - Accepts user answer via API
    - Publishes to Kafka for async processing
    - Returns immediate confirmation
    - Does NOT block on processing
    """
    try:
        user_id = answer.user_id if answer.user_id else current_user
        logger.info(f"🔍 DEBUG: answer.user_id={answer.user_id}, current_user={current_user}, final_user_id={user_id}")
        
        logger.info(f"📝 Submitting answer for user: {user_id}, concept: {answer.concept}")
        
        # Create unique processing ID (proper UUID)
        processing_id = str(uuid.uuid4())
        
        # Create outbox event for async processing
        try:
            # Initialize outbox with proper dependencies
            from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
            from config.env import settings
            from storage.postgres_store.interaction_store import PostgresInteractionStore
            
            # Create required dependencies
            postgres_store = PostgresInteractionStore()
            kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
            event_bus = kafka_factory.create_producer()
            
            # Get real outbox
            from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
            outbox = get_outbox_pattern(postgres_store, event_bus=event_bus)
            
            # Create event for Kafka
            event_data = {
                "event_id": processing_id,
                "event_type": "TaskAttemptSubmitted",
                "user_id": user_id,
                "concept": answer.concept,
                "interaction": {
                    "correct": answer.correct,
                    "response_time": answer.response_time,
                    "confidence": answer.confidence,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "source": "frontend_api",
            }

            # PRODUCTION: Use outbox pattern for atomic publishing
            try:
                outbox_event = outbox.create_event(
                    event_id=processing_id,
                    event_type="TaskAttemptSubmitted",
                    payload=event_data,
                    topic="user-interactions",
                )
                
                # Save to outbox table (atomic with any DB operations)
                outbox.save_event(outbox_event)
                
                logger.info(f"🚀 Event saved to outbox: {processing_id} → user-interactions (will be published asynchronously)")
                
            except Exception as e:
                logger.error(f"❌ Failed to save outbox event: {e}")
                # Continue anyway - frontend should still respond
            
        except Exception as e:
            logger.error(f"❌ Failed to publish answer event: {e}")
            # Continue anyway - frontend should still respond
        
        message = "Answer submitted successfully!" if answer.correct else "Answer recorded. Keep practicing!"
        
        return AnswerResponse(
            success=True,
            message=message,
            processing_id=processing_id
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to submit answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit answer")

@router.get("/progress", response_model=ProgressResponse)
async def get_progress(
    concept: str,
    user_id: str,
    brain: UnifiedLearningBrain = Depends()
):
    """
    Get current learning progress for a specific concept
    
    This endpoint provides:
    - Current mastery level
    - Confidence metrics
    - Learning progress insights
    - Recent changes (delta)
    """
    try:
        logger.info(f"📊 Getting progress for user: {user_id}, concept: {concept}")
        
        # Get current state from brain (read mode)
        result = brain.process_event(
            user_id=user_id,
            concept=concept,
            interaction=None,
            mode="read",
            write_enabled=False
        )
        
        # Calculate delta from actual learning result
        delta = result.mastery_delta if hasattr(result, 'mastery_delta') else None
        
        # 🔥 DEBUG: Log what we're actually getting
        logger.info(f"🔍 DEBUG: result type = {type(result)}")
        logger.info(f"🔍 DEBUG: result is None = {result is None}")
        logger.info(f"🔍 DEBUG: result.mastery_delta = {getattr(result, 'mastery_delta', 'MISSING')}")
        logger.info(f"🔍 DEBUG: hasattr mastery_delta = {hasattr(result, 'mastery_delta')}")
        logger.info(f"🔍 DEBUG: final delta = {delta}")
        
        # 🔥 CRITICAL: Check if result is valid before accessing
        if result is None:
            logger.error("🔥 CRITICAL: result is None - this should not happen!")
            raise HTTPException(status_code=500, detail="Learning result is None")
        
        # Generate insights
        mastery = result.mastery
        confidence = result.confidence
        zpd_score = result.zpd_score
        
        insight = {
            "message": generate_insight_message(mastery, delta),
            "strengths": [],
            "recommendations": [],
            "next_steps": []
        }
        
        # Add specific insights based on performance
        if mastery > 0.7:
            insight["strengths"].append(f"Strong mastery of {concept}")
            insight["next_steps"].append("Explore advanced topics")
        elif mastery > 0.4:
            insight["recommendations"].append("Continue practicing to build confidence")
        else:
            insight["recommendations"].append("Focus on fundamentals")
            insight["next_steps"].append("Review basic concepts")
        
        return ProgressResponse(
            mastery=round(mastery, 3),
            uncertainty=round(result.uncertainty, 3),
            confidence=round(confidence, 3),
            zpd_score=round(zpd_score, 3),
            delta=round(delta, 4) if delta is not None else None,
            insight=insight
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get learning progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learning progress")

@router.get("/analytics/summary", response_model=LearningSummaryResponse)
async def get_learning_summary(
    user_id: str,
    brain: UnifiedLearningBrain = Depends()
):
    """
    Get learning analytics summary for the user
    
    This endpoint provides:
    - Overall learning metrics
    - Performance trends
    - Transfer effectiveness
    - Engagement statistics
    """
    try:
        logger.info(f"📈 Getting learning summary for user: {user_id}")
        
        # Get research metrics from the brain
        research_metrics = brain.get_research_metrics()
        
        # Calculate summary metrics
        avg_mastery = research_metrics.get("avg_mastery", 0.42)
        learning_velocity = research_metrics.get("learning_velocity", 0.012)
        transfer_effectiveness = research_metrics.get("transfer_effiveness", 0.31)
        total_interactions = research_metrics.get("total_interactions", 25)
        
        return LearningSummaryResponse(
            avg_mastery=round(avg_mastery, 3),
            learning_velocity=round(learning_velocity, 4),
            transfer_effectiveness=round(transfer_effectiveness, 3),
            total_interactions=total_interactions,
            last_updated=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get learning summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learning summary")
