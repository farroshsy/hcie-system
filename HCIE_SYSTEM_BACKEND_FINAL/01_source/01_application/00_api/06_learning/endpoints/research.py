"""
Research API - Algorithm Introspection and Debugging
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.repositories.learning_trace_repository import LearningTraceRepository
from storage.postgres_store.interaction_store import PostgresInteractionStore
from app.api.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])

def get_trace_repository() -> LearningTraceRepository:
    """Dependency injection for trace repository"""
    postgres_store = PostgresInteractionStore()
    return LearningTraceRepository(postgres_store)

@router.get("/trace/{event_id}")
def get_learning_trace(
    event_id: str,
    trace_repo: LearningTraceRepository = Depends(get_trace_repository),
    current_user: dict = Depends(get_current_user)
):
    """Get full algorithm trace for a specific event"""
    
    trace = trace_repo.get_trace(event_id)
    
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {event_id} not found")
    
    logger.info(f"🔬 Research trace accessed: {event_id} by user {current_user.get('user_id')}")
    return trace

@router.get("/traces/user/{user_id}")
def get_user_traces(
    user_id: str,
    limit: int = 50,
    trace_repo: LearningTraceRepository = Depends(get_trace_repository),
    current_user: dict = Depends(get_current_user)
):
    """Get all learning traces for a user (research analysis)"""
    
    traces = trace_repo.get_user_traces(user_id, limit)
    
    logger.info(f"🔬 User traces accessed: {user_id} ({len(traces)} traces) by {current_user.get('user_id')}")
    return {
        "user_id": user_id,
        "total_traces": len(traces),
        "traces": traces
    }

@router.get("/traces/concept/{concept}")
def get_concept_traces(
    concept: str,
    limit: int = 50,
    trace_repo: LearningTraceRepository = Depends(get_trace_repository),
    current_user: dict = Depends(get_current_user)
):
    """Get all learning traces for a concept (research analysis)"""
    
    traces = trace_repo.get_concept_traces(concept, limit)
    
    logger.info(f"🔬 Concept traces accessed: {concept} ({len(traces)} traces) by {current_user.get('user_id')}")
    return {
        "concept": concept,
        "total_traces": len(traces),
        "traces": traces
    }

@router.get("/algorithms/{user_id}")
def get_algorithm_summary(
    user_id: str,
    trace_repo: LearningTraceRepository = Depends(get_trace_repository),
    current_user: dict = Depends(get_current_user)
):
    """Get algorithm performance summary for a user - SQL optimized version"""
    # Use SQL-optimized aggregation method
    summary = trace_repo.get_algorithm_summary(user_id)
    
    # Add learning velocity from timeline if available
    timeline = trace_repo.get_learning_timeline(user_id, limit=100)
    if timeline:
        learning_velocity = sum(abs(item["delta"]) for item in timeline) / len(timeline)
        summary["learning_velocity"] = learning_velocity
    
    return summary

@router.get("/timeline/{user_id}")
def get_learning_timeline(
    user_id: str,
    concept: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    trace_repo: LearningTraceRepository = Depends(get_trace_repository),
    current_user: dict = Depends(get_current_user)
):
    """Get learning timeline for a user (mastery over time) - optimized SQL version"""
    # Use optimized SQL-based timeline method
    timeline = trace_repo.get_learning_timeline(user_id, concept, limit)
    
    # Calculate metrics from timeline data
    if timeline:
        learning_velocity = sum(abs(item["delta"]) for item in timeline) / len(timeline)
        avg_mastery = sum(item["mastery"] for item in timeline) / len(timeline)
        stagnation_periods = _detect_stagnation_periods(timeline)
    else:
        learning_velocity = 0.0
        avg_mastery = 0.0
        stagnation_periods = []
    
    return {
        "user_id": user_id,
        "concept": concept,
        "timeline": timeline,
        "total_events": len(timeline),
        "learning_velocity": learning_velocity,
        "avg_mastery": avg_mastery,
        "stagnation_periods": stagnation_periods
    }

def _detect_stagnation_periods(timeline: List[dict], threshold: float = 0.001) -> List[dict]:
    """Detect periods of learning stagnation"""
    if len(timeline) < 5:
        return []
    
    stagnant_periods = []
    start_idx = 0
    
    for i in range(1, len(timeline)):
        # Check if last 5 events had minimal learning
        recent_deltas = [abs(timeline[j]["delta"]) for j in range(max(0, i-4), i+1)]
        avg_recent_delta = sum(recent_deltas) / len(recent_deltas)
        
        if avg_recent_delta < threshold:
            # Continue stagnation period
            continue
        else:
            # End of stagnation period
            if i - start_idx >= 5:  # At least 5 stagnant events
                stagnant_periods.append({
                    "start_event": start_idx,
                    "end_event": i-1,
                    "duration": i - start_idx,
                    "start_mastery": timeline[start_idx]["mastery"],
                    "end_mastery": timeline[i-1]["mastery"],
                    "avg_delta": sum(abs(timeline[j]["delta"]) for j in range(start_idx, i)) / (i - start_idx)
                })
            start_idx = i
    
    return stagnant_periods
