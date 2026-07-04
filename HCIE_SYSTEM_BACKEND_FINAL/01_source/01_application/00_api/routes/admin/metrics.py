"""
Metrics API Routes
For testing and triggering research metrics
"""

from fastapi import APIRouter, HTTPException
from app.telemetry.opentelemetry_setup import (
    interaction_counter, 
    interaction_reward_sum, 
    interaction_reward_histogram
)

router = APIRouter(prefix="/admin/metrics", tags=["metrics"])

@router.post("/test-interaction")
async def test_interaction_metric():
    """Test endpoint to simulate interaction metrics with Phase 8 random policy assignment"""
    try:
        import random
        
        # Phase 8: Random policy assignment for tournament
        policy_mode = random.choice(["hcie", "dag", "random"])
        
        # Simulate realistic reward based on policy
        if policy_mode == "hcie":
            reward = 0.85 + random.uniform(-0.1, 0.1)  # HCIE: ~0.85 ± 0.1
        elif policy_mode == "dag":
            reward = 0.75 + random.uniform(-0.15, 0.15)  # DAG: ~0.75 ± 0.15
        else:  # random
            reward = 0.65 + random.uniform(-0.2, 0.2)  # Random: ~0.65 ± 0.2
        
        concept_id = "test_concept"
        
        # Update metrics
        interaction_counter.add(1, {"policy_mode": policy_mode, "concept_id": concept_id})
        interaction_reward_sum.add(reward, {"policy_mode": policy_mode})
        interaction_reward_histogram.record(reward, {"policy_mode": policy_mode, "concept_id": concept_id})
        
        return {
            "status": "success",
            "message": "Test interaction metrics recorded",
            "reward": reward,
            "policy_mode": policy_mode,
            "concept_id": concept_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record metrics: {e}")

@router.post("/simulate-low-performance")
async def simulate_low_performance():
    """Simulate low performance for testing alerts"""
    try:
        # Simulate low rewards (below 0.5 threshold)
        low_rewards = [0.2, 0.3, 0.1, 0.4, 0.35]
        policy_mode = "hcie_test"
        concept_id = "test_concept"
        
        for reward in low_rewards:
            interaction_counter.add(1, {"policy_mode": policy_mode, "concept_id": concept_id})
            interaction_reward_sum.add(reward, {"policy_mode": policy_mode})
            interaction_reward_histogram.record(reward, {"policy_mode": policy_mode, "concept_id": concept_id})
        
        return {
            "status": "success",
            "message": "Low performance simulation completed",
            "rewards": low_rewards,
            "policy_mode": policy_mode,
            "concept_id": concept_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to simulate low performance: {e}")
