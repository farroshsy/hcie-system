"""
Debug API Routes
Enhanced debugging with bandit, signals, and research-grade introspection
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import logging
from datetime import datetime
import numpy as np

from app.services.task.task_service import TaskService
from core.signal.signal_extractor import SignalExtractor
from core.bandit.bandit import ContextualBandit
from core.mastery.mastery_model import MasteryModel
from core.learning.transfer_aware_learner import TransferAwareLearner
from storage.redis_store.redis_store import RedisFeatureStore
from app.infrastructure.di.config_factory import build_config_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["debug"])

# Development flag - these endpoints should only be available in debug mode
DEBUG_ENABLED = build_config_provider().get_bool("debug_mode", False)

def check_debug_enabled():
    """Check if debug endpoints are enabled"""
    if not DEBUG_ENABLED:
        raise HTTPException(status_code=404, detail="Debug endpoints not available in production")

class ResetUserRequest(BaseModel):
    user_id: str

@router.post("/reset_user")
async def reset_user_state(request: ResetUserRequest):
    """Reset a user's state in Redis for clean experiments"""
    try:
        # 🔥 RUNTIME CONVERGENCE: Use ServiceFactory for canonical authority
        from app.services import get_service_factory
        service_factory = get_service_factory()
        task_service = service_factory.get_task_service()
        
        # Delete user's mastery data from Redis
        user_id = request.user_id
        redis_store = task_service.redis_store
        
        # Try to delete the user's mastery keys
        try:
            # Delete Lyapunov state
            lyapunov_key = f"lyapunov:{user_id}:*"
            redis_store.redis.delete(*redis_store.redis.keys(lyapunov_key))
            
            # Delete Bayesian state  
            bayesian_key = f"bayesian:{user_id}:*"
            redis_store.redis.delete(*redis_store.redis.keys(bayesian_key))
            
            # Delete Kalman state
            kalman_key = f"kalman:{user_id}:*"
            redis_store.redis.delete(*redis_store.redis.keys(kalman_key))
            
            # Reset bandit cumulative regret
            if hasattr(task_service, 'bandit'):
                task_service.bandit.reset_cumulative_regret(user_id)
            
            logger.info(f"✅ Reset state for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Partial reset for user {user_id}: {e}")
        
        return {"success": True, "message": f"Reset state for {user_id}"}
        
    except Exception as e:
        logger.error(f"Failed to reset user {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bandit_state/{user_id}")
async def debug_bandit_state(user_id: str):
    """
    Debug bandit algorithm state
    Returns alpha/beta parameters, regret, and selection metrics
    """
    try:
        from app.services import get_service_factory
        service_factory = get_service_factory()
        debug_service = service_factory.get_debug_service()
        
        return debug_service.get_bandit_state(user_id)
        
    except Exception as e:
        logger.error(f"Error debugging bandit state: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging bandit state: {str(e)}")

@router.get("/signals/{user_id}")
async def debug_signals(user_id: str, limit: int = Query(default=10, ge=1, le=50)):
    """
    Debug signal extraction for recent interactions
    """
    try:
        from app.services import get_service_factory
        service_factory = get_service_factory()
        debug_service = service_factory.get_debug_service()
        
        return debug_service.get_signal_state(user_id, limit)
        
    except Exception as e:
        logger.error(f"Error debugging signals: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging signals: {str(e)}")

@router.get("/state/{user_id}")
async def debug_complete_state(user_id: str):
    """
    Complete debug state for a user
    Combines bandit, mastery, and signals
    """
    try:
        from app.services import get_service_factory
        service_factory = get_service_factory()
        debug_service = service_factory.get_debug_service()
        
        return debug_service.get_complete_state(user_id)
        
    except Exception as e:
        logger.error(f"Error getting complete state: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting complete state: {str(e)}")

@router.get("/mastery/{user_id}")
async def debug_mastery_state(user_id: str):
    """Debug endpoint to inspect user mastery state"""
    try:
        from app.services import get_service_factory
        service_factory = get_service_factory()
        debug_service = service_factory.get_debug_service()
        
        return debug_service.get_mastery_state(user_id)
        
    except Exception as e:
        logger.error(f"Error debugging mastery state: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging mastery state: {str(e)}")

@router.get("/learner/{user_id}")
async def debug_learner_state(user_id: str):
    """Debug endpoint to inspect learner state"""
    try:
        from app.services import get_service_factory
        service_factory = get_service_factory()
        debug_service = service_factory.get_debug_service()
        
        return debug_service.get_learner_state(user_id)
        
    except Exception as e:
        logger.error(f"Error debugging learner state: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging learner state: {str(e)}")

@router.get("/transfer/{user_id}")
async def debug_transfer_state(user_id: str):
    """Debug endpoint to inspect transfer learning state"""
    try:
        from app.services import get_service_factory
        service_factory = get_service_factory()
        debug_service = service_factory.get_debug_service()
        
        return debug_service.get_transfer_state(user_id)
        
    except Exception as e:
        logger.error(f"Error debugging transfer state: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging transfer state: {str(e)}")

