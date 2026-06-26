"""
Admin routes for tiered state reconstruction monitoring
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/tiered-stats")
async def get_tiered_stats() -> Dict[str, Any]:
    """Get tiered reconstruction system statistics"""
    try:
        from app.services import get_service_factory
        sf = get_service_factory()
        
        # Get task service
        task_service = sf.get_task_service()
        
        if not hasattr(task_service, 'tiered_reconstructor'):
            return {
                "status": "not_initialized",
                "message": "Tiered reconstructor not initialized"
            }
        
        reconstructor = task_service.tiered_reconstructor
        stats = reconstructor.get_system_stats()
        
        return {
            "status": "active",
            "stats": stats,
            "config": {
                "hot_threshold": reconstructor.config.hot_user_threshold,
                "warm_threshold": reconstructor.config.warm_user_threshold,
                "chunk_size": reconstructor.config.chunk_size,
                "max_interactions": reconstructor.config.max_interactions_per_user
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get tiered stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tiered-hot-users")
async def get_hot_users(limit: int = 50) -> Dict[str, Any]:
    """Get list of hot tier users"""
    try:
        from app.services import get_service_factory
        sf = get_service_factory()
        
        task_service = sf.get_task_service()
        
        if not hasattr(task_service, 'tiered_reconstructor'):
            raise HTTPException(status_code=404, detail="Tiered reconstructor not initialized")
        
        reconstructor = task_service.tiered_reconstructor
        hot_users = list(reconstructor.hot_state.keys())[:limit]
        
        user_details = []
        for user_id in hot_users:
            state = reconstructor.hot_state.get(user_id, {})
            user_details.append({
                "user_id": user_id,
                "tier": "hot",
                "interaction_count": state.get('interaction_count', 0),
                "step_count": state.get('bandit', {}).get('step_count', 0),
                "last_access": state.get('last_access'),
                "timestamp": state.get('timestamp')
            })
        
        return {
            "hot_users": user_details,
            "total_hot": len(reconstructor.hot_state),
            "showing": len(user_details)
        }
        
    except Exception as e:
        logger.error(f"Failed to get hot users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tiered/promote/{user_id}")
async def promote_user_to_hot(user_id: str) -> Dict[str, Any]:
    """Manually promote a user to hot tier"""
    try:
        from app.services import get_service_factory
        sf = get_service_factory()
        
        task_service = sf.get_task_service()
        
        if not hasattr(task_service, 'tiered_reconstructor'):
            raise HTTPException(status_code=404, detail="Tiered reconstructor not initialized")
        
        reconstructor = task_service.tiered_reconstructor
        
        # Get user state (this will trigger reconstruction if needed)
        state = reconstructor.get_user_state(user_id)
        
        if not state:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found or has no interactions")
        
        # Force promotion to hot
        reconstructor._promote_to_hot(user_id, state)
        
        # Apply to bandit
        sf._apply_hot_states_to_bandit(task_service, reconstructor)
        
        return {
            "message": f"User {user_id} promoted to hot tier",
            "current_tier": reconstructor.user_tiers.get(user_id, "unknown"),
            "stats": reconstructor.get_system_stats()
        }
        
    except Exception as e:
        logger.error(f"Failed to promote user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tiered/user/{user_id}")
async def get_user_tier_info(user_id: str) -> Dict[str, Any]:
    """Get detailed tier information for a specific user"""
    try:
        from app.services import get_service_factory
        sf = get_service_factory()
        
        task_service = sf.get_task_service()
        
        if not hasattr(task_service, 'tiered_reconstructor'):
            raise HTTPException(status_code=404, detail="Tiered reconstructor not initialized")
        
        reconstructor = task_service.tiered_reconstructor
        
        # Get user tier
        tier = reconstructor.user_tiers.get(user_id, "cold")
        
        # Get user state (triggers reconstruction if needed)
        state = reconstructor.get_user_state(user_id)
        
        result = {
            "user_id": user_id,
            "tier": tier,
            "has_state": state is not None,
            "in_hot_memory": user_id in reconstructor.hot_state
        }
        
        if state:
            result.update({
                "interaction_count": state.get('interaction_count', 0),
                "step_count": state.get('bandit', {}).get('step_count', 0),
                "arm_count": len(state.get('bandit', {}).get('arm_contexts', {})),
                "concept_count": len(state.get('learner', {}).get('mastery_data', {})),
                "timestamp": state.get('timestamp'),
                "last_access": state.get('last_access')
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get user tier info for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tiered/evict/{user_id}")
async def evict_user_from_hot(user_id: str) -> Dict[str, Any]:
    """Manually evict a user from hot tier"""
    try:
        from app.services import get_service_factory
        sf = get_service_factory()
        
        task_service = sf.get_task_service()
        
        if not hasattr(task_service, 'tiered_reconstructor'):
            raise HTTPException(status_code=404, detail="Tiered reconstructor not initialized")
        
        reconstructor = task_service.tiered_reconstructor
        
        if user_id not in reconstructor.hot_state:
            raise HTTPException(status_code=404, detail=f"User {user_id} not in hot tier")
        
        # Evict from hot
        evicted_state = reconstructor.hot_state.pop(user_id)
        reconstructor.user_tiers[user_id] = 'warm'
        reconstructor._snapshot_to_redis(user_id, evicted_state)
        
        return {
            "message": f"User {user_id} evicted from hot tier to warm",
            "previous_tier": "hot",
            "new_tier": "warm",
            "stats": reconstructor.get_system_stats()
        }
        
    except Exception as e:
        logger.error(f"Failed to evict user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
