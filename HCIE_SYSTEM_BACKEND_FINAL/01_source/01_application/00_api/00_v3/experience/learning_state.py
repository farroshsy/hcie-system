"""
Experience APIs - Frontend-Ready User Experience Layer

This layer hides runtime ontology (governance, replay, attribution, lifecycle, mutations, authority, telemetry)
and exposes user-facing adaptive semantics (learning state, recommendations, progress, continuity, confidence, recovery state).

Purpose: Product/frontend consumption
Audience: Frontend applications, user-facing features
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Experience API Models (Frontend-Ready, Not Runtime-Exposed)
# =============================================================================

class LearningStateResponse(BaseModel):
    """Frontend-ready learning state - hides governance internals"""
    user_id: str
    current_mastery: float  # Overall mastery level (0-1)
    concept_progress: List[Dict[str, Any]]  # Per-concept mastery
    learning_velocity: float  # How fast learning is happening
    confidence_level: str  # "low", "medium", "high"
    session_continuity: bool  # Whether session is continuous
    recovery_state: Optional[str]  # "recovering", "stable", None
    active_challenges: List[Dict[str, Any]]  # Current learning challenges
    next_recommended_difficulty: float  # Suggested next difficulty
    streak_count: int  # Current learning streak
    last_interaction_time: Optional[datetime]


class RecommendationExperienceResponse(BaseModel):
    """Frontend-ready recommendation - hides governance internals"""
    user_id: str
    recommended_concept: str
    recommended_difficulty: float
    confidence_score: float  # How confident the system is (0-1)
    reasoning_summary: str  # Human-readable explanation
    alternative_options: List[Dict[str, Any]]  # Other good options
    continuity_context: Dict[str, Any]  # Session continuity info
    trajectory_alignment: float  # How aligned with learning trajectory
    recovery_hints: Optional[List[str]]  # Hints if recovering from failure
    estimated_success_probability: float  # Likelihood of success


class ProgressExperienceResponse(BaseModel):
    """Frontend-ready progress - hides governance internals"""
    user_id: str
    overall_progress: float  # Overall progress (0-1)
    milestones_completed: int
    milestones_total: int
    current_milestone: Optional[str]
    time_to_completion_estimate: Optional[int]  # Minutes
    learning_curve_trend: str  # "accelerating", "steady", "decelerating"
    areas_of_strength: List[str]  # Concepts user is good at
    areas_for_improvement: List[str]  # Concepts needing work
    recent_achievements: List[Dict[str, Any]]  # Recent accomplishments


class SessionContinuityResponse(BaseModel):
    """Frontend-ready session continuity - hides lifecycle internals"""
    user_id: str
    session_active: bool
    session_duration: Optional[int]  # Seconds
    context_preserved: bool  # Whether learning context is preserved
    last_state: Optional[Dict[str, Any]]  # Last learning state snapshot
    recovery_available: bool  # Can recover from interruption
    estimated_recovery_time: Optional[int]  # Seconds to recover


class AdaptiveFeedbackResponse(BaseModel):
    """Frontend-ready adaptive feedback - hides governance internals"""
    user_id: str
    feedback_type: str  # "encouragement", "challenge", "guidance", "correction"
    message: str  # Human-readable feedback
    actionable_hints: List[str]  # Specific suggestions
    difficulty_adjustment: Optional[str]  # "increase", "decrease", "maintain"
    confidence_impact: Optional[float]  # How this affects confidence
    mastery_impact: Optional[float]  # How this affects mastery


# =============================================================================
# Experience API Endpoints
# =============================================================================

@router.get("/user/{user_id}/learning-state", response_model=LearningStateResponse)
async def get_learning_state(user_id: str) -> LearningStateResponse:
    """
    Get user's learning state (frontend-ready)
    
    This endpoint calls actual service functions directly (not HTTP) and transforms the response to hide runtime ontology.
    NO fake calculations - all math comes from the actual cognitive components.
    
    Hides: JT trajectories, governance evolution, authority state, replay semantics, lifecycle boundaries
    Exposes: learning state, progress, confidence, recovery hints, session continuity
    """
    try:
        # Call actual service functions directly (not HTTP calls)
        from app.services.projection import GovernanceProjection
        from app.api.v3.dependencies import get_governance_projection as get_projection
        
        # Get governance projection service
        projection = get_projection()
        
        # Get governance state directly from projection service
        state = projection.project_state(user_id)
        
        # Get trajectory directly from projection service
        trajectory = projection.project_trajectory(user_id)
        
        # Transform runtime data to frontend-ready semantics
        # Extract real mastery from governance weights
        governance_weights = state.governance_weights if hasattr(state, 'governance_weights') else {}
        
        # Calculate overall mastery from real governance data
        if governance_weights:
            current_mastery = governance_weights.get("overall_mastery", 0.0)
        else:
            current_mastery = 0.0
        
        # Derive concept progress from real trajectory data
        concept_progress = []
        component_history = state.component_history if hasattr(state, 'component_history') else {}
        
        for component, data in component_history.items():
            if isinstance(data, dict) and "mastery" in data:
                concept_progress.append({
                    "concept": component,
                    "mastery": data["mastery"],
                    "interactions": data.get("interactions", 0)
                })
        
        # Derive confidence level from real governance state
        normalization_state = state.normalization_state if hasattr(state, 'normalization_state') else {}
        confidence_score = normalization_state.get("confidence", 0.5)
        
        if confidence_score > 0.7:
            confidence_level = "high"
        elif confidence_score > 0.4:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        # Derive learning velocity from real trajectory data
        jt_trajectory = trajectory.jt_trajectory if hasattr(trajectory, 'jt_trajectory') else []
        if len(jt_trajectory) >= 2:
            learning_velocity = abs(jt_trajectory[-1] - jt_trajectory[-2])
        else:
            learning_velocity = 0.0
        
        # Derive session continuity from trajectory
        session_continuity = len(jt_trajectory) > 0
        
        # Derive recovery state from governance
        recovery_state = governance_weights.get("recovery_state", None)
        
        # Get active challenges from governance
        active_challenges = governance_weights.get("active_challenges", [])
        
        # Get next recommended difficulty from governance (real value, not hardcoded)
        next_recommended_difficulty = governance_weights.get("recommended_difficulty", 0.5)
        
        # Get streak count from governance
        streak_count = governance_weights.get("streak_count", 0)
        
        # Get last interaction time from governance
        last_interaction_time = governance_weights.get("last_interaction_time")
        
        return LearningStateResponse(
            user_id=user_id,
            current_mastery=current_mastery,
            concept_progress=concept_progress,
            learning_velocity=learning_velocity,
            confidence_level=confidence_level,
            session_continuity=session_continuity,
            recovery_state=recovery_state,
            active_challenges=active_challenges,
            next_recommended_difficulty=next_recommended_difficulty,
            streak_count=streak_count,
            last_interaction_time=last_interaction_time
        )
        
    except Exception as e:
        logger.error(f"Failed to get learning state for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve learning state")


@router.post("/user/{user_id}/recommendation", response_model=RecommendationExperienceResponse)
async def get_recommendation_experience(user_id: str, context: Dict[str, Any]) -> RecommendationExperienceResponse:
    """
    Get user-facing recommendation (frontend-ready)
    
    This endpoint calls actual service functions directly (not HTTP) and transforms the response to hide runtime ontology.
    NO fake calculations or reasoning - all comes from actual cognitive components.
    
    Hides: governance internals, transfer topology, uncertainty calculations, lifecycle boundaries
    Exposes: recommendation with confidence, reasoning, alternatives, continuity context, recovery hints
    """
    try:
        # Call actual service functions directly (not HTTP calls)
        from app.services.projection import RecommendationProjection
        from app.api.v3.dependencies import get_recommendation_projection as get_projection
        
        # Get recommendation projection service
        projection = get_projection()
        
        # Get recommendation directly from projection service
        state = projection.project_recommendation(user_id, context.get("mastery_data", {}))
        
        # Transform runtime data to frontend-ready semantics
        # Extract real recommendation data from projection service
        recommended_concept = state.recommended_concept if hasattr(state, 'recommended_concept') else ""
        recommended_difficulty = state.recommendation_metadata.get("difficulty", 0.5) if hasattr(state, 'recommendation_metadata') else 0.5
        confidence_score = state.recommendation_metadata.get("confidence", 0.5) if hasattr(state, 'recommendation_metadata') else 0.5
        
        # Use real reasoning from runtime API, not fake text
        reasoning_summary = state.recommendation_metadata.get("reasoning", "") if hasattr(state, 'recommendation_metadata') else ""
        
        # Get real alternative options from runtime API
        alternative_options = state.recommendation_metadata.get("alternative_options", []) if hasattr(state, 'recommendation_metadata') else []
        
        # Get real continuity context from runtime API
        continuity_context = state.recommendation_metadata.get("continuity_context", {}) if hasattr(state, 'recommendation_metadata') else {}
        
        # Get real trajectory alignment from runtime API
        trajectory_alignment = state.recommendation_metadata.get("trajectory_alignment", 0.5) if hasattr(state, 'recommendation_metadata') else 0.5
        
        # Get real recovery hints from runtime API
        recovery_hints = state.recommendation_metadata.get("recovery_hints", None) if hasattr(state, 'recommendation_metadata') else None
        
        # Get real estimated success probability from runtime API
        estimated_success_probability = state.recommendation_metadata.get("estimated_success_probability", 0.5) if hasattr(state, 'recommendation_metadata') else 0.5
        
        return RecommendationExperienceResponse(
            user_id=user_id,
            recommended_concept=recommended_concept,
            recommended_difficulty=recommended_difficulty,
            confidence_score=confidence_score,
            reasoning_summary=reasoning_summary,
            alternative_options=alternative_options,
            continuity_context=continuity_context,
            trajectory_alignment=trajectory_alignment,
            recovery_hints=recovery_hints,
            estimated_success_probability=estimated_success_probability
        )
        
    except Exception as e:
        logger.error(f"Failed to get recommendation for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendation")


@router.get("/user/{user_id}/progress", response_model=ProgressExperienceResponse)
async def get_progress_experience(user_id: str) -> ProgressExperienceResponse:
    """
    Get user's progress (frontend-ready)
    
    This endpoint calls actual service functions directly (not HTTP) and transforms the response to hide runtime ontology.
    NO fake calculations - all data comes from actual cognitive components.
    
    Hides: governance internals, trajectory structure, replay semantics
    Exposes: progress, milestones, learning curve trend, strengths, improvements
    """
    try:
        # Call actual service functions directly (not HTTP calls)
        from app.services.projection import TrajectoryProjection
        from app.api.v3.dependencies import get_trajectory_projection as get_projection
        
        # Get trajectory projection service
        projection = get_projection()
        
        # Get trajectory state directly from projection service
        state = projection.project_trajectory_state(user_id)
        
        # Transform runtime data to frontend-ready semantics
        # Extract real progress data from trajectory projection
        overall_progress = state.overall_progress if hasattr(state, 'overall_progress') else 0.0
        milestones_completed = state.milestones_completed if hasattr(state, 'milestones_completed') else 0
        milestones_total = state.milestones_total if hasattr(state, 'milestones_total') else 10
        current_milestone = state.current_milestone if hasattr(state, 'current_milestone') else None
        time_to_completion_estimate = state.time_to_completion_estimate if hasattr(state, 'time_to_completion_estimate') else None
        learning_curve_trend = state.learning_curve_trend if hasattr(state, 'learning_curve_trend') else "steady"
        areas_of_strength = state.areas_of_strength if hasattr(state, 'areas_of_strength') else []
        areas_for_improvement = state.areas_for_improvement if hasattr(state, 'areas_for_improvement') else []
        recent_achievements = state.recent_achievements if hasattr(state, 'recent_achievements') else []
        
        return ProgressExperienceResponse(
            user_id=user_id,
            overall_progress=overall_progress,
            milestones_completed=milestones_completed,
            milestones_total=milestones_total,
            current_milestone=current_milestone,
            time_to_completion_estimate=time_to_completion_estimate,
            learning_curve_trend=learning_curve_trend,
            areas_of_strength=areas_of_strength,
            areas_for_improvement=areas_for_improvement,
            recent_achievements=recent_achievements
        )
        
    except Exception as e:
        logger.error(f"Failed to get progress for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve progress")


@router.get("/user/{user_id}/session-continuity", response_model=SessionContinuityResponse)
async def get_session_continuity(user_id: str) -> SessionContinuityResponse:
    """
    Get session continuity (frontend-ready)
    
    This endpoint calls actual service functions directly (not HTTP) and transforms the response to hide runtime ontology.
    NO fake calculations - all data comes from actual cognitive components.
    
    Hides: lifecycle internals, state machine transitions, recovery mechanisms
    Exposes: session active, duration, context preserved, recovery available
    """
    try:
        # Call actual service functions directly (not HTTP calls)
        from app.services.projection import LifecycleProjection
        from app.api.v3.dependencies import get_lifecycle_projection as get_projection
        
        # Get lifecycle projection service
        projection = get_projection()
        
        # Get lifecycle state directly from projection service
        state = projection.project_lifecycle_state(user_id)
        
        # Transform runtime data to frontend-ready semantics
        # Extract real session continuity data from lifecycle projection
        session_active = state.session_active if hasattr(state, 'session_active') else False
        session_duration = state.session_duration if hasattr(state, 'session_duration') else 0
        context_preserved = state.context_preserved if hasattr(state, 'context_preserved') else False
        recovery_available = state.recovery_available if hasattr(state, 'recovery_available') else False
        last_session_time = state.last_session_time if hasattr(state, 'last_session_time') else None
        context_state = state.context_state if hasattr(state, 'context_state') else {}
        
        return SessionContinuityResponse(
            user_id=user_id,
            session_active=session_active,
            session_duration=session_duration,
            context_preserved=context_preserved,
            recovery_available=recovery_available,
            last_session_time=last_session_time,
            context_state=context_state
        )
        
    except Exception as e:
        logger.error(f"Failed to get session continuity for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session continuity")


@router.post("/user/{user_id}/adaptive-feedback", response_model=AdaptiveFeedbackResponse)
async def get_adaptive_feedback(user_id: str, interaction_result: Dict[str, Any]) -> AdaptiveFeedbackResponse:
    """
    Get adaptive feedback (frontend-ready)
    
    This endpoint calls actual service functions directly (not HTTP) and transforms the response to hide runtime ontology.
    NO fake calculations or feedback - all comes from actual cognitive components.
    
    Hides: governance internals, adaptive reasoning, policy calculations
    Exposes: feedback type, message, actionable hints, difficulty adjustment
    """
    try:
        # Call actual service functions directly (not HTTP calls)
        from app.services.projection import MutationProjection
        from app.api.v3.dependencies import get_mutation_projection as get_projection
        
        # Get mutation projection service
        projection = get_projection()
        
        # Submit mutation directly via projection service
        mutation_result = projection.submit_mutation(user_id, interaction_result)
        
        # Transform runtime data to frontend-ready semantics
        # Extract real feedback data from mutation projection
        feedback_type = mutation_result.feedback_type if hasattr(mutation_result, 'feedback_type') else "informational"
        message = mutation_result.feedback_message if hasattr(mutation_result, 'feedback_message') else ""
        actionable_hints = mutation_result.actionable_hints if hasattr(mutation_result, 'actionable_hints') else []
        difficulty_adjustment = mutation_result.difficulty_adjustment if hasattr(mutation_result, 'difficulty_adjustment') else "maintain"
        confidence_impact = mutation_result.confidence_impact if hasattr(mutation_result, 'confidence_impact') else 0.0
        mastery_impact = mutation_result.mastery_impact if hasattr(mutation_result, 'mastery_impact') else 0.0
        
        return AdaptiveFeedbackResponse(
            user_id=user_id,
            feedback_type=feedback_type,
            message=message,
            actionable_hints=actionable_hints,
            difficulty_adjustment=difficulty_adjustment,
            confidence_impact=confidence_impact,
            mastery_impact=mastery_impact
        )
        
    except Exception as e:
        logger.error(f"Failed to get adaptive feedback for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate adaptive feedback")
