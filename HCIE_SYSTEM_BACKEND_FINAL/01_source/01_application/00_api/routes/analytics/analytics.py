"""
Analytics API endpoints
Enhanced analytics with signal processing and learning insights
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List
from datetime import datetime

from app.services.task import TaskService
from core.signal.signal_extractor import SignalExtractor
from storage.postgres_store.interaction_store import get_postgres_interaction_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

def get_postgres_store():
    """Get PostgreSQL interaction store"""
    return get_postgres_interaction_store()

@router.get("/stats")
async def get_interaction_stats(postgres_store = Depends(get_postgres_store)):
    """Get overall interaction statistics"""
    try:
        stats = postgres_store.get_interaction_stats()
        return {
            "success": True,
            "data": stats,
            "message": "Interaction statistics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting interaction stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get interaction statistics")

@router.get("/interactions/{user_id}")
async def get_user_interactions(
    user_id: str, 
    limit: int = 100,
    postgres_store = Depends(get_postgres_store)
):
    """Get interactions for a specific user"""
    try:
        interactions = postgres_store.get_user_interactions(user_id, limit)
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "interactions": interactions,
                "total": len(interactions)
            },
        }
    except Exception as e:
        logger.error(f"Error getting user interactions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user interactions")

@router.get("/signals/{user_id}")
async def get_user_signals(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    include_patterns: bool = Query(default=True)
):
    """
    Get processed signal analysis for a user (user-facing)
    """
    try:
        from app.services import get_service_factory
        service_factory = get_service_factory()
        analytics_service = service_factory.get_analytics_service()
        
        return analytics_service.get_user_signals(user_id, limit, include_patterns)
        
    except Exception as e:
        logger.error(f"Error getting user signals: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting user signals: {str(e)}")

@router.get("/insights/{user_id}")
async def get_learning_insights(
    user_id: str,
    limit: int = Query(default=30, ge=1, le=100)
):
    """
    Get processed learning insights for a user (user-facing)
    """
    try:
        from app.services import get_service_factory
        service_factory = get_service_factory()
        analytics_service = service_factory.get_analytics_service()
        
        return analytics_service.get_learning_insights(user_id, limit)
        
    except Exception as e:
        logger.error(f"Error getting learning insights: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting learning insights: {str(e)}")

@router.get("/trajectory/{user_id}")
async def get_learning_trajectory(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    include_signals: bool = Query(default=True)
):
    """
    Get processed learning trajectory for a user (user-facing)
    """
    try:
        from app.services import get_service_factory
        service_factory = get_service_factory()
        analytics_service = service_factory.get_analytics_service()
        
        return analytics_service.get_learning_trajectory(user_id, limit, include_signals)
        
    except Exception as e:
        logger.error(f"Error getting learning trajectory: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting learning trajectory: {str(e)}")

# Helper functions
def _generate_recommendations(pattern_analysis: Dict[str, Any], insights: List[str]) -> List[str]:
    """Generate actionable recommendations from analysis"""
    recommendations = []
    
    learning_health = pattern_analysis.get("learning_health", {})
    
    # Engagement recommendations
    engagement = learning_health.get("average_engagement", 0.5)
    if engagement < 0.4:
        recommendations.append("Consider adjusting task difficulty to improve engagement")
    elif engagement > 0.8:
        recommendations.append("Current engagement level is excellent - maintain current approach")
    
    # Mastery gain recommendations
    mastery_gain = learning_health.get("average_mastery_gain", 0.0)
    if mastery_gain < 0.01:
        recommendations.append("Low mastery gain detected - review content difficulty and relevance")
    elif mastery_gain > 0.05:
        recommendations.append("Strong mastery gains - current learning path is effective")
    
    # ZPD alignment recommendations
    zpd_alignment = learning_health.get("zpd_alignment_score", 0.5)
    if zpd_alignment < 0.4:
        recommendations.append("Poor ZPD alignment - adjust difficulty to match skill level")
    
    # Policy effectiveness recommendations
    policy_effectiveness = learning_health.get("policy_effectiveness", 0.0)
    if policy_effectiveness < 0.3:
        recommendations.append("Consider adjusting learning policy for better effectiveness")
    
    return recommendations

def _get_engagement_level(engagement: float) -> str:
    """Get engagement level description"""
    if engagement < 0.3:
        return "Low"
    elif engagement < 0.6:
        return "Moderate"
    elif engagement < 0.8:
        return "Good"
    else:
        return "High"

def _get_learning_velocity(velocity: float) -> str:
    """Get learning velocity description"""
    if velocity < 0.01:
        return "Slow"
    elif velocity < 0.03:
        return "Moderate"
    elif velocity < 0.05:
        return "Good"
    else:
        return "Fast"

def _get_difficulty_alignment(alignment: float) -> str:
    """Get difficulty alignment description"""
    if alignment < 0.3:
        return "Poor"
    elif alignment < 0.5:
        return "Fair"
    elif alignment < 0.7:
        return "Good"
    else:
        return "Excellent"

def _get_policy_effectiveness(effectiveness: float) -> str:
    """Get policy effectiveness description"""
    if effectiveness < 0.2:
        return "Poor"
    elif effectiveness < 0.4:
        return "Fair"
    elif effectiveness < 0.6:
        return "Good"
    else:
        return "Excellent"

@router.get("/research-data")
async def get_research_data(
    limit: int = 1000,
    postgres_store = Depends(get_postgres_store)
):
    """Get interactions for research analysis"""
    try:
        interactions = postgres_store.get_interactions_for_analysis(limit)
        return {
            "success": True,
            "data": {
                "interactions": interactions,
                "total": len(interactions),
                "limit": limit
            },
            "message": f"Retrieved {len(interactions)} interactions for research analysis"
        }
    except Exception as e:
        logger.error(f"Error getting research data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get research data")

@router.get("/learning-curves/{user_id}")
async def get_learning_curves(
    user_id: str,
    postgres_store = Depends(get_postgres_store)
):
    """Get learning curve data for a user"""
    try:
        interactions = postgres_store.get_user_interactions(user_id, limit=1000)
        
        # Calculate learning curve metrics
        learning_curve = []
        cumulative_correct = 0
        cumulative_reward = 0
        
        for i, interaction in enumerate(interactions):
            cumulative_correct += 1 if interaction['correct'] else 0
            cumulative_reward += interaction['reward']
            
            learning_curve.append({
                "interaction_number": i + 1,
                "correct": interaction['correct'],
                "reward": interaction['reward'],
                "cumulative_correct_rate": cumulative_correct / (i + 1),
                "cumulative_avg_reward": cumulative_reward / (i + 1),
                "difficulty": interaction['difficulty'],
                "response_time": interaction['response_time'],
                "timestamp": interaction['timestamp']
            })
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "learning_curve": learning_curve,
                "total_interactions": len(interactions)
            },
            "message": f"Learning curve calculated for user {user_id}"
        }
    except Exception as e:
        logger.error(f"Error calculating learning curve: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate learning curve")

@router.get("/concept-performance")
async def get_concept_performance(postgres_store = Depends(get_postgres_store)):
    """Get performance metrics by concept"""
    try:
        interactions = postgres_store.get_interactions_for_analysis(limit=5000)
        
        # Calculate concept performance
        concept_stats = {}
        for interaction in interactions:
            concept_id = interaction['concept_id']
            if concept_id not in concept_stats:
                concept_stats[concept_id] = {
                    "total_interactions": 0,
                    "correct_interactions": 0,
                    "total_reward": 0,
                    "avg_response_time": 0,
                    "avg_difficulty": 0
                }
            
            stats = concept_stats[concept_id]
            stats["total_interactions"] += 1
            if interaction['correct']:
                stats["correct_interactions"] += 1
            stats["total_reward"] += interaction['reward']
            stats["avg_response_time"] += interaction['response_time']
            stats["avg_difficulty"] += interaction['difficulty']
        
        # Calculate averages
        for concept_id, stats in concept_stats.items():
            total = stats["total_interactions"]
            stats["accuracy"] = stats["correct_interactions"] / total
            stats["avg_reward"] = stats["total_reward"] / total
            stats["avg_response_time"] = stats["avg_response_time"] / total
            stats["avg_difficulty"] = stats["avg_difficulty"] / total
        
        return {
            "success": True,
            "data": {
                "concept_stats": concept_stats,
                "total_concepts": len(concept_stats)
            },
            "message": f"Performance metrics calculated for {len(concept_stats)} concepts"
        }
    except Exception as e:
        logger.error(f"Error getting concept performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get concept performance")
