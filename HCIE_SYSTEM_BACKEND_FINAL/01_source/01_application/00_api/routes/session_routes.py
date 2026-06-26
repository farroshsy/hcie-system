"""
Session Routes - C1.1.2 Session Interaction Loop

These routes provide session lifecycle management for the frontend.
Validates longitudinal runtime coherence, pacing memory, learner continuity.

C1.3 - Task Semantics Hardening: Integrated misconception ontology for
pedagogical semantic richness and interpretability.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

from app.api.dependencies.learning import get_session_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sessions", tags=["sessions"])

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    status: str
    started_at: Optional[str] = None
    paused_at: Optional[str] = None
    completed_at: Optional[str] = None
    current_task_id: Optional[str] = None
    tasks_completed: int
    total_tasks: Optional[int] = None
    concept_progress: dict = {}

class MisconceptionDetail(BaseModel):
    id: str
    description: str
    severity: str
    remediation_strategy: str
    explanation_template: str
    recommended_practice: str

class DifficultyDimensions(BaseModel):
    conceptual_difficulty: float
    cognitive_load: float
    transfer_complexity: float
    abstraction_depth: float
    prerequisite_burden: float

class TaskResult(BaseModel):
    is_correct: bool
    misconception_detected: Optional[str] = None
    misconception_detail: Optional[MisconceptionDetail] = None
    explanation: Optional[str] = None
    next_task_id: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    concept_id: str
    concept_name: str
    task_type: str
    difficulty: float
    difficulty_dimensions: Optional[DifficultyDimensions] = None
    question: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    misconception_targets: Optional[List[str]] = None

class TaskSubmissionRequest(BaseModel):
    task_id: str
    answer: str
    response_time_ms: Optional[int] = None

class StartSessionRequest(BaseModel):
    tenant_id: str = "default"
    target_concepts: List[str] = ["k2_algorithms"]
    initial_concept_id: Optional[str] = None


def get_session_service_safe():
    """
    Safe wrapper for SessionService dependency with error handling.
    
    MIGRATION: Uses common dependency from app.api.dependencies.learning.
    """
    try:
        return get_session_service()
    except Exception as e:
        logger.error(f"Failed to get SessionService: {e}")
        raise HTTPException(status_code=500, detail="Session service unavailable")

@router.post("/{user_id}/start")
async def start_session(user_id: str, request: StartSessionRequest, session_service = Depends(get_session_service)):
    """
    Start a new learning session.
    
    Validates longitudinal runtime coherence by creating a new session
    with proper curriculum context and persistence.
    """
    try:
        session = session_service.start_session(
            user_id=user_id,
            tenant_id=request.tenant_id,
            target_concepts=request.target_concepts,
            initial_concept_id=request.initial_concept_id
        )
        
        return SessionResponse(
            session_id=session.id,
            user_id=session.user_id,
            status=session.status.value,
            started_at=session.started_at.isoformat() if session.started_at else None,
            paused_at=session.paused_at.isoformat() if session.paused_at else None,
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
            current_task_id=session.current_concept_id,  # Using current_concept as proxy for task
            tasks_completed=session.tasks_completed,
            total_tasks=len(request.target_concepts),
            concept_progress={}
        )
    except Exception as e:
        logger.error(f"Failed to start session for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/pause")
async def pause_session(session_id: str, session_service = Depends(get_session_service)):
    """
    Pause an active session.
    
    Validates pacing memory by preserving session state for resumption.
    """
    try:
        session = session_service.pause_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            session_id=session.id,
            user_id=session.user_id,
            status=session.status.value,
            started_at=session.started_at.isoformat() if session.started_at else None,
            paused_at=session.paused_at.isoformat() if session.paused_at else None,
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
            current_task_id=session.current_concept_id,
            tasks_completed=session.tasks_completed,
            concept_progress={}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/resume")
async def resume_session(session_id: str, session_service = Depends(get_session_service)):
    """
    Resume a paused session.
    
    Validates learner continuity by restoring session state.
    """
    try:
        session = session_service.resume_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            session_id=session.id,
            user_id=session.user_id,
            status=session.status.value,
            started_at=session.started_at.isoformat() if session.started_at else None,
            paused_at=session.paused_at.isoformat() if session.paused_at else None,
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
            current_task_id=session.current_concept_id,
            tasks_completed=session.tasks_completed,
            concept_progress={}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/end")
async def end_session(session_id: str, session_service = Depends(get_session_service)):
    """
    End a session (complete or abandon).
    
    Validates replay-safe session progression by finalizing session state.
    """
    try:
        session = session_service.complete_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            session_id=session.id,
            user_id=session.user_id,
            status=session.status.value,
            started_at=session.started_at.isoformat() if session.started_at else None,
            paused_at=session.paused_at.isoformat() if session.paused_at else None,
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
            current_task_id=session.current_concept_id,
            tasks_completed=session.tasks_completed,
            concept_progress={}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/active")
async def get_active_session(user_id: str, session_service = Depends(get_session_service)):
    """
    Get the active session for a user.
    
    Validates longitudinal runtime continuity by retrieving current session state.
    """
    try:
        # Use session_service to get active session
        active_session = session_service.session_repository.get_active(user_id)
        
        if active_session is None:
            raise HTTPException(status_code=404, detail="No active session found")
        
        return SessionResponse(
            session_id=active_session.id,
            user_id=active_session.user_id,
            status=active_session.status.value,
            started_at=active_session.started_at.isoformat() if active_session.started_at else None,
            paused_at=active_session.paused_at.isoformat() if active_session.paused_at else None,
            completed_at=active_session.completed_at.isoformat() if active_session.completed_at else None,
            current_task_id=active_session.current_concept_id,
            tasks_completed=active_session.tasks_completed,
            total_tasks=len(active_session.target_concepts) if active_session.target_concepts else None,
            concept_progress={}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get active session for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/history")
async def get_session_history(user_id: str, limit: int = 10, session_service = Depends(get_session_service)):
    """
    Get session history for a user.
    
    C1.2 - Longitudinal Session Recovery:
    Validates cognition coherence across days/sessions.
    Enables resuming previous sessions to validate learner continuity.
    """
    try:
        # Retrieve session history from repository
        session_history = session_service.session_repository.get_by_user(user_id, limit)
        
        # Convert to response format
        history_responses = []
        for session in session_history:
            history_responses.append(SessionResponse(
                session_id=session.id,
                user_id=session.user_id,
                status=session.status.value,
                started_at=session.started_at.isoformat() if session.started_at else None,
                paused_at=session.paused_at.isoformat() if session.paused_at else None,
                completed_at=session.completed_at.isoformat() if session.completed_at else None,
                current_task_id=session.current_concept_id,
                tasks_completed=session.tasks_completed,
                total_tasks=len(session.target_concepts) if session.target_concepts else None,
                concept_progress={}
            ))
        
        return {
            "user_id": user_id,
            "total_sessions": len(history_responses),
            "sessions": history_responses
        }
    except Exception as e:
        logger.error(f"Failed to get session history for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/next-task")
async def get_next_task(session_id: str, session_service = Depends(get_session_service)):
    """
    Get the next task for a session.
    
    Validates task selection continuity by retrieving appropriate task.
    C1.3 - Task Semantics Hardening: Uses difficulty ladders for multi-dimensional
    difficulty semantics.
    """
    try:
        # Import difficulty ladder for C1.3 multi-dimensional difficulty
        from core.curriculum.difficulty_ladder import get_difficulty_ladder_registry, DifficultyDimensions
        
        ladder_registry = get_difficulty_ladder_registry()
        ladder = ladder_registry.get("k2_algorithms")
        
        # For now, return a mock task
        # In production, this would call TaskSelectionService
        task_id = str(__import__('uuid').uuid4())
        
        # Use difficulty ladder if available
        difficulty_dimensions = None
        if ladder:
            # Get first step for new learners (mastery = 0)
            difficulty_dimensions = ladder.get_step_for_mastery(0.0)
            difficulty_scalar = difficulty_dimensions.to_scalar()
            
            # Convert to dictionary for Pydantic
            difficulty_dimensions_api = {
                "conceptual_difficulty": difficulty_dimensions.conceptual_difficulty,
                "cognitive_load": difficulty_dimensions.cognitive_load,
                "transfer_complexity": difficulty_dimensions.transfer_complexity,
                "abstraction_depth": difficulty_dimensions.abstraction_depth,
                "prerequisite_burden": difficulty_dimensions.prerequisite_burden
            }
        else:
            difficulty_scalar = 0.5
            difficulty_dimensions_api = None
        
        return TaskResponse(
            task_id=task_id,
            concept_id="k2_algorithms",
            concept_name="Algorithms",
            task_type="multiple_choice",
            difficulty=difficulty_scalar,
            difficulty_dimensions=difficulty_dimensions_api,
            question="What is the time complexity of binary search?",
            options=["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            correct_answer="O(log n)",
            misconception_targets=["linear_search_confusion", "complexity_misunderstanding"]
        )
    except Exception as e:
        logger.error(f"Failed to get next task for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/submit-task")
async def submit_task(session_id: str, submission: TaskSubmissionRequest, session_service = Depends(get_session_service)):
    """
    Submit a task attempt.
    
    Validates evaluation continuity by processing learner answer.
    C1.3 - Task Semantics Hardening: Uses misconception ontology for
    pedagogical semantic richness and interpretability.
    """
    try:
        # Import misconception ontology
        from core.curriculum.misconception_ontology import get_misconception_ontology
        
        ontology = get_misconception_ontology()
        
        # For now, simple correctness check
        # In production, this would call AttemptEvaluationService
        is_correct = submission.answer.lower() == "o(log n)"
        
        # Detect misconception using ontology
        misconception_id = None
        misconception_detail = None
        
        if not is_correct:
            # Simple pattern-based detection (production would use more sophisticated analysis)
            if "o(1)" in submission.answer.lower():
                misconception_id = "linear_search_confusion"
            else:
                misconception_id = "binary_search_confusion"
            
            # Get misconception detail from ontology
            misconception = ontology.get(misconception_id)
            if misconception:
                misconception_detail = MisconceptionDetail(
                    id=misconception.identity.id,
                    description=misconception.semantics.description,
                    severity=misconception.semantics.severity.value,
                    remediation_strategy=misconception.remediation.strategy,
                    explanation_template=misconception.remediation.explanation_template,
                    recommended_practice=", ".join(misconception.remediation.practice_requirements)
                )
        
        return TaskResult(
            is_correct=is_correct,
            misconception_detected=misconception_id,
            misconception_detail=misconception_detail,
            explanation="Binary search divides the array in half each time, resulting in logarithmic time complexity.",
            next_task_id=str(__import__('uuid').uuid4()) if is_correct else None
        )
    except Exception as e:
        logger.error(f"Failed to submit task for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