@router.get("/engine/{user_id}")
async def debug_engine_state(user_id: str):
    """Debug endpoint to inspect engine state"""
    try:
        from app.services import get_service_factory
        service_factory = get_service_factory()
        debug_service = service_factory.get_debug_service()
        
        return debug_service.get_engine_state(user_id)
        
    except Exception as e:
        logger.error(f"Error debugging engine state: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging engine state: {str(e)}")

@router.get("/governance/{user_id}")
async def debug_governance_state(user_id: str):
    """
    🔥 CONSTITUTIONAL GOVERNANCE: Production endpoint to inspect JT governance state
    Returns JT trajectory, volatility, exploration pressure, stability index, attribution, and weights
    
    NOTE: This is a production observability endpoint, not a debug endpoint
    """
    try:
        from app.services import get_service_factory
        service_factory = get_service_factory()
        task_service = service_factory.get_task_service()
        
        # Access JT governance from UnifiedLearningBrain
        if hasattr(task_service, 'unified_brain') and hasattr(task_service.unified_brain, 'jt_governance'):
            jt_governance = task_service.unified_brain.jt_governance
            
            # Get governance metrics
            metrics = jt_governance.get_governance_metrics()
            
            # Get JT history
            jt_history = jt_governance.jt_history
            
            # Get component history
            component_history = jt_governance.component_history
            
            return {
                "user_id": user_id,
                "weights": metrics["weights"],
                "volatility": metrics["volatility"],
                "exploration_pressure": metrics["exploration_pressure"],
                "stability_index": metrics["stability_index"],
                "jt_history_length": metrics["jt_history_length"],
                "jt_history": jt_history[-50:],  # Last 50 JT values
                "component_history": {
                    key: values[-50:] for key, values in component_history.items()
                }
            }
        else:
            return {
                "user_id": user_id,
                "error": "Constitutional JT governance not available"
            }
        
    except Exception as e:
        logger.error(f"Error debugging governance state: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging governance state: {str(e)}")

@router.get("/jt_trajectory/{user_id}")
async def debug_jt_trajectory(user_id: str):
    """
    🔥 CONSTITUTIONAL GOVERNANCE: Production endpoint to inspect JT trajectory over time
    Returns JT values with temporal ordering for trajectory analysis
    
    NOTE: This is a production observability endpoint, not a debug endpoint
    """
    try:
        from app.services import get_service_factory
        service_factory = get_service_factory()
        task_service = service_factory.get_task_service()
        
        # Access JT governance from UnifiedLearningBrain
        if hasattr(task_service, 'unified_brain') and hasattr(task_service.unified_brain, 'jt_governance'):
            jt_governance = task_service.unified_brain.jt_governance
            
            # Get JT history
            jt_history = jt_governance.jt_history
            
            # Compute trajectory statistics
            if len(jt_history) > 0:
                jt_mean = np.mean(jt_history)
                jt_std = np.std(jt_history)
                jt_min = np.min(jt_history)
                jt_max = np.max(jt_history)
                jt_trend = jt_history[-1] - jt_history[0] if len(jt_history) > 1 else 0
            else:
                jt_mean = jt_std = jt_min = jt_max = jt_trend = 0
            
            return {
                "user_id": user_id,
                "jt_trajectory": jt_history,
                "trajectory_length": len(jt_history),
                "statistics": {
                    "mean": jt_mean,
                    "std": jt_std,
                    "min": jt_min,
                    "max": jt_max,
                    "trend": jt_trend
                }
            }
        else:
            return {
                "user_id": user_id,
                "error": "Constitutional JT governance not available"
            }
        
    except Exception as e:
        logger.error(f"Error debugging JT trajectory: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging JT trajectory: {str(e)}")

@router.get("/weight_evolution/{user_id}")
async def debug_weight_evolution(user_id: str):
    """
    🔥 CONSTITUTIONAL GOVERNANCE: Production endpoint to inspect weight evolution over time
    Returns weight adaptation history for constitutional bounds verification
    
    NOTE: This is a production observability endpoint, not a debug endpoint
    """
    try:
        from app.services import get_service_factory
        service_factory = get_service_factory()
        task_service = service_factory.get_task_service()
        
        # Access JT governance from UnifiedLearningBrain
        if hasattr(task_service, 'unified_brain') and hasattr(task_service.unified_brain, 'jt_governance'):
            jt_governance = task_service.unified_brain.jt_governance
            
            # Get current weights
            current_weights = jt_governance.weights.copy()
            
            # Get default weights
            default_weights = jt_governance.default_weights.copy()
            
            # Compute weight changes
            weight_changes = {
                key: current_weights[key] - default_weights[key]
                for key in current_weights.keys()
            }
            
            return {
                "user_id": user_id,
                "current_weights": current_weights,
                "default_weights": default_weights,
                "weight_changes": weight_changes,
                "weights_sum": sum(current_weights.values()),
                "constitutional_bounds_verified": (
                    abs(sum(current_weights.values()) - 1.0) < 0.01 and
                    all(0 <= w <= 1 for w in current_weights.values())
                )
            }
        else:
            return {
                "user_id": user_id,
                "error": "Constitutional JT governance not available"
            }
        
    except Exception as e:
        logger.error(f"Error debugging weight evolution: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging weight evolution: {str(e)}")

