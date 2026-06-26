"""
Trajectory API - Query and Replay for Research and Debugging
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from storage.postgres_store.interaction_store import PostgresInteractionStore
from app.api.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trajectory", tags=["trajectory"])

def get_postgres_store() -> PostgresInteractionStore:
    """Dependency injection for postgres store"""
    return PostgresInteractionStore()

@router.get("/run/{experiment_run_id}")
def get_experiment_trajectory(
    experiment_run_id: str,
    user_id: Optional[str] = None,
    concept: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    postgres_store: PostgresInteractionStore = Depends(get_postgres_store),
    current_user: dict = Depends(get_current_user)
):
    """Get trajectory for an experiment run (with optional filters)"""
    
    try:
        # Build query
        conditions = ["experiment_run_id = %s"]
        values = [experiment_run_id]
        
        if user_id:
            conditions.append("user_id = %s")
            values.append(user_id)
        
        if concept:
            conditions.append("concept = %s")
            values.append(concept)
        
        where_clause = " AND ".join(conditions)
        sql = f"""
        SELECT * FROM experiment_trajectories
        WHERE {where_clause}
        ORDER BY interaction_number
        LIMIT %s
        """
        values.append(limit)
        
        results = postgres_store.execute_query(sql, tuple(values))
        
        logger.info(f"🔥 Trajectory accessed: {experiment_run_id} ({len(results)} records) by {current_user.get('user_id')}")
        return {
            "experiment_run_id": experiment_run_id,
            "user_id": user_id,
            "concept": concept,
            "total_records": len(results),
            "trajectories": results
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve trajectory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")
def get_user_trajectories(
    user_id: str,
    concept: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    postgres_store: PostgresInteractionStore = Depends(get_postgres_store),
    current_user: dict = Depends(get_current_user)
):
    """Get all trajectories for a user (longitudinal analysis)"""
    
    try:
        conditions = ["user_id = %s"]
        values = [user_id]
        
        if concept:
            conditions.append("concept = %s")
            values.append(concept)
        
        where_clause = " AND ".join(conditions)
        sql = f"""
        SELECT * FROM experiment_trajectories
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT %s
        """
        values.append(limit)
        
        results = postgres_store.execute_query(sql, tuple(values))
        
        # Calculate metrics
        if results:
            mastery_changes = []
            for r in results:
                if r.get("mastery_before") is not None and r.get("mastery_after") is not None:
                    mastery_changes.append(abs(r["mastery_after"] - r["mastery_before"]))
            
            avg_mastery_change = sum(mastery_changes) / len(mastery_changes) if mastery_changes else 0.0
            total_learning_events = len(results)
        else:
            avg_mastery_change = 0.0
            total_learning_events = 0
        
        logger.info(f"🔥 User trajectories accessed: {user_id} ({len(results)} records) by {current_user.get('user_id')}")
        return {
            "user_id": user_id,
            "concept": concept,
            "total_records": len(results),
            "total_learning_events": total_learning_events,
            "avg_mastery_change": avg_mastery_change,
            "trajectories": results
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve user trajectories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/concept/{concept}")
def get_concept_trajectories(
    concept: str,
    limit: int = Query(default=50, le=500),
    postgres_store: PostgresInteractionStore = Depends(get_postgres_store),
    current_user: dict = Depends(get_current_user)
):
    """Get all trajectories for a concept (concept-level analysis)"""
    
    try:
        sql = """
        SELECT * FROM experiment_trajectories
        WHERE concept = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        results = postgres_store.execute_query(sql, (concept, limit))
        
        # Aggregate by user
        user_stats = {}
        for r in results:
            uid = r.get("user_id")
            if uid not in user_stats:
                user_stats[uid] = {
                    "user_id": uid,
                    "total_interactions": 0,
                    "mastery_before_sum": 0.0,
                    "mastery_after_sum": 0.0
                }
            user_stats[uid]["total_interactions"] += 1
            if r.get("mastery_before"):
                user_stats[uid]["mastery_before_sum"] += r["mastery_before"]
            if r.get("mastery_after"):
                user_stats[uid]["mastery_after_sum"] += r["mastery_after"]
        
        # Calculate averages
        for uid, stats in user_stats.items():
            if stats["total_interactions"] > 0:
                stats["avg_mastery_before"] = stats["mastery_before_sum"] / stats["total_interactions"]
                stats["avg_mastery_after"] = stats["mastery_after_sum"] / stats["total_interactions"]
            else:
                stats["avg_mastery_before"] = 0.0
                stats["avg_mastery_after"] = 0.0
        
        logger.info(f"🔥 Concept trajectories accessed: {concept} ({len(results)} records) by {current_user.get('user_id')}")
        return {
            "concept": concept,
            "total_records": len(results),
            "unique_users": len(user_stats),
            "user_statistics": list(user_stats.values()),
            "trajectories": results
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve concept trajectories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/replay")
def replay_trajectory(
    experiment_run_id: str,
    user_id: str,
    concept: str,
    postgres_store: PostgresInteractionStore = Depends(get_postgres_store),
    current_user: dict = Depends(get_current_user)
):
    """
    Replay a trajectory for debugging and validation
    
    Returns the sequence of states and interactions for the specified trajectory
    """
    
    try:
        sql = """
        SELECT * FROM experiment_trajectories
        WHERE experiment_run_id = %s AND user_id = %s AND concept = %s
        ORDER BY interaction_number
        """
        results = postgres_store.execute_query(sql, (experiment_run_id, user_id, concept))
        
        if not results:
            raise HTTPException(status_code=404, detail="Trajectory not found")
        
        # Build replay sequence
        replay_sequence = []
        for r in results:
            replay_sequence.append({
                "interaction_number": r["interaction_number"],
                "state_before": {
                    "mastery": r.get("mastery_before"),
                    "uncertainty": r.get("uncertainty_before"),
                    "confidence": r.get("confidence_before"),
                    "lyapunov_mastery": r.get("lyapunov_mastery_before"),
                    "bayesian_alpha": r.get("bayesian_alpha_before"),
                    "bayesian_beta": r.get("bayesian_beta_before"),
                    "kalman_mastery": r.get("kalman_mastery_before"),
                    "kalman_covariance": r.get("kalman_covariance_before")
                },
                "interaction": {
                    "correctness": r.get("correctness"),
                    "response_time": r.get("response_time"),
                    "difficulty": r.get("difficulty"),
                    "policy": r.get("policy"),
                    "arm_selected": r.get("arm_selected")
                },
                "state_after": {
                    "mastery": r.get("mastery_after"),
                    "uncertainty": r.get("uncertainty_after"),
                    "confidence": r.get("confidence_after"),
                    "lyapunov_mastery": r.get("lyapunov_mastery_after"),
                    "bayesian_alpha": r.get("bayesian_alpha_after"),
                    "bayesian_beta": r.get("bayesian_beta_after"),
                    "kalman_mastery": r.get("kalman_mastery_after"),
                    "kalman_covariance": r.get("kalman_covariance_after")
                },
                "governance_signals": {
                    "jt_value": r.get("jt_value"),
                    "jt_volatility": r.get("jt_volatility"),
                    "stability_index": r.get("stability_index"),
                    "exploration_pressure": r.get("exploration_pressure"),
                    "transfer_amount": r.get("transfer_amount"),
                    "transfer_efficiency": r.get("transfer_efficiency"),
                    "zpd_target": r.get("zpd_target"),
                    "zpd_alignment_error": r.get("zpd_alignment_error"),
                    "zpd_score": r.get("zpd_score")
                },
                "metadata": {
                    "processing_time": r.get("processing_time"),
                    "timestamp": r.get("timestamp")
                }
            })
        
        logger.info(f"🔥 Trajectory replay: {experiment_run_id}/{user_id}/{concept} ({len(replay_sequence)} steps) by {current_user.get('user_id')}")
        return {
            "experiment_run_id": experiment_run_id,
            "user_id": user_id,
            "concept": concept,
            "total_steps": len(replay_sequence),
            "replay_sequence": replay_sequence
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to replay trajectory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/summary")
def get_trajectory_analytics(
    experiment_run_id: Optional[str] = None,
    postgres_store: PostgresInteractionStore = Depends(get_postgres_store),
    current_user: dict = Depends(get_current_user)
):
    """Get trajectory analytics summary (aggregated metrics)"""
    
    try:
        conditions = []
        values = []
        
        if experiment_run_id:
            conditions.append("experiment_run_id = %s")
            values.append(experiment_run_id)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"""
        SELECT 
            COUNT(*) as total_trajectories,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT concept) as unique_concepts,
            AVG(mastery_after - mastery_before) as avg_mastery_delta,
            AVG(processing_time) as avg_processing_time,
            AVG(jt_value) as avg_jt_value,
            AVG(transfer_amount) as avg_transfer_amount,
            AVG(zpd_score) as avg_zpd_score
        FROM experiment_trajectories
        WHERE {where_clause}
        """
        
        result = postgres_store.execute_query(sql, tuple(values), fetch_one=True)
        
        logger.info(f"🔥 Trajectory analytics accessed by {current_user.get('user_id')}")
        return result or {}
        
    except Exception as e:
        logger.error(f"❌ Failed to get trajectory analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
