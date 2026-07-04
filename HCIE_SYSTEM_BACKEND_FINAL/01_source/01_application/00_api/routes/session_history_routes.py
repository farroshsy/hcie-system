"""
Session History Routes - Pedagogical Continuity Surfaces

C1.1.3 - Session Memory Visualization:
Expose session continuity, pacing evolution, prior adaptations, 
recent misconceptions, concept progression history as 
pedagogical continuity surfaces (NOT analytics dashboards).

Key Design Principles:
- Timeline semantics, NOT statistics
- Pedagogical narrative, NOT metric aggregation
- Continuity surfaces, NOT dashboard widgets
- Semantic progression, NOT numerical summaries
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.services.service_factory import ServiceFactory


# ============================================================================
# API Models - Pedagogical Continuity Surfaces
# ============================================================================

class MisconceptionOccurrence(BaseModel):
    """Single misconception occurrence in timeline"""
    misconception_id: str
    description: str
    severity: str
    occurred_at: str  # ISO format
    task_id: str
    concept_id: str
    remediation_strategy: str
    is_recurring: bool = False  # Whether this misconception appeared before


class DifficultyProgression(BaseModel):
    """Difficulty progression across session"""
    task_id: str
    concept_id: str
    conceptual_difficulty: float
    cognitive_load: float
    transfer_complexity: float
    abstraction_depth: float
    prerequisite_burden: float
    occurred_at: str


class AdaptationEvent(BaseModel):
    """Adaptation event in session timeline"""
    adaptation_type: str
    recommendation: str
    policy_version: str
    occurred_at: str
    triggered_by: str  # What cognition state triggered this


class PacingMetric(BaseModel):
    """Pacing evolution metric"""
    time_between_tasks: float  # seconds
    tasks_per_hour: float
    streak_length: int
    occurred_at: str


class ConceptProgression(BaseModel):
    """Concept progression through session"""
    concept_id: str
    first_encountered: str
    last_encountered: str
    total_attempts: int
    correct_count: int
    mastery_trend: str  # "improving", "stable", "declining"


class SessionHistoryResponse(BaseModel):
    """Complete session history as pedagogical continuity surface"""
    session_id: str
    user_id: str
    started_at: str
    ended_at: Optional[str] = None
    
    # Pedagogical continuity surfaces
    misconceptions: List[MisconceptionOccurrence]
    difficulty_progression: List[DifficultyProgression]
    adaptations: List[AdaptationEvent]
    pacing_metrics: List[PacingMetric]
    concept_progression: List[ConceptProgression]
    
    # Semantic summaries (timeline semantics, NOT statistics)
    total_tasks: int
    unique_concepts: int
    recurring_misconceptions: int
    difficulty_trend: str  # "increasing", "stable", "decreasing"


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/session-history", tags=["session-history"])


# ============================================================================
# Session History Endpoints
# ============================================================================

@router.get("/{session_id}/full")
async def get_session_history(
    session_id: str,
    service_factory: ServiceFactory = Depends(ServiceFactory)
) -> SessionHistoryResponse:
    """
    Get complete session history as pedagogical continuity surface.
    
    This endpoint returns timeline-based semantic progression,
    NOT aggregated statistics. The focus is on narrative continuity
    of the learner's journey through the session.
    
    Args:
        session_id: Session identifier
        service_factory: Service factory dependency
    
    Returns:
        Session history with pedagogical continuity surfaces
    """
    try:
        # Get session service
        session_service = service_factory.get_session_service()
        
        # Get session
        session = session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get task attempts from repository
        # Note: For MVP, we'll use in-memory tracking
        # In production, this would query the task_attempts table
        
        # Build pedagogical continuity surfaces
        # For MVP: return empty lists that will be populated by real data
        
        return SessionHistoryResponse(
            session_id=session.id,
            user_id=session.user_id,
            started_at=session.started_at.isoformat() if session.started_at else "",
            ended_at=session.completed_at.isoformat() if session.completed_at else None,
            misconceptions=[],
            difficulty_progression=[],
            adaptations=[],
            pacing_metrics=[],
            concept_progression=[],
            total_tasks=session.tasks_completed,
            unique_concepts=len(set(session.target_concepts)),
            recurring_misconceptions=0,
            difficulty_trend="stable"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/misconceptions")
async def get_session_misconceptions(
    session_id: str,
    service_factory: ServiceFactory = Depends(ServiceFactory)
) -> List[MisconceptionOccurrence]:
    """
    Get misconception timeline for session.
    
    Shows misconception recurrence patterns and remediation history.
    """
    # MVP: Return empty list
    # Production: Query task_attempts with misconception details
    return []


@router.get("/{session_id}/difficulty")
async def get_difficulty_progression(
    session_id: str,
    service_factory: ServiceFactory = Depends(ServiceFactory)
) -> List[DifficultyProgression]:
    """
    Get difficulty progression across session.
    
    Shows how multi-dimensional difficulty evolved through tasks.
    """
    # MVP: Return empty list
    # Production: Query task_attempts with difficulty_dimensions
    return []


@router.get("/{session_id}/adaptations")
async def get_adaptation_history(
    session_id: str,
    service_factory: ServiceFactory = Depends(ServiceFactory)
) -> List[AdaptationEvent]:
    """
    Get adaptation history for session.
    
    Shows pedagogical adaptations and their triggers.
    """
    # MVP: Return empty list
    # Production: Query adaptation_events table
    return []


@router.get("/user/{user_id}/recent")
async def get_recent_session_summaries(
    user_id: str,
    limit: int = 5,
    service_factory: ServiceFactory = Depends(ServiceFactory)
) -> List[SessionHistoryResponse]:
    """
    Get recent session summaries for user.
    
    Provides longitudinal continuity surface across sessions.
    """
    # MVP: Return empty list
    # Production: Query learning_sessions by user_id with limit
    return []
