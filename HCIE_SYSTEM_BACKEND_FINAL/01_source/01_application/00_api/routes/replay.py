"""
Replay Runtime API Endpoints

Provides deterministic replay functionality for research validation as specified in RUNTIME_CONTRACTS.md.
These endpoints enable counterfactual analysis and state reconstruction for experiment validation.

Design Principles:
- Deterministic replay (same events → same state)
- Counterfactual analysis (policy substitution → divergent state)
- Lineage preservation (causation_id, trace_id)
- Replay result retrieval
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from infrastructure.experiment.replay_engine import ReplayEngine
from infrastructure.experiment.trajectory_recorder import TrajectoryRecorder
from core.learning.unified_brain import UnifiedLearningBrain
from storage.postgres_store.interaction_store import PostgresInteractionStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/replay", tags=["replay"])


def get_postgres_store() -> PostgresInteractionStore:
    """Dependency injection for postgres store"""
    return PostgresInteractionStore()


# Pydantic models for API
class ReplayRequest(BaseModel):
    experiment_run_id: str
    user_id: str
    concept: str
    interaction_range: Optional[List[int]] = None
    verify_projections: bool = True
    counterfactual_policy: Optional[str] = None


class ReplayResponse(BaseModel):
    replay_id: str
    status: str
    divergence_detected: bool
    projection_verification: Optional[Dict[str, Any]]
    reconstructed_state: Dict[str, Any]
    divergence_metrics: Dict[str, Any]
    experiment_run_id: str
    user_id: str
    concept: str
    interaction_range: Optional[List[int]]
    replayed_at: str


# Store replay results (in production, use Redis)
active_replays: Dict[str, Dict[str, Any]] = {}


@router.post("/trigger/{session_id}")
async def trigger_replay(
    session_id: str,
    request: ReplayRequest,
    postgres_store: PostgresInteractionStore = Depends(get_postgres_store)
):
    """
    Trigger deterministic replay for a session
    
    API: POST /api/replay/trigger/{session_id}
    
    Args:
        session_id: Session identifier
        request: Replay request parameters
        
    Returns:
        Replay response with replay_id for result retrieval
    """
    try:
        # Generate replay ID
        replay_id = str(uuid.uuid4())
        
        # Initialize replay components
        trajectory_recorder = TrajectoryRecorder(postgres_store)
        unified_brain = UnifiedLearningBrain(trajectory_recorder=trajectory_recorder)
        replay_engine = ReplayEngine(unified_brain, trajectory_recorder)
        
        # Retrieve original trajectory from database
        original_trajectory = _retrieve_trajectory(
            postgres_store=postgres_store,
            experiment_run_id=request.experiment_run_id,
            user_id=request.user_id,
            concept=request.concept,
            interaction_range=request.interaction_range
        )
        
        if not original_trajectory:
            raise HTTPException(
                status_code=404,
                detail=f"No trajectory found for experiment {request.experiment_run_id}"
            )
        
        # Perform replay
        replay_result = replay_engine.replay_trajectory(
            experiment_run_id=request.experiment_run_id,
            user_id=request.user_id,
            concept=request.concept,
            original_trajectory=original_trajectory,
            counterfactual_policy=request.counterfactual_policy
        )
        
        # Perform projection verification if requested
        projection_verification = None
        if request.verify_projections:
            projection_verification = _verify_projections(
                original_trajectory,
                replay_result.get("reconstructed_trajectory", [])
            )
        
        # Check for divergence
        divergence_detected = replay_result.get("divergence_detected", False)
        
        # Format response
        response = {
            "replay_id": replay_id,
            "status": "success" if not divergence_detected else "divergence_detected",
            "divergence_detected": divergence_detected,
            "projection_verification": projection_verification,
            "reconstructed_state": replay_result.get("reconstructed_state", {}),
            "divergence_metrics": replay_result.get("divergence_metrics", {}),
            "experiment_run_id": request.experiment_run_id,
            "user_id": request.user_id,
            "concept": request.concept,
            "interaction_range": request.interaction_range,
            "session_id": session_id,
            "replayed_at": datetime.now().isoformat()
        }
        
        # Store replay result
        active_replays[replay_id] = response
        
        logger.info(f"Replay {replay_id} triggered for session {session_id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger replay for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{replay_id}")
async def get_replay_result(replay_id: str):
    """
    Get replay result by replay_id
    
    API: GET /api/replay/result/{replay_id}
    
    Args:
        replay_id: Replay identifier
        
    Returns:
        Replay result
    """
    if replay_id not in active_replays:
        raise HTTPException(status_code=404, detail=f"Replay {replay_id} not found")
    
    logger.info(f"Replay result retrieved: {replay_id}")
    return active_replays[replay_id]


@router.get("/status")
async def get_replay_status():
    """
    Get status of all active replays
    
    API: GET /api/replay/status
    
    Returns:
        List of active replay statuses
    """
    return {
        "active_replays": len(active_replays),
        "replay_ids": list(active_replays.keys())
    }


def _retrieve_trajectory(
    postgres_store: PostgresInteractionStore,
    experiment_run_id: str,
    user_id: str,
    concept: str,
    interaction_range: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve trajectory from database
    
    Args:
        postgres_store: PostgreSQL store
        experiment_run_id: Experiment run identifier
        user_id: User identifier
        concept: Concept identifier
        interaction_range: Interaction range to retrieve
        
    Returns:
        List of trajectory records
    """
    try:
        # Build query - use trajectory_records table (not experiment_trajectories)
        query = """
            SELECT * FROM trajectory_records
            WHERE experiment_run_id = %s AND user_id = %s AND concept = %s
        """
        params = [experiment_run_id, user_id, concept]
        
        if interaction_range:
            query += " AND interaction_number BETWEEN %s AND %s"
            params.extend(interaction_range)
        
        query += " ORDER BY interaction_number ASC"
        
        # Execute query
        trajectories = postgres_store.execute_read(query, tuple(params))
        
        return trajectories if trajectories else []
        
    except Exception as e:
        logger.error(f"Failed to retrieve trajectory: {e}")
        return []


def _verify_projections(
    original_trajectory: List[Dict[str, Any]],
    reconstructed_trajectory: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Verify projection consistency between original and replay
    
    Args:
        original_trajectory: Original trajectory records
        reconstructed_trajectory: Reconstructed trajectory records
        
    Returns:
        Projection verification results
    """
    try:
        mismatch_count = 0
        
        # Compare trajectories point-by-point
        for i, (orig, recon) in enumerate(zip(original_trajectory, reconstructed_trajectory)):
            # Compare key fields
            if orig.get("jt_value") != recon.get("jt_value"):
                mismatch_count += 1
            
            if orig.get("mastery_after") != recon.get("mastery_after"):
                mismatch_count += 1
            
            if orig.get("uncertainty_after") != recon.get("uncertainty_after"):
                mismatch_count += 1
        
        verified = mismatch_count == 0
        
        return {
            "verified": verified,
            "mismatch_count": mismatch_count,
            "total_points": len(original_trajectory),
            "mismatch_rate": mismatch_count / len(original_trajectory) if original_trajectory else 0.0
        }
        
    except Exception as e:
        logger.error(f"Failed to verify projections: {e}")
        return {
            "verified": False,
            "mismatch_count": -1,
            "error": str(e)
        }
