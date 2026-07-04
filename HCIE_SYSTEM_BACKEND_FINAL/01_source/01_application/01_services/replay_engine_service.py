"""
Replay Engine Service

Separate service for enabling exact reconstruction of experiment runs for validation and debugging.
Provides API endpoints for deterministic replay as specified in EXPERIMENT_INFRASTRUCTURE_DESIGN.md.

Design Principles:
- Separate service (not integrated into existing code)
- Provides REST API for replay operations
- Uses existing ReplayEngine class for replay logic
- Supports replay by experiment_id, cohort_id, or individual learner
- Deterministic reconstruction (same seeds → same results)
- Projection verification
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import uuid

from infrastructure.experiment.replay_engine import ReplayEngine
from infrastructure.experiment.trajectory_recorder import TrajectoryRecorder
from core.learning.unified_brain import UnifiedLearningBrain
from storage.postgres_store.interaction_store import PostgresInteractionStore

logger = logging.getLogger(__name__)


class ReplayEngineService:
    """
    Service for deterministic replay with API interface
    
    RESPONSIBILITIES:
    - Provide REST API for replay operations
    - Replay by experiment_id, cohort_id, or individual learner
    - Deterministic reconstruction (same seeds → same results)
    - Projection verification (semantic projections match replay)
    - Measure stochastic cognition divergence
    """
    
    def __init__(self):
        """Initialize replay engine service"""
        self.db_store = PostgresInteractionStore()
        self.trajectory_recorder = TrajectoryRecorder(self.db_store)
        self.unified_brain = UnifiedLearningBrain(trajectory_recorder=self.trajectory_recorder)
        self.replay_engine = ReplayEngine(self.unified_brain, self.trajectory_recorder)
        
        # Store replay results
        self.active_replays: Dict[str, Dict[str, Any]] = {}
    
    def replay_trajectory(
        self,
        experiment_id: str,
        cohort_id: Optional[str] = None,
        learner_id: Optional[str] = None,
        interaction_range: Optional[List[int]] = None,
        verify_projections: bool = True
    ) -> Dict[str, Any]:
        """
        Replay trajectory with deterministic reconstruction
        
        API: POST /experiments/replay
        
        Args:
            experiment_id: Experiment identifier
            cohort_id: Optional cohort identifier
            learner_id: Optional learner identifier
            interaction_range: Interaction range to replay [start, end]
            verify_projections: Whether to verify projection consistency
            
        Returns:
            Replay results with divergence detection and projection verification
        """
        try:
            # Generate replay ID
            replay_id = str(uuid.uuid4())
            
            # Retrieve original trajectory from database
            original_trajectory = self._retrieve_trajectory(
                experiment_id=experiment_id,
                cohort_id=cohort_id,
                learner_id=learner_id,
                interaction_range=interaction_range
            )
            
            if not original_trajectory:
                raise ValueError(f"No trajectory found for experiment {experiment_id}")
            
            # Get concept from trajectory
            concept = original_trajectory[0].get("concept") if original_trajectory else "unknown"
            user_id = original_trajectory[0].get("user_id") if original_trajectory else "unknown"
            experiment_run_id = original_trajectory[0].get("experiment_run_id") if original_trajectory else "unknown"
            
            # Perform replay
            replay_result = self.replay_engine.replay_trajectory(
                experiment_run_id=experiment_run_id,
                user_id=user_id,
                concept=concept,
                original_trajectory=original_trajectory
            )
            
            # Perform projection verification if requested
            projection_verification = None
            if verify_projections:
                projection_verification = self._verify_projections(
                    original_trajectory,
                    replay_result.get("reconstructed_trajectory", [])
                )
            
            # Check for divergence
            divergence_detected = replay_result.get("divergence_detected", False)
            
            # Format response according to API specification
            response = {
                "replay_id": replay_id,
                "status": "success" if not divergence_detected else "divergence_detected",
                "divergence_detected": divergence_detected,
                "projection_verification": projection_verification,
                "reconstructed_state": replay_result.get("reconstructed_state", {}),
                "divergence_metrics": replay_result.get("divergence_metrics", {}),
                "replay_metadata": replay_result.get("replay_metadata", {}),
                "experiment_id": experiment_id,
                "cohort_id": cohort_id,
                "learner_id": learner_id,
                "interaction_range": interaction_range,
                "replayed_at": datetime.now().isoformat()
            }
            
            # Store replay result
            self.active_replays[replay_id] = response
            
            logger.info(f"Replay {replay_id} completed for experiment {experiment_id}")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to replay trajectory for experiment {experiment_id}: {e}")
            raise
    
    def _retrieve_trajectory(
        self,
        experiment_id: str,
        cohort_id: Optional[str] = None,
        learner_id: Optional[str] = None,
        interaction_range: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve trajectory from database
        
        Args:
            experiment_id: Experiment identifier
            cohort_id: Optional cohort identifier
            learner_id: Optional learner identifier
            interaction_range: Interaction range to retrieve
            
        Returns:
            List of trajectory records
        """
        try:
            # Build query
            # Authority migrated from ``trajectory_records`` (now empty) to
            # ``experiment_trajectories`` — the canonical per-attempt table
            # the trajectory_recorder consumer writes for both live and
            # synthetic learners. Same columns, just different table name.
            query = "SELECT * FROM experiment_trajectories WHERE experiment_run_id = %s"
            params = [experiment_id]
            
            if cohort_id:
                # Filter by cohort (via user_id pattern)
                query += " AND user_id LIKE %s"
                params.append(f"%{cohort_id}%")
            
            if learner_id:
                query += " AND user_id = %s"
                params.append(learner_id)
            
            if interaction_range:
                query += " AND interaction_number BETWEEN %s AND %s"
                params.extend(interaction_range)
            
            query += " ORDER BY interaction_number ASC"
            
            # Execute query
            trajectories = self.db_store.execute_read(query, tuple(params))
            
            return trajectories if trajectories else []
            
        except Exception as e:
            logger.error(f"Failed to retrieve trajectory: {e}")
            return []
    
    def _verify_projections(
        self,
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
    
    def get_replay_status(self, replay_id: str) -> Dict[str, Any]:
        """
        Get replay status
        
        Args:
            replay_id: Replay identifier
            
        Returns:
            Replay status
        """
        if replay_id not in self.active_replays:
            raise ValueError(f"Replay {replay_id} not found")
        
        return self.active_replays[replay_id]


def main():
    """Main entry point for replay engine service"""
    import os
    from fastapi import FastAPI
    from pydantic import BaseModel
    
    # Create FastAPI app
    app = FastAPI(title="Replay Engine Service")
    
    # Initialize service
    service = ReplayEngineService()
    
    # Pydantic models for API
    class ReplayRequest(BaseModel):
        experiment_id: str
        cohort_id: Optional[str] = None
        learner_id: Optional[str] = None
        interaction_range: Optional[List[int]] = None
        verify_projections: bool = True
    
    # API endpoints
    @app.post("/experiments/replay")
    async def replay(request: ReplayRequest):
        """Replay trajectory with deterministic reconstruction"""
        return service.replay_trajectory(
            experiment_id=request.experiment_id,
            cohort_id=request.cohort_id,
            learner_id=request.learner_id,
            interaction_range=request.interaction_range,
            verify_projections=request.verify_projections
        )
    
    @app.get("/experiments/replay/{replay_id}")
    async def get_replay_status(replay_id: str):
        """Get replay status"""
        return service.get_replay_status(replay_id)
    
    # Run service
    import uvicorn
    port = int(os.getenv("REPLAY_ENGINE_PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
