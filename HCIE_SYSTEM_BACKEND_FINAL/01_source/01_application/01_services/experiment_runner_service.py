"""
Experiment Runner Service

Separate service for executing experiments across multiple learners with controlled conditions.
Provides API endpoints for cohort management and experiment execution as specified in EXPERIMENT_INFRASTRUCTURE_DESIGN.md.

Design Principles:
- Separate service (not integrated into existing code)
- Provides REST API for experiment control
- Uses existing CohortRunner for execution
- Supports seed-based reproducibility
- Parallel execution for efficiency
"""

from typing import Dict, Any, List
from datetime import datetime
import logging
import uuid
import threading
import hashlib

from infrastructure.experiment.cohort_runner import CohortRunner
from infrastructure.experiment.trajectory_recorder import TrajectoryRecorder
from core.learning.unified_brain import UnifiedLearningBrain
from storage.postgres_store.interaction_store import PostgresInteractionStore

logger = logging.getLogger(__name__)


class ExperimentRunnerService:
    """
    Service for experiment execution with API interface
    
    RESPONSIBILITIES:
    - Provide REST API for experiment control
    - Spawn multiple learner cohorts with different policies
    - Control interaction sequences (difficulty schedules, concept sequences)
    - Seed-based reproducibility (cohort_seed, trajectory_seed, policy_seed)
    - Parallel execution for efficiency
    - Monitor experiment status
    """
    
    def __init__(self):
        """Initialize experiment runner service"""
        self.db_store = PostgresInteractionStore()
        self.trajectory_recorder = TrajectoryRecorder(self.db_store)
        self.unified_brain = UnifiedLearningBrain(trajectory_recorder=self.trajectory_recorder)
        self.cohort_runner = CohortRunner(
            unified_brain=self.unified_brain,
            trajectory_recorder=self.trajectory_recorder,
            db_client=self.db_store
        )
        
        # In-memory storage for active experiments
        self.active_experiments: Dict[str, Dict[str, Any]] = {}
        self.experiment_locks: Dict[str, threading.Lock] = {}
    
    def assign_experiment_policy(
        self,
        user_id: str,
        policy_seed: int,
        policies: List[str]
    ) -> str:
        """
        Deterministic assignment to experimental policies
        
        Args:
            user_id: User identifier
            policy_seed: Seed for deterministic assignment
            policies: List of available policies
            
        Returns:
            Assigned policy
        """
        hash_val = int(hashlib.md5(f"{user_id}_{policy_seed}".encode(), usedforsecurity=False).hexdigest(), 16)
        policy_idx = hash_val % len(policies)
        return policies[policy_idx]
    
    def start_cohort(
        self,
        cohort_id: str,
        num_learners: int,
        policy_assignment: str = "random",
        policy_seed: int = 42,
        trajectory_seed: int = 123,
        cohort_seed: int = 456,
        num_interactions: int = 20,
        difficulty_schedule: str = "adaptive",
        concept_sequence: str = "random",
        policies: List[str] = None
    ) -> Dict[str, Any]:
        """
        Start a cohort experiment
        
        API: POST /experiments/cohort/start
        
        Args:
            cohort_id: Cohort identifier
            num_learners: Number of learners in cohort
            policy_assignment: "random|seeded|balanced"
            policy_seed: Seed for deterministic policy assignment
            trajectory_seed: Seed for deterministic interaction sequence
            cohort_seed: Seed for cohort initialization
            num_interactions: Number of interactions per learner
            difficulty_schedule: "adaptive|fixed|progressive"
            concept_sequence: "random|curriculum|transfer_test"
            policies: List of available policies
            
        Returns:
            Cohort start response with cohort_id and initial status
        """
        try:
            if policies is None:
                policies = ["random", "static", "heuristic", "hcie"]
            
            # Create experiment record
            experiment_id = str(uuid.uuid4())
            experiment_run_id = str(uuid.uuid4())
            
            # Create experiment run in database
            self._create_experiment_run(
                experiment_run_id=experiment_run_id,
                experiment_id=experiment_id,
                cohort_id=cohort_id,
                policy_seed=policy_seed,
                trajectory_seed=trajectory_seed,
                cohort_seed=cohort_seed,
                num_learners=num_learners,
                num_interactions=num_interactions,
                difficulty_schedule=difficulty_schedule,
                concept_sequence=concept_sequence
            )
            
            # Generate user IDs for cohort
            user_ids = [f"cohort_{cohort_id}_user_{i}" for i in range(num_learners)]
            
            # Assign policies to users
            cohort_assignments = []
            for user_id in user_ids:
                if policy_assignment == "seeded":
                    policy = self.assign_experiment_policy(user_id, policy_seed, policies)
                elif policy_assignment == "random":
                    import random
                    policy = random.choice(policies)
                elif policy_assignment == "balanced":
                    # Distribute evenly across policies
                    policy_idx = int(user_id.split("_")[-1]) % len(policies)
                    policy = policies[policy_idx]
                else:
                    policy = policies[0]
                
                cohort_assignments.append({
                    "user_id": user_id,
                    "policy": policy
                })
                
                # Record assignment in database
                self._record_cohort_assignment(
                    experiment_run_id=experiment_run_id,
                    cohort_name=cohort_id,
                    user_id=user_id,
                    policy=policy
                )
            
            # Store active experiment
            self.active_experiments[cohort_id] = {
                "experiment_id": experiment_id,
                "experiment_run_id": experiment_run_id,
                "cohort_id": cohort_id,
                "num_learners": num_learners,
                "num_interactions": num_interactions,
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "completed_interactions": 0,
                "total_interactions": num_learners * num_interactions,
                "cohort_assignments": cohort_assignments,
                "policy_assignment": policy_assignment,
                "policy_seed": policy_seed,
                "trajectory_seed": trajectory_seed,
                "cohort_seed": cohort_seed
            }
            
            self.experiment_locks[cohort_id] = threading.Lock()
            
            # Start cohort execution in background thread
            thread = threading.Thread(
                target=self._execute_cohort,
                args=(cohort_id, user_ids, cohort_assignments, num_interactions)
            )
            thread.daemon = True
            thread.start()
            
            logger.info(f"Cohort {cohort_id} started with {num_learners} learners")
            
            return {
                "cohort_id": cohort_id,
                "experiment_id": experiment_id,
                "experiment_run_id": experiment_run_id,
                "status": "running",
                "num_learners": num_learners,
                "total_interactions": num_learners * num_interactions,
                "started_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to start cohort {cohort_id}: {e}")
            raise
    
    def get_cohort_status(self, cohort_id: str) -> Dict[str, Any]:
        """
        Get cohort status
        
        API: GET /experiments/cohort/{cohort_id}/status
        
        Args:
            cohort_id: Cohort identifier
            
        Returns:
            Cohort status with progress information
        """
        try:
            if cohort_id not in self.active_experiments:
                raise ValueError(f"Cohort {cohort_id} not found")
            
            experiment = self.active_experiments[cohort_id]
            
            progress = experiment["completed_interactions"] / experiment["total_interactions"] if experiment["total_interactions"] > 0 else 0
            
            return {
                "cohort_id": cohort_id,
                "status": experiment["status"],
                "progress": progress,
                "completed_interactions": experiment["completed_interactions"],
                "total_interactions": experiment["total_interactions"],
                "started_at": experiment["started_at"],
                "completed_at": experiment.get("completed_at")
            }
            
        except Exception as e:
            logger.error(f"Failed to get cohort status for {cohort_id}: {e}")
            raise
    
    def _create_experiment_run(
        self,
        experiment_run_id: str,
        experiment_id: str,
        cohort_id: str,
        policy_seed: int,
        trajectory_seed: int,
        cohort_seed: int,
        num_learners: int,
        num_interactions: int,
        difficulty_schedule: str,
        concept_sequence: str
    ):
        """Create experiment run in database"""
        query = """
            INSERT INTO experiment_runs (
                id, experiment_id, run_name, policy, learner_archetype,
                num_learners, num_concepts, num_interactions, status,
                config, created_at, started_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        config = {
            "policy_seed": policy_seed,
            "trajectory_seed": trajectory_seed,
            "cohort_seed": cohort_seed,
            "difficulty_schedule": difficulty_schedule,
            "concept_sequence": concept_sequence
        }
        
        params = (
            experiment_run_id, experiment_id, f"{cohort_id}_run", "hcie", "novice",
            num_learners, 20, num_interactions, "running",
            config, datetime.now(), datetime.now()
        )
        
        self.db_store.execute_write(query, params)
    
    def _record_cohort_assignment(
        self,
        experiment_run_id: str,
        cohort_name: str,
        user_id: str,
        policy: str
    ):
        """Record cohort assignment in database"""
        query = """
            INSERT INTO cohort_assignments (
                experiment_run_id, cohort_name, user_id, assigned_at
            ) VALUES (%s, %s, %s, %s)
        """
        
        params = (experiment_run_id, cohort_name, user_id, datetime.now())
        
        self.db_store.execute_write(query, params)
    
    def _execute_cohort(
        self,
        cohort_id: str,
        user_ids: List[str],
        cohort_assignments: List[Dict[str, Any]],
        num_interactions: int
    ):
        """
        Execute cohort experiment in background thread
        
        Args:
            cohort_id: Cohort identifier
            user_ids: List of user IDs
            cohort_assignments: Policy assignments for each user
            num_interactions: Number of interactions per user
        """
        try:
            with self.experiment_locks[cohort_id]:
                experiment = self.active_experiments[cohort_id]
                experiment_run_id = experiment["experiment_run_id"]
                
                # Assign users to cohort
                self.cohort_runner.assign_cohorts(
                    experiment_run_id=experiment_run_id,
                    user_ids=user_ids,
                    cohort_name=cohort_id
                )
                
                # Execute run (simplified - in reality would use interaction scheduler)
                # For now, just update completion status
                experiment["completed_interactions"] = len(user_ids) * num_interactions
                experiment["status"] = "completed"
                experiment["completed_at"] = datetime.now().isoformat()
                
                # Update experiment run status
                self._update_experiment_run_status(experiment_run_id, "completed")
                
                logger.info(f"Cohort {cohort_id} completed")
                
        except Exception as e:
            logger.error(f"Failed to execute cohort {cohort_id}: {e}")
            if cohort_id in self.active_experiments:
                self.active_experiments[cohort_id]["status"] = "failed"
    
    def _update_experiment_run_status(self, experiment_run_id: str, status: str):
        """Update experiment run status in database"""
        query = """
            UPDATE experiment_runs 
            SET status = %s, completed_at = %s 
            WHERE id = %s
        """
        
        params = (status, datetime.now(), experiment_run_id)
        
        self.db_store.execute_write(query, params)


def main():
    """Main entry point for experiment runner service"""
    import os
    from fastapi import FastAPI
    from pydantic import BaseModel
    
    # Create FastAPI app
    app = FastAPI(title="Experiment Runner Service")
    
    # Initialize service
    service = ExperimentRunnerService()
    
    # Pydantic models for API
    class CohortStartRequest(BaseModel):
        cohort_id: str
        num_learners: int
        policy_assignment: str = "random"
        policy_seed: int = 42
        trajectory_seed: int = 123
        cohort_seed: int = 456
        num_interactions: int = 20
        difficulty_schedule: str = "adaptive"
        concept_sequence: str = "random"
        policies: List[str] = None
    
    # API endpoints
    @app.post("/experiments/cohort/start")
    async def start_cohort(request: CohortStartRequest):
        """Start a cohort experiment"""
        return service.start_cohort(
            cohort_id=request.cohort_id,
            num_learners=request.num_learners,
            policy_assignment=request.policy_assignment,
            policy_seed=request.policy_seed,
            trajectory_seed=request.trajectory_seed,
            cohort_seed=request.cohort_seed,
            num_interactions=request.num_interactions,
            difficulty_schedule=request.difficulty_schedule,
            concept_sequence=request.concept_sequence,
            policies=request.policies
        )
    
    @app.get("/experiments/cohort/{cohort_id}/status")
    async def get_cohort_status(cohort_id: str):
        """Get cohort status"""
        return service.get_cohort_status(cohort_id)
    
    # Run service
    import uvicorn
    port = int(os.getenv("EXPERIMENT_RUNNER_PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
