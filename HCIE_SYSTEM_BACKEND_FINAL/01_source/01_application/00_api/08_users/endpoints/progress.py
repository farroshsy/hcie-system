"""
User Progress Endpoint - User learning progress
"""

from fastapi import APIRouter, HTTPException, Depends
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.learning import get_task_service
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/me/progress")
async def get_user_progress(
    user: Dict[str, Any] = Depends(get_current_user),
    task_service = Depends(get_task_service)  # MIGRATION: Explicit dependency (was get_service_factory accessor)
) -> Dict[str, Any]:
    """Get current user learning progress"""
    try:
        
        if not hasattr(task_service, 'bandit') or not task_service.bandit:
            return {
                "user_id": user["id"],
                "message": "Learning system not available",
                "progress": {}
            }
        
        bandit = task_service.bandit
        
        # Check if user exists in bandit system
        if user["id"] not in bandit.step_count:
            return {
                "user_id": user["id"],
                "message": "No learning activity yet",
                "progress": {
                    "total_steps": 0,
                    "total_rewards": 0,
                    "avg_reward": 0.0,
                    "policy_mode": user["policy_mode"],
                    "experiment_group": user["experiment_group"]
                }
            }
        
        # Calculate progress metrics
        step_count = bandit.step_count.get(user["id"], 0)
        arm_contexts = bandit.arm_contexts.get(user["id"], {})
        
        total_rewards = []
        for arm_id, contexts in arm_contexts.items():
            for context in contexts:
                if isinstance(context, dict) and 'reward' in context:
                    total_rewards.append(context.get('reward', 0.0))
        
        total_reward_sum = sum(total_rewards)
        avg_reward = total_reward_sum / len(total_rewards) if total_rewards else 0.0
        
        # Get regret if available
        learning_regret = 0.0
        decision_regret = 0.0
        
        try:
            learning_regret = float(bandit.cumulative_learning_regret.get(user["id"], 0.0))
            decision_regret = float(bandit.cumulative_decision_regret.get(user["id"], 0.0))
        except (AttributeError, KeyError):
            pass
        
        progress_data = {
            "user_id": user["id"],
            "policy_mode": user["policy_mode"],
            "experiment_group": user["experiment_group"],
            "learning_metrics": {
                "total_steps": step_count,
                "total_interactions": len(total_rewards),
                "total_rewards": total_reward_sum,
                "avg_reward": avg_reward,
                "learning_regret": learning_regret,
                "decision_regret": decision_regret
            },
            "bandit_info": {
                "arms_mastered": len(arm_contexts),
                "alpha_beta_params": bandit.alpha_beta_params.get(user["id"], {}),
                "last_activity": max([
                    ctx.get('timestamp', '') 
                    for contexts in arm_contexts.values() 
                    for ctx in contexts 
                    if isinstance(ctx, dict)
                ], default=user["last_active"])
            }
        }
        
        logger.info(f"📊 Retrieved progress for user: {user['id']}")
        return progress_data
        
    except Exception as e:
        logger.error(f"❌ Get progress error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get progress")
