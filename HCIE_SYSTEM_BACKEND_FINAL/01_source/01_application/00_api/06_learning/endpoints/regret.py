"""
Regret Analysis API - Learning and decision regret metrics
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/regret/{user_id}")
async def get_regret_analysis(user_id: str) -> Dict[str, Any]:
    """Get detailed regret analysis for a user"""
    try:
        from app.services import get_service_factory
        sf = get_service_factory()
        
        # Get task service which has access to bandit state
        task_service = sf.get_task_service()
        
        if not hasattr(task_service, 'bandit') or not task_service.bandit:
            raise HTTPException(status_code=404, detail="Bandit state not available")
        
        bandit = task_service.bandit
        
        # Check if user exists
        if user_id not in bandit.step_count:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Extract regret metrics
        regret_data = {
            "user_id": user_id,
            "cumulative_learning_regret": float(bandit.cumulative_learning_regret.get(user_id, 0.0)),
            "cumulative_decision_regret": float(bandit.cumulative_decision_regret.get(user_id, 0.0)),
            "avg_learning_regret": float(bandit.avg_learning_regret.get(user_id, 0.0)),
            "avg_decision_regret": float(bandit.avg_decision_regret.get(user_id, 0.0)),
            "step_count": bandit.step_count.get(user_id, 0),
            "redis_regret": bandit.redis_regret.get(user_id, {}),
            "analysis": {
                "total_regret": float(
                    bandit.cumulative_learning_regret.get(user_id, 0.0) + 
                    bandit.cumulative_decision_regret.get(user_id, 0.0)
                ),
                "regret_per_step": 0.0,
                "efficiency_score": 0.0
            }
        }
        
        # Calculate derived metrics
        step_count = bandit.step_count.get(user_id, 0)
        if step_count > 0:
            regret_data["analysis"]["regret_per_step"] = regret_data["analysis"]["total_regret"] / step_count
            # Efficiency score: lower regret = higher efficiency
            regret_data["analysis"]["efficiency_score"] = max(0, 1.0 - (regret_data["analysis"]["total_regret"] / max(step_count, 1)))
        
        logger.info(f"📊 Retrieved regret analysis for {user_id}")
        return regret_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get regret analysis for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve regret analysis")

@router.get("/regret/{user_id}/history")
async def get_regret_history(user_id: str) -> Dict[str, Any]:
    """Get regret history trajectory for a user"""
    try:
        from app.services import get_service_factory
        sf = get_service_factory()
        
        # Get task service
        task_service = sf.get_task_service()
        
        if not hasattr(task_service, 'bandit') or not task_service.bandit:
            raise HTTPException(status_code=404, detail="Bandit state not available")
        
        bandit = task_service.bandit
        
        # Check if user exists
        if user_id not in bandit.step_count:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Get arm contexts for trajectory analysis
        arm_contexts = bandit.arm_contexts.get(user_id, {})
        
        # Build regret trajectory from arm contexts
        learning_regret_trajectory = []
        decision_regret_trajectory = []
        steps = []
        
        for arm_id, contexts in arm_contexts.items():
            for context in contexts:
                if isinstance(context, dict) and 'timestamp' in context:
                    # Extract regret from context if available
                    reward = context.get('reward', 0.0)
                    # Simple regret calculation: 1.0 - reward (assuming optimal reward is 1.0)
                    regret = max(0.0, 1.0 - reward)
                    learning_regret_trajectory.append(regret)
                    decision_regret_trajectory.append(regret * 0.5)  # Assume decision regret is half
                    steps.append(len(learning_regret_trajectory))
        
        return {
            "user_id": user_id,
            "trajectory": {
                "steps": steps,
                "learning_regret": learning_regret_trajectory,
                "decision_regret": decision_regret_trajectory,
                "cumulative_learning": [
                    sum(learning_regret_trajectory[:i+1]) for i in range(len(learning_regret_trajectory))
                ],
                "cumulative_decision": [
                    sum(decision_regret_trajectory[:i+1]) for i in range(len(decision_regret_trajectory))
                ]
            },
            "summary": {
                "total_steps": len(steps),
                "final_learning_regret": learning_regret_trajectory[-1] if learning_regret_trajectory else 0.0,
                "final_decision_regret": decision_regret_trajectory[-1] if decision_regret_trajectory else 0.0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get regret history for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve regret history")
