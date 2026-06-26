"""
Learning State API - User bandit and learner state
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from app.api.dependencies.learning import get_task_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/state/{user_id}")
async def get_learning_state(
    user_id: str,
    task_service = Depends(get_task_service)  # MIGRATION: Explicit dependency (was get_service_factory accessor)
) -> Dict[str, Any]:
    """Get full learning state (bandit + learner) for a user"""
    try:
        
        if not hasattr(task_service, 'bandit') or not task_service.bandit:
            raise HTTPException(status_code=404, detail="Bandit state not available")
        
        bandit = task_service.bandit
        
        # Get bandit state
        if user_id not in bandit.step_count:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Extract safe state attributes only
        state = {
            "user_id": user_id,
            "timestamp": "2026-04-27T00:00:00Z",
            "step_count": int(bandit.step_count.get(user_id, 0)),
            "tier": "unknown"
        }
        
        # Try to get regret values safely
        try:
            state["cumulative_learning_regret"] = float(bandit.cumulative_learning_regret.get(user_id, 0.0))
        except AttributeError:
            state["cumulative_learning_regret"] = 0.0
            
        try:
            state["cumulative_decision_regret"] = float(bandit.cumulative_decision_regret.get(user_id, 0.0))
        except AttributeError:
            state["cumulative_decision_regret"] = 0.0
        
        # Try to get arm contexts safely
        try:
            state["arm_contexts"] = bandit.arm_contexts.get(user_id, {})
        except AttributeError:
            state["arm_contexts"] = {}
        
        # Try to get alpha beta params safely
        try:
            state["alpha_beta_params"] = bandit.alpha_beta_params.get(user_id, {})
        except AttributeError:
            state["alpha_beta_params"] = {}
        
        # Get tier information if available
        if hasattr(task_service, 'tiered_reconstructor') and task_service.tiered_reconstructor:
            reconstructor = task_service.tiered_reconstructor
            if user_id in reconstructor.hot_state:
                state["tier"] = "hot"
            elif reconstructor.user_tiers.get(user_id) == "warm":
                state["tier"] = "warm"
            elif reconstructor.user_tiers.get(user_id) == "cold":
                state["tier"] = "cold"
        
        logger.info(f"🧠 Retrieved learning state for {user_id} (tier: {state['tier']})")
        return state
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get learning state for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve learning state")
