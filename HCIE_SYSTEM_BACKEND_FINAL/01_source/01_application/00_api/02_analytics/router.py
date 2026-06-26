"""
Analytics API Router - Research analytics and insights
"""

from fastapi import APIRouter
from app.api.routes.analytics.analytics import router as analytics_router

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Mount existing analytics router directly
router.include_router(analytics_router)

# Add learning curve endpoint
@router.get("/learning-curve/{user_id}")
async def get_learning_curve(user_id: str):
    """Get learning curve for a user"""
    try:
        from app.services import get_service_factory
        sf = get_service_factory()
        
        # Get task service which has access to bandit state
        task_service = sf.get_task_service()
        
        if not hasattr(task_service, 'bandit') or not task_service.bandit:
            return {"error": "Bandit state not available"}
        
        bandit = task_service.bandit
        
        # Check if user exists
        if user_id not in bandit.step_count:
            return {"error": f"User {user_id} not found"}
        
        # Get arm contexts for learning curve analysis
        arm_contexts = bandit.arm_contexts.get(user_id, {})
        
        # Build simple learning trajectory
        rewards = []
        steps = []
        
        for arm_id, contexts in arm_contexts.items():
            for context in contexts:
                if isinstance(context, dict) and 'reward' in context:
                    steps.append(len(steps) + 1)
                    rewards.append(context.get('reward', 0.0))
        
        return {
            "user_id": user_id,
            "steps": steps,
            "rewards": rewards,
            "total_steps": len(steps),
            "avg_reward": sum(rewards) / len(rewards) if rewards else 0.0
        }
        
    except Exception as e:
        return {"error": str(e)}
