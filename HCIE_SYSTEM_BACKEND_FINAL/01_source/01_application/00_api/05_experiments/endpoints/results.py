"""
Experiment Results API - Analyze and retrieve experiment results
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{experiment_id}/results")
async def get_experiment_results(experiment_id: str) -> Dict[str, Any]:
    """Get comprehensive experiment results from database"""
    try:
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        
        store = PostgresInteractionStore()
        
        # Get experiment details
        experiment_query = "SELECT id, name, status, created_at FROM experiments WHERE id = %s"
        experiment = store.execute_read(experiment_query, (experiment_id,), fetch_one=True)
        
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # Get all experiment runs for this experiment
        runs_query = "SELECT id, run_name, policy, learner_archetype, num_learners, num_concepts, num_interactions, status FROM experiment_runs WHERE experiment_id = %s"
        runs = store.execute_read(runs_query, (experiment_id,))
        
        if not runs:
            raise HTTPException(status_code=404, detail="No experiment runs found")
        
        # Get trajectory data for all runs
        results = {}
        for run in runs:
            run_id = run["id"]
            
            # Get trajectories for this run
            trajectory_query = """
                SELECT user_id, concept, interaction_number, mastery_after, uncertainty_after, 
                       confidence_after, correctness, policy, jt_value, exploration_pressure, 
                       transfer_amount, transfer_efficiency, zpd_score
                FROM trajectory_records 
                WHERE experiment_run_id = %s
                ORDER BY user_id, interaction_number
            """
            trajectories = store.execute_read(trajectory_query, (run_id,))
            
            # Calculate aggregate metrics
            if trajectories:
                total_trajectories = len(trajectories)
                avg_mastery = np.mean([t["mastery_after"] for t in trajectories])
                avg_uncertainty = np.mean([t["uncertainty_after"] for t in trajectories])
                avg_confidence = np.mean([t["confidence_after"] for t in trajectories])
                accuracy = sum([1 for t in trajectories if t["correctness"]]) / total_trajectories
                
                # Per-user metrics
                user_metrics = {}
                for user_id in set(t["user_id"] for t in trajectories):
                    user_trajectories = [t for t in trajectories if t["user_id"] == user_id]
                    user_metrics[user_id] = {
                        "interactions": len(user_trajectories),
                        "avg_mastery": np.mean([t["mastery_after"] for t in user_trajectories]),
                        "avg_uncertainty": np.mean([t["uncertainty_after"] for t in user_trajectories]),
                        "accuracy": sum([1 for t in user_trajectories if t["correctness"]]) / len(user_trajectories)
                    }
                
                results[run_id] = {
                    "run_name": run["run_name"],
                    "policy": run["policy"],
                    "learner_archetype": run["learner_archetype"],
                    "num_learners": run["num_learners"],
                    "num_concepts": run["num_concepts"],
                    "num_interactions": run["num_interactions"],
                    "status": run["status"],
                    "total_trajectories": total_trajectories,
                    "aggregate_metrics": {
                        "avg_mastery": float(avg_mastery),
                        "avg_uncertainty": float(avg_uncertainty),
                        "avg_confidence": float(avg_confidence),
                        "accuracy": float(accuracy)
                    },
                    "user_metrics": user_metrics,
                    "trajectories": trajectories
                }
            else:
                results[run_id] = {
                    "run_name": run["run_name"],
                    "status": run["status"],
                    "message": "No trajectory data available"
                }
        
        logger.info(f"📊 Retrieved results for experiment: {experiment['name']} ({experiment_id})")
        
        return {
            "experiment_id": experiment_id,
            "experiment_name": experiment["name"],
            "experiment_status": experiment["status"],
            "total_runs": len(runs),
            "results": results,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get experiment results: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve experiment results")

@router.get("/{experiment_id}/results/summary")
async def get_experiment_summary(experiment_id: str) -> Dict[str, Any]:
    """Get experiment summary with statistical significance from database"""
    try:
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        
        store = PostgresInteractionStore()
        
        # Get experiment details
        experiment_query = "SELECT id, name, status FROM experiments WHERE id = %s"
        experiment = store.execute_read(experiment_query, (experiment_id,), fetch_one=True)
        
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # Get all experiment runs for this experiment
        runs_query = "SELECT id, run_name, policy, learner_archetype, status FROM experiment_runs WHERE experiment_id = %s"
        runs = store.execute_read(runs_query, (experiment_id,))
        
        if not runs:
            raise HTTPException(status_code=404, detail="No experiment runs found")
        
        # Collect metrics across all runs
        all_metrics = {}
        total_trajectories = 0
        
        for run in runs:
            run_id = run["id"]
            
            # Get trajectories for this run
            trajectory_query = """
                SELECT user_id, mastery_after, uncertainty_after, correctness
                FROM trajectory_records 
                WHERE experiment_run_id = %s
            """
            trajectories = store.execute_read(trajectory_query, (run_id,))
            
            if trajectories:
                total_trajectories += len(trajectories)
                run_key = f"{run['policy']}_{run['learner_archetype']}"
                
                all_metrics[run_key] = {
                    "mastery_values": [t["mastery_after"] for t in trajectories],
                    "uncertainty_values": [t["uncertainty_after"] for t in trajectories],
                    "correctness_values": [1 if t["correctness"] else 0 for t in trajectories]
                }
        
        # Calculate summary statistics
        if not all_metrics:
            return {
                "experiment_id": experiment_id,
                "experiment_name": experiment["name"],
                "message": "No trajectory data available for summary",
                "retrieved_at": datetime.utcnow().isoformat()
            }
        
        summary = {
            "total_trajectories": total_trajectories,
            "total_configurations": len(all_metrics),
            "configurations": {}
        }
        
        for config_key, metrics in all_metrics.items():
            mastery_values = metrics["mastery_values"]
            uncertainty_values = metrics["uncertainty_values"]
            correctness_values = metrics["correctness_values"]
            
            summary["configurations"][config_key] = {
                "mastery": {
                    "mean": float(np.mean(mastery_values)),
                    "std": float(np.std(mastery_values)),
                    "min": float(np.min(mastery_values)),
                    "max": float(np.max(mastery_values))
                },
                "uncertainty": {
                    "mean": float(np.mean(uncertainty_values)),
                    "std": float(np.std(uncertainty_values)),
                    "min": float(np.min(uncertainty_values)),
                    "max": float(np.max(uncertainty_values))
                },
                "accuracy": {
                    "mean": float(np.mean(correctness_values)),
                    "total_correct": int(sum(correctness_values)),
                    "total_interactions": len(correctness_values)
                }
            }
        
        # Find best performing configuration
        best_config = None
        best_accuracy = 0
        for config_key, config_data in summary["configurations"].items():
            if config_data["accuracy"]["mean"] > best_accuracy:
                best_accuracy = config_data["accuracy"]["mean"]
                best_config = config_key
        
        summary["best_performer"] = {
            "configuration": best_config,
            "accuracy": best_accuracy
        }
        
        logger.info(f"📈 Retrieved summary for experiment: {experiment['name']} ({experiment_id})")
        
        return {
            "experiment_id": experiment_id,
            "experiment_name": experiment["name"],
            "summary": summary,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get experiment summary: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve experiment summary")
