from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import random
import redis
from datetime import datetime

from storage.postgres_store.interaction_store import PostgresInteractionStore
from app.telemetry.opentelemetry_setup import (
    interaction_counter, 
    interaction_reward_sum, 
    interaction_reward_histogram
)

router = APIRouter(prefix="/admin/interactions", tags=["interactions"])

class InteractionRequest(BaseModel):
    user_id: str
    concept_id: str
    representation: str = "text"

@router.post("/create")
async def create_interaction(interaction: InteractionRequest):
    """Create a real interaction that saves to database and triggers CDC"""
    try:
        import random
        import math
        
        # Phase 8.2: Random policy assignment for tournament
        policy_mode = random.choice(["hcie", "dag", "random"])
        
        # THE STATE: Get user's current skill from Redis (default to 0.3)
        redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        user_key = f"user:{interaction.user_id}:latent_skill"
        current_skill = float(redis_client.get(user_key) or 0.3)
        
        # THE DECISION: How well does the policy "select" the task?
        if policy_mode == "hcie":
            # HCIE is optimal: targets the learner's "sweet spot" (ZPD)
            difficulty = current_skill + random.uniform(-0.05, 0.05)
        elif policy_mode == "dag":
            # DAG is better than random but less precise
            difficulty = current_skill + random.uniform(-0.2, 0.2)
        else:
            # Random is completely unaligned
            difficulty = random.uniform(0.1, 0.9)

        # THE ENVIRONMENT: Identical sigmoid for all
        # prob_correct is higher when skill and difficulty are matched (ZPD)
        # We use a gaussian centering: exp(-((skill-diff)^2)
        prob_success = math.exp(-((current_skill - difficulty)**2) / 0.1)
        correct = random.random() < prob_success
        
        # THE GROWTH: Stateful Learning with Variance
        if correct:
            learning_gain = 0.05 * (1 - current_skill) # Significant gain on success
        else:
            learning_gain = -0.01 * current_skill # Slight "forgetting" or confusion penalty
            
        new_skill = max(0.1, min(current_skill + learning_gain, 1.0))
        redis_client.set(user_key, new_skill)
        
        reward = prob_success + random.uniform(-0.01, 0.01)
        response_time = random.uniform(2.0, 8.0)
        
        # Create interaction data
        interaction_data = {
            "user_id": interaction.user_id,
            "concept_id": interaction.concept_id,
            "representation": interaction.representation,
            "correct": correct,
            "reward": reward,
            "response_time": response_time,
            "difficulty": difficulty,  # Policy-selected difficulty
            "task_id": f"task_{random.randint(1000, 9999)}",
            "policy_mode": policy_mode,
            "learning_gain": learning_gain,  # NEW METRIC
            "timestamp": datetime.now().isoformat()
        }
        
        # Save to database (this triggers CDC!)
        store = PostgresInteractionStore()
        result = store.save_interaction(interaction_data)
        
        # Update Prometheus metrics
        interaction_counter.add(1, {"policy_mode": policy_mode, "concept_id": interaction.concept_id})
        interaction_reward_sum.add(reward, {"policy_mode": policy_mode})
        interaction_reward_histogram.record(reward, {"policy_mode": policy_mode, "concept_id": interaction.concept_id})
        
        return {
            "status": "success",
            "message": "Interaction created and saved to database",
            "interaction_id": "generated" if result else "failed",
            "user_id": interaction.user_id,
            "reward": reward,
            "policy_mode": policy_mode,
            "correct": correct,
            "learning_gain": learning_gain,
            "current_skill": current_skill,
            "new_skill": redis_client.get(user_key) if correct else current_skill
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create interaction: {str(e)}")

@router.post("/batch-create")
async def batch_create_interactions(count: int = 60):
    """Create multiple interactions for tournament testing"""
    try:
        results = []
        for i in range(count):
            interaction = InteractionRequest(
                user_id=f"tournament_user_{i+1}",
                concept_id="tournament_concept",
                representation="text"
            )
            result = await create_interaction(interaction)
            results.append(result)
        
        return {
            "status": "success",
            "message": f"Created {count} interactions",
            "interactions": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to batch create: {str(e)}")
