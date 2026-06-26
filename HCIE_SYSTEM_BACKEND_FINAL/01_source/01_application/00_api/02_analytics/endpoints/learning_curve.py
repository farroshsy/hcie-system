"""
Learning Curve API - User learning trajectory analysis
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging

from app.api.dependencies.learning import get_task_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/learning-curve/{user_id}")
async def get_learning_curve(
    user_id: str,
    task_service = Depends(get_task_service)  # MIGRATION: Explicit dependency (was get_service_factory accessor)
) -> Dict[str, Any]:
    """Get learning curve trajectory for a user"""
    try:
        
        if not hasattr(task_service, 'bandit') or not task_service.bandit:
            raise HTTPException(status_code=404, detail="Bandit state not available")
        
        bandit = task_service.bandit
        
        # Check if user exists
        if user_id not in bandit.step_count:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Get arm contexts for learning curve analysis
        arm_contexts = bandit.arm_contexts.get(user_id, {})
        
        # Build learning trajectory
        steps = []
        rewards = []
        mastery_estimates = []
        timestamps = []
        
        for arm_id, contexts in arm_contexts.items():
            for context in contexts:
                if isinstance(context, dict) and 'timestamp' in context:
                    steps.append(len(steps) + 1)
                    rewards.append(context.get('reward', 0.0))
                    
                    # Estimate mastery from reward (simplified)
                    mastery = max(0.0, min(1.0, context.get('reward', 0.0)))
                    mastery_estimates.append(mastery)
                    
                    timestamps.append(context.get('timestamp'))
        
        # Calculate moving averages for smoother curves
        window_size = min(5, len(rewards))
        moving_avg_rewards = []
        moving_avg_mastery = []
        
        for i in range(len(rewards)):
            start_idx = max(0, i - window_size + 1)
            window_rewards = rewards[start_idx:i+1]
            window_mastery = mastery_estimates[start_idx:i+1]
            
            moving_avg_rewards.append(sum(window_rewards) / len(window_rewards))
            moving_avg_mastery.append(sum(window_mastery) / len(window_mastery))
        
        # Calculate learning rate (slope of mastery curve)
        learning_rate = 0.0
        if len(mastery_estimates) >= 2:
            # Simple linear regression for learning rate
            n = len(mastery_estimates)
            x = list(range(n))
            y = mastery_estimates
            
            x_mean = sum(x) / n
            y_mean = sum(y) / n
            
            numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            learning_rate = numerator / denominator if denominator != 0 else 0.0
        
        learning_curve_data = {
            "user_id": user_id,
            "trajectory": {
                "steps": steps,
                "rewards": rewards,
                "mastery_estimates": mastery_estimates,
                "moving_avg_rewards": moving_avg_rewards,
                "moving_avg_mastery": moving_avg_mastery,
                "timestamps": timestamps
            },
            "metrics": {
                "total_steps": len(steps),
                "final_mastery": mastery_estimates[-1] if mastery_estimates else 0.0,
                "avg_reward": sum(rewards) / len(rewards) if rewards else 0.0,
                "learning_rate": learning_rate,
                "improvement": mastery_estimates[-1] - mastery_estimates[0] if len(mastery_estimates) >= 2 else 0.0
            },
            "analysis": {
                "learning_phase": _classify_learning_phase(learning_rate, mastery_estimates[-1] if mastery_estimates else 0.0),
                "performance_trend": _classify_performance_trend(moving_avg_rewards),
                "mastery_stability": _calculate_mastery_stability(mastery_estimates)
            }
        }
        
        logger.info(f"📈 Generated learning curve for {user_id}")
        return learning_curve_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to generate learning curve for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate learning curve")

def _classify_learning_phase(learning_rate: float, final_mastery: float) -> str:
    """Classify the user's current learning phase"""
    if final_mastery < 0.3:
        return "beginner"
    elif learning_rate > 0.05 and final_mastery < 0.7:
        return "rapid_growth"
    elif learning_rate > 0.02:
        return "steady_progress"
    elif final_mastery > 0.8:
        return "mastery"
    else:
        return "plateau"

def _classify_performance_trend(moving_avg: List[float]) -> str:
    """Classify performance trend from moving average"""
    if len(moving_avg) < 3:
        return "insufficient_data"
    
    # Compare recent performance to earlier performance
    recent_avg = sum(moving_avg[-3:]) / 3
    earlier_avg = sum(moving_avg[:3]) / 3
    
    if recent_avg > earlier_avg + 0.1:
        return "improving"
    elif recent_avg < earlier_avg - 0.1:
        return "declining"
    else:
        return "stable"

def _calculate_mastery_stability(mastery_estimates: List[float]) -> str:
    """Calculate mastery stability from variance"""
    if len(mastery_estimates) < 3:
        return "insufficient_data"
    
    # Calculate variance
    mean = sum(mastery_estimates) / len(mastery_estimates)
    variance = sum((x - mean) ** 2 for x in mastery_estimates) / len(mastery_estimates)
    
    if variance < 0.01:
        return "very_stable"
    elif variance < 0.05:
        return "stable"
    elif variance < 0.1:
        return "variable"
    else:
        return "unstable"

# Export the router for proper module import
__all__ = ['router']
