"""
Cohort Runner for Phase 1 Experiment Infrastructure

Executes experiments across multiple learners with configurable policies and archetypes.
Supports Contribution A (System Design), B (Decision-Making), C (Empirical Validation).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class CohortRunner:
    """
    Executes experiments across multiple learners
    
    RESPONSIBILITIES:
    - Assign learners to cohorts
    - Execute experiment runs
    - Coordinate with interaction scheduler
    - Record trajectories
    - Support multiple policies and learner archetypes
    """
    
    def __init__(self, unified_brain, trajectory_recorder, db_client, 
                 in_memory_state=None, environment="production", mode="real_time"):
        """
        Initialize cohort runner
        
        Args:
            unified_brain: UnifiedLearningBrain instance
            trajectory_recorder: TrajectoryRecorder instance
            db_client: Database client for experiment storage
            in_memory_state: In-memory state dict for research mode
            environment: Environment type ("research" or "production")
            mode: Execution mode ("simulation" or "real_time")
        """
        self.unified_brain = unified_brain
        self.trajectory_recorder = trajectory_recorder
        self.db_client = db_client
        self.in_memory_state = in_memory_state
        self.environment = environment
        self.mode = mode
    
    def create_experiment_run(
        self,
        experiment_id: str,
        run_name: str,
        policy: str,
        learner_archetype: str,
        num_learners: int,
        num_concepts: int,
        num_interactions: int,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new experiment run
        
        Args:
            experiment_id: Experiment identifier
            run_name: Run name
            policy: Policy to use (random, static, greedy, uncertainty, zpd, epsilon, ucb, thompson, hcie)
            learner_archetype: Learner archetype (novice, unstable, transfer_heavy, forgetting, exploration_sensitive, challenge_seeking)
            num_learners: Number of learners
            num_concepts: Number of concepts
            num_interactions: Number of interactions per learner
            config: Additional configuration
            
        Returns:
            Experiment run ID
        """
        try:
            run_config = {
                "policy": policy,
                "learner_archetype": learner_archetype,
                "num_learners": num_learners,
                "num_concepts": num_concepts,
                "num_interactions": num_interactions,
                **(config or {})
            }
            
            # Generate run ID
            run_id = str(uuid.uuid4())
            
            run_data = {
                "id": run_id,
                "experiment_id": experiment_id,
                "run_name": run_name,
                "policy": policy,
                "learner_archetype": learner_archetype,
                "num_learners": num_learners,
                "num_concepts": num_concepts,
                "num_interactions": num_interactions,
                "status": "pending",
                "config": run_config,
                "created_at": datetime.now()
            }
            
            self.db_client.insert("experiment_runs", run_data)
            
            logger.info(f"Created experiment run {run_id}: {policy} policy, {learner_archetype} archetype")
            
            return run_id
            
        except Exception as e:
            logger.error(f"Failed to create experiment run: {e}")
            raise
    
    def assign_cohorts(
        self,
        experiment_run_id: str,
        user_ids: List[str],
        cohort_name: str = "default"
    ):
        """
        Assign users to cohorts
        
        Args:
            experiment_run_id: Experiment run identifier
            user_ids: List of user IDs
            cohort_name: Cohort name
        """
        try:
            for user_id in user_ids:
                assignment_data = {
                    "experiment_run_id": experiment_run_id,
                    "cohort_name": cohort_name,
                    "user_id": user_id,
                    "assigned_at": datetime.now()
                }
                
                self.db_client.insert("cohort_assignments", assignment_data)
            
            logger.info(f"Assigned {len(user_ids)} users to cohort {cohort_name}")
            
        except Exception as e:
            logger.error(f"Failed to assign cohorts: {e}")
            raise
    
    def execute_run(
        self,
        experiment_run_id: str,
        interaction_scheduler
    ) -> Dict[str, Any]:
        """
        Execute an experiment run
        
        Args:
            experiment_run_id: Experiment run identifier
            interaction_scheduler: InteractionScheduler instance
            
        Returns:
            Execution metrics
        """
        try:
            # Update status to running
            self.db_client.update(
                "experiment_runs",
                {"id": experiment_run_id},
                {"status": "running", "started_at": datetime.now()}
            )
            
            # Get run configuration
            run = self.db_client.query(
                "experiment_runs",
                {"id": experiment_run_id}
            )[0]
            
            # Get cohort assignments
            assignments = self.db_client.query(
                "cohort_assignments",
                {"experiment_run_id": experiment_run_id}
            )
            
            user_ids = [a["user_id"] for a in assignments]
            config = run["config"]
            
            # Execute interactions for each user
            total_interactions = 0
            interaction_number = 0
            
            # Establish ownership context for experiment execution
            try:
                from core.ownership.ownership_enforcement import get_ownership_enforcement, CognitionWriter
                ownership = get_ownership_enforcement()
                ownership.set_writer(CognitionWriter.UNIFIED_BRAIN)
            except ImportError:
                logger.warning("⚠️  Ownership enforcement not available - proceeding without ownership context")
            
            for user_id in user_ids:
                for i in range(config["num_interactions"]):
                    interaction_number += 1
                    
                    # Schedule next interaction
                    scheduled = interaction_scheduler.schedule_next(
                        user_id=user_id,
                        config=config,
                        interaction_number=i + 1
                    )
                    
                    # Generate interaction data (simulate for experiment)
                    # Select a concept from the scheduler's concepts list
                    if hasattr(interaction_scheduler, 'concepts') and interaction_scheduler.concepts:
                        concept = interaction_scheduler.concepts[i % len(interaction_scheduler.concepts)]
                    else:
                        concept = "computing_systems"  # Default concept
                    
                    # Generate interaction data
                    interaction_data = interaction_scheduler.simulate_interaction_data(
                        concept=concept,
                        archetype=scheduled["archetype"],
                        interaction_number=interaction_number
                    )
                    
                    # Execute interaction
                    # Note: write_enabled=False for experiments - trajectories recorded to PostgreSQL, not Redis
                    result = self.unified_brain.process_event(
                        user_id=user_id,
                        concept=concept,
                        interaction=interaction_data,
                        mode="write",
                        event_id=f"{experiment_run_id}_{user_id}_{i}",
                        interaction_id=f"{experiment_run_id}_{user_id}_{i}",
                        write_enabled=False
                    )
                    
                    # Record trajectory
                    self.trajectory_recorder.record_interaction(
                        experiment_run_id=experiment_run_id,
                        user_id=user_id,
                        concept=concept,
                        interaction_id=f"{experiment_run_id}_{user_id}_{i}",
                        event_id=f"{experiment_run_id}_{user_id}_{i}",
                        interaction_number=interaction_number,
                        state_before=scheduled.get("state_before", {}),
                        state_after={
                            "mastery": result.mastery,
                            "uncertainty": result.uncertainty,
                            "confidence": result.confidence,
                            "lyapunov_mastery": result.lyapunov_mastery,
                            "bayesian_alpha": result.bayesian_alpha,
                            "bayesian_beta": result.bayesian_beta,
                            "kalman_mastery": result.kalman_mastery,
                            "kalman_covariance": result.kalman_covariance
                        },
                        interaction_data=interaction_data,
                        governance_signals={
                            "jt_value": result.J_value if hasattr(result, 'J_value') else None
                        }
                    )
                    
                    total_interactions += 1
            
            # Update status to completed
            self.db_client.update(
                "experiment_runs",
                {"id": experiment_run_id},
                {"status": "completed", "completed_at": datetime.now()}
            )
            
            metrics = {
                "total_interactions": total_interactions,
                "num_learners": len(user_ids),
                "interactions_per_learner": config["num_interactions"],
                "executed_at": datetime.now()
            }
            
            logger.info(f"Experiment run {experiment_run_id} completed: {total_interactions} interactions")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to execute run: {e}")
            # Update status to failed
            self.db_client.update(
                "experiment_runs",
                {"id": experiment_run_id},
                {"status": "failed"}
            )
            raise
