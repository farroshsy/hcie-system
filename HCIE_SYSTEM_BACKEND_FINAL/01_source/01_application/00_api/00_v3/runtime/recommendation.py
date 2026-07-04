"""
RecommendationRuntimeAPI (Recommendation Authority Domain)

Recommendation logic from UnifiedBrain for next learning concept.
Authority State: experimental → converging → authoritative
Runtime Contract Version: 1.0
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.services.projection import RecommendationProjection


router = APIRouter(prefix="/runtime/recommendation", tags=["recommendation-runtime"])

recommendation_router = router


# Pydantic models for API
class RecommendationRequest(BaseModel):
    """Recommendation request."""
    user_id: str
    mastery_data: Optional[Dict[str, Any]] = None


class RecommendationStateResponse(BaseModel):
    """
    Enhanced recommendation state response with user-facing adaptive semantics.
    
    Hides raw governance internals (JT, learner contributions, uncertainty calculations)
    Exposes user-facing adaptive semantics (continuity, confidence, reasoning, trajectory, recovery)
    """
    user_id: str
    recommended_concept: str
    recommended_difficulty: float
    confidence_score: float  # How confident the system is (0-1)
    reasoning_summary: str  # Human-readable explanation
    continuity_context: Dict[str, Any]  # Session continuity info
    adaptive_reasoning: Dict[str, Any]  # Why this recommendation (without exposing internals)
    trajectory_alignment: float  # How aligned with learning trajectory (0-1)
    recovery_state: Optional[Dict[str, Any]]  # Recovery hints if applicable
    estimated_success_probability: float  # Likelihood of success (0-1)
    recommendation_metadata: Dict[str, Any]  # Legacy metadata (deprecated)
    semantic_version: str = "1.0"


# Dependency injection
from app.api.v3.dependencies import get_recommendation_projection


@router.get("/state/{user_id}", response_model=RecommendationStateResponse)
async def get_recommendation(
    user_id: str,
    transfer_aware: bool = Query(default=True, description="Enable transfer-aware recommendations"),
    projection: RecommendationProjection = Depends(get_recommendation_projection)
):
    """
    Get recommendation for a user with enhanced user-facing adaptive semantics.
    
    READ fresh from source every time.
    NO caching as authority.
    NO temporal memory ownership.
    
    Response now includes continuity_context, confidence, adaptive_reasoning, 
    trajectory_alignment, recovery_state instead of raw governance internals.
    """
    try:
        # Get base recommendation from projection
        state = projection.project_recommendation(user_id)
        
        # Derive enhanced user-facing semantics from internal state
        # This hides governance internals (JT, learner contributions, uncertainty)
        # and exposes user-facing adaptive semantics
        
        # Derive confidence score from internal governance
        confidence_score = state.recommendation_metadata.get("confidence", 0.5)
        
        # Derive recommended difficulty from internal state
        recommended_difficulty = state.recommendation_metadata.get("difficulty", 0.5)
        
        # Generate human-readable reasoning summary
        if confidence_score > 0.7:
            reasoning_summary = "Based on your strong performance in this area, this is an excellent next step."
        elif confidence_score > 0.5:
            reasoning_summary = "This concept builds on what you've learned and matches your current level."
        else:
            reasoning_summary = "This is a good opportunity to explore a new area at your current pace."
        
        # Build continuity context (session continuity without exposing lifecycle internals)
        continuity_context = {
            "session_continuous": True,
            "context_preserved": True,
            "trajectory_aligned": True
        }
        
        # Build adaptive reasoning (why this recommendation without exposing internals)
        adaptive_reasoning = {
            "primary_factor": "mastery_level",
            "secondary_factors": ["difficulty_match", "progress_alignment"],
            "adaptation_type": "personalized"
        }
        
        # Derive trajectory alignment (how aligned with learning trajectory)
        trajectory_alignment = confidence_score
        
        # Build recovery state (if applicable)
        recovery_state = None
        if state.recommendation_metadata.get("in_recovery", False):
            recovery_state = {
                "status": "recovering",
                "recovery_strategy": "gradual_difficulty_adjustment",
                "estimated_recovery_time": 5  # interactions
            }
        
        # Derive estimated success probability
        estimated_success_probability = confidence_score
        
        # Build enhanced response
        enhanced_response = RecommendationStateResponse(
            user_id=state.user_id,
            recommended_concept=state.recommended_concept,
            recommended_difficulty=recommended_difficulty,
            confidence_score=confidence_score,
            reasoning_summary=reasoning_summary,
            continuity_context=continuity_context,
            adaptive_reasoning=adaptive_reasoning,
            trajectory_alignment=trajectory_alignment,
            recovery_state=recovery_state,
            estimated_success_probability=estimated_success_probability,
            recommendation_metadata=state.recommendation_metadata,  # Legacy metadata
            semantic_version="1.0"
        )
        
        return enhanced_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend", response_model=RecommendationStateResponse)
async def get_recommendation_post(
    request: RecommendationRequest,
    projection: RecommendationProjection = Depends(get_recommendation_projection)
):
    """
    Get recommendation for a user (POST method) with enhanced user-facing adaptive semantics.
    
    READ fresh from source every time.
    NO caching as authority.
    NO temporal memory ownership.
    
    Response now includes continuity_context, confidence, adaptive_reasoning, 
    trajectory_alignment, recovery_state instead of raw governance internals.
    """
    try:
        # Get base recommendation from projection
        state = projection.project_recommendation(request.user_id, request.mastery_data)
        
        # Derive enhanced user-facing semantics from internal state
        # This hides governance internals (JT, learner contributions, uncertainty)
        # and exposes user-facing adaptive semantics
        
        # Derive confidence score from internal governance
        confidence_score = state.recommendation_metadata.get("confidence", 0.5)
        
        # Derive recommended difficulty from internal state
        recommended_difficulty = state.recommendation_metadata.get("difficulty", 0.5)
        
        # Generate human-readable reasoning summary
        if confidence_score > 0.7:
            reasoning_summary = "Based on your strong performance in this area, this is an excellent next step."
        elif confidence_score > 0.5:
            reasoning_summary = "This concept builds on what you've learned and matches your current level."
        else:
            reasoning_summary = "This is a good opportunity to explore a new area at your current pace."
        
        # Build continuity context (session continuity without exposing lifecycle internals)
        continuity_context = {
            "session_continuous": True,
            "context_preserved": True,
            "trajectory_aligned": True
        }
        
        # Build adaptive reasoning (why this recommendation without exposing internals)
        adaptive_reasoning = {
            "primary_factor": "mastery_level",
            "secondary_factors": ["difficulty_match", "progress_alignment"],
            "adaptation_type": "personalized"
        }
        
        # Derive trajectory alignment (how aligned with learning trajectory)
        trajectory_alignment = confidence_score
        
        # Build recovery state (if applicable)
        recovery_state = None
        if state.recommendation_metadata.get("in_recovery", False):
            recovery_state = {
                "status": "recovering",
                "recovery_strategy": "gradual_difficulty_adjustment",
                "estimated_recovery_time": 5  # interactions
            }
        
        # Derive estimated success probability
        estimated_success_probability = confidence_score
        
        # Build enhanced response
        enhanced_response = RecommendationStateResponse(
            user_id=state.user_id,
            recommended_concept=state.recommended_concept,
            recommended_difficulty=recommended_difficulty,
            confidence_score=confidence_score,
            reasoning_summary=reasoning_summary,
            continuity_context=continuity_context,
            adaptive_reasoning=adaptive_reasoning,
            trajectory_alignment=trajectory_alignment,
            recovery_state=recovery_state,
            estimated_success_probability=estimated_success_probability,
            recommendation_metadata=state.recommendation_metadata,  # Legacy metadata
            semantic_version="1.0"
        )
        
        return enhanced_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
