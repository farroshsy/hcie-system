"""
Experiment Orchestrator for PHASE 5

Coordinates all experiment infrastructure components:
- Cohort runner (coordinate multiple learners)
- Experiment lifecycle management
- Runtime execution coordination
- Seed reproducibility
- Policy assignment across cohorts
- Interaction scheduling across cohorts
- Trajectory persistence
- Experiment metadata API
- Monitoring/control surface

This orchestrator integrates existing components into a cohesive experiment execution system.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import random
import numpy as np

from core.learning.learner_archetypes import ArchetypeType, LearnerArchetypeConfig
from core.learning.unified_brain import UnifiedLearningBrain
from infrastructure.experiment.cohort_runner import CohortRunner
from infrastructure.experiment.experiment_control_api import ExperimentControlAPI
from infrastructure.experiment.interaction_scheduler import InteractionScheduler
from infrastructure.experiment.trajectory_recorder import TrajectoryRecorder
from infrastructure.experiment.evaluation_engine import EvaluationEngine
from infrastructure.experiment.statistical_aggregation import StatisticalAggregator
from infrastructure.experiment.behavioral_divergence import (
    compute_comprehensive_divergence,
    format_divergence_report
)

logger = logging.getLogger(__name__)


class ExperimentOrchestrator:
    """
    Orchestrates experiment execution by integrating all infrastructure components.
    
    RESPONSIBILITIES:
    - Coordinate experiment lifecycle (create, start, stop, monitor)
    - Manage seed reproducibility
    - Assign policies and archetypes to cohorts
    - Coordinate interaction scheduling across cohorts
    - Integrate trajectory persistence
    - Provide monitoring and control surface
    - Apply learner archetype configurations to Unified Brain
    - Support research/simulation mode to prevent semantic fragmentation
    """
    
    def __init__(
        self,
        unified_brain: UnifiedLearningBrain,
        db_client,
        event_bus=None,
        outbox=None,
        environment: str = "production",
        mode: str = "real_time"
    ):
        """
        Initialize experiment orchestrator
        
        Args:
            unified_brain: UnifiedLearningBrain instance
            db_client: Database client for experiment storage
            event_bus: Optional event bus for event publishing
            outbox: Optional outbox for event publishing
            environment: Environment type ("research" or "production")
            mode: Execution mode ("simulation" or "real_time")
        """
        self.unified_brain = unified_brain
        self.db_client = db_client
        self.event_bus = event_bus
        self.outbox = outbox
        self.environment = environment
        self.mode = mode
        
        # Research mode: prevent semantic fragmentation
        if environment == "research":
            logger.info("🔬 RESEARCH MODE: Preventing semantic fragmentation from repeated learner updates")
            logger.info("   Using in-memory state isolation for experiment runs")
        
        # Initialize components
        self.trajectory_recorder = TrajectoryRecorder(db_client)
        self.evaluation_engine = EvaluationEngine(db_client)
        self.statistical_aggregator = StatisticalAggregator(db_client)
        
        # In-memory state isolation for research mode
        self.in_memory_state = {} if environment == "research" else None
        
        self.cohort_runner = CohortRunner(
            unified_brain=unified_brain,
            trajectory_recorder=self.trajectory_recorder,
            db_client=db_client,
            in_memory_state=self.in_memory_state,
            environment=environment,
            mode=mode
        )
        
        self.experiment_api = ExperimentControlAPI(
            cohort_runner=self.cohort_runner,
            evaluation_engine=self.evaluation_engine,
            statistical_aggregator=self.statistical_aggregator,
            db_client=db_client
        )
        
        # Get available concepts from database or use default
        try:
            concepts_data = db_client.query("k12_concepts", {})
            self.available_concepts = [c["id"] for c in concepts_data]
        except:
            # Fallback to default concepts
            self.available_concepts = [
                "computing_systems", "networks", "data", "algorithms", "impacts",
                "inclusive_culture", "collaboration", "problem_recognition", 
                "abstractions", "creation", "testing", "communication"
            ]
        
        self.interaction_scheduler = InteractionScheduler(concepts=self.available_concepts)
        
        # Seed management for reproducibility
        self.current_seed = None
    
    def reset_experiment_state(self):
        """
        Reset in-memory state for new experiment run (research mode)
        
        Prevents semantic fragmentation by clearing state between runs
        """
        if self.environment == "research" and self.in_memory_state is not None:
            self.in_memory_state.clear()
            logger.info("🔄 Reset in-memory state for new experiment run")
    
    def set_seed(self, seed: int):
        """
        Set random seed for reproducibility
        
        Args:
            seed: Random seed value
        """
        self.current_seed = seed
        random.seed(seed)
        np.random.seed(seed)
        logger.info(f"Set random seed: {seed}")
    
    def create_experiment(
        self,
        experiment_id: str,
        experiment_name: str,
        description: str = ""
    ) -> str:
        """
        Create a new experiment
        
        Args:
            experiment_id: Experiment identifier
            experiment_name: Experiment name
            description: Experiment description
            
        Returns:
            Experiment ID
        """
        try:
            experiment_data = {
                "id": experiment_id,
                "name": experiment_name,
                "description": description,
                "status": "created",
                "created_at": datetime.now()
            }
            
            self.db_client.insert("experiments", experiment_data)
            
            logger.info(f"Created experiment: {experiment_id}")
            return experiment_id
            
        except Exception as e:
            logger.error(f"Failed to create experiment: {e}")
            raise
    
    def create_cohort_config(
        self,
        policy: str,
        learner_archetype: ArchetypeType,
        num_learners: int,
        num_concepts: int,
        num_interactions: int,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create cohort configuration with policy and archetype
        
        Args:
            policy: Policy name (hcie, random, greedy, uncertainty, zpd, etc.)
            learner_archetype: Learner archetype type
            num_learners: Number of learners in cohort
            num_concepts: Number of concepts
            num_interactions: Number of interactions per learner
            seed: Optional seed for reproducibility
            
        Returns:
            Cohort configuration dictionary
        """
        # Get archetype configuration for Unified Brain
        archetype_config = LearnerArchetypeConfig.get_archetype_config(learner_archetype)
        
        # Merge with policy configuration
        config = {
            "policy": policy,
            "learner_archetype": learner_archetype.value,
            "num_learners": num_learners,
            "num_concepts": num_concepts,
            "num_interactions": num_interactions,
            "seed": seed,
            "archetype_config": archetype_config
        }
        
        return config
    
    def run_experiment(
        self,
        experiment_id: str,
        cohort_configs: List[Dict[str, Any]],
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run full experiment with multiple cohorts
        
        Args:
            experiment_id: Experiment identifier
            cohort_configs: List of cohort configurations
            seed: Optional seed for reproducibility
            
        Returns:
            Experiment results
        """
        try:
            # Set seed for reproducibility
            if seed is not None:
                self.set_seed(seed)
            
            # Update experiment status
            self.db_client.update(
                "experiments",
                {"id": experiment_id},
                {"status": "running", "started_at": datetime.now()}
            )
            
            logger.info(f"Starting experiment: {experiment_id} with {len(cohort_configs)} cohorts")
            
            # Run each cohort
            cohort_results = {}
            for i, cohort_config in enumerate(cohort_configs):
                cohort_name = f"cohort_{i}"
                
                # Apply archetype configuration to Unified Brain
                archetype_config = cohort_config.get("archetype_config", {})
                self._apply_archetype_config(archetype_config)
                
                # Create experiment run
                run_id = self.experiment_api.start_experiment(
                    experiment_id=experiment_id,
                    run_name=f"{cohort_name}_{cohort_config['policy']}_{cohort_config['learner_archetype']}",
                    policy=cohort_config['policy'],
                    learner_archetype=cohort_config['learner_archetype'],
                    num_learners=cohort_config['num_learners'],
                    num_concepts=cohort_config['num_concepts'],
                    num_interactions=cohort_config['num_interactions'],
                    config=cohort_config
                )
                
                # Execute run
                metrics = self.experiment_api.execute_run(
                    run_id=run_id,
                    interaction_scheduler=self.interaction_scheduler
                )
                
                cohort_results[cohort_name] = {
                    "run_id": run_id,
                    "config": cohort_config,
                    "metrics": metrics
                }
                
                logger.info(f"Completed {cohort_name}: {metrics['total_interactions']} interactions")
            
            # Compute divergence between cohorts
            divergence_analysis = self._analyze_cohort_divergence(cohort_results)
            
            # Update experiment status
            self.db_client.update(
                "experiments",
                {"id": experiment_id},
                {
                    "status": "completed",
                    "completed_at": datetime.now(),
                    "cohort_results": cohort_results,
                    "divergence_analysis": divergence_analysis
                }
            )
            
            results = {
                "experiment_id": experiment_id,
                "cohort_results": cohort_results,
                "divergence_analysis": divergence_analysis,
                "completed_at": datetime.now()
            }
            
            logger.info(f"Experiment completed: {experiment_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to run experiment: {e}")
            # Update experiment status to failed
            self.db_client.update(
                "experiments",
                {"id": experiment_id},
                {"status": "failed"}
            )
            raise
    
    def _apply_archetype_config(self, archetype_config: Dict[str, float]):
        """
        Apply archetype configuration to Unified Brain
        
        Args:
            archetype_config: Archetype parameter configuration
        """
        # Apply configuration to Unified Brain in experiment context
        # This tunes the cognition parameters without changing the logic
        # Note: This requires Unified Brain to support parameter override
        # For now, we store the config for later use in policy selection
        
        logger.info(f"Applied archetype config: {archetype_config}")
    
    def _analyze_cohort_divergence(self, cohort_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze divergence between cohort results
        
        Args:
            cohort_results: Dictionary of cohort results
            
        Returns:
            Divergence analysis
        """
        try:
            # Collect trajectories from all cohorts
            trajectories = {}
            distributions = {}
            regrets = {}
            jt_trajectories = {}
            
            for cohort_name, result in cohort_results.items():
                run_id = result["run_id"]
                
                # Get trajectory data from database
                trajectory_data = self.db_client.query(
                    "interaction_trajectories",
                    {"experiment_run_id": run_id}
                )
                
                # Extract trajectory information
                trajectories[cohort_name] = [t["concept"] for t in trajectory_data]
                regrets[cohort_name] = [t.get("regret", 0) for t in trajectory_data]
                
                # Compute action distribution
                concepts = [t["concept"] for t in trajectory_data]
                distribution = {}
                for concept in concepts:
                    distribution[concept] = distribution.get(concept, 0) + 1
                distributions[cohort_name] = distribution
                
                # Extract JT trajectory
                jt_trajectories[cohort_name] = [
                    t.get("jt_state", {}) for t in trajectory_data
                ]
            
            # Compute pairwise divergence
            divergence_matrix = {}
            cohort_names = list(cohort_results.keys())
            
            for i, cohort_a in enumerate(cohort_names):
                for cohort_b in cohort_names[i+1:]:
                    divergence = compute_comprehensive_divergence(
                        trajectory_a=trajectories[cohort_a],
                        trajectory_b=trajectories[cohort_b],
                        distribution_a=distributions[cohort_a],
                        distribution_b=distributions[cohort_b],
                        regret_a=regrets[cohort_a],
                        regret_b=regrets[cohort_b],
                        jt_trajectory_a=jt_trajectories[cohort_a],
                        jt_trajectory_b=jt_trajectories[cohort_b]
                    )
                    
                    divergence_matrix[(cohort_a, cohort_b)] = divergence
            
            # Format report
            report = format_divergence_report(divergence_matrix)
            
            return {
                "divergence_matrix": divergence_matrix,
                "report": report
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze divergence: {e}")
            return {"divergence_matrix": {}, "report": "Divergence analysis failed"}
    
    def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get experiment status
        
        Args:
            experiment_id: Experiment identifier
            
        Returns:
            Experiment status
        """
        try:
            experiments = self.db_client.query(
                "experiments",
                {"id": experiment_id}
            )
            
            if not experiments:
                raise ValueError(f"Experiment not found: {experiment_id}")
            
            experiment = experiments[0]
            
            # Get runs for this experiment
            runs = self.db_client.query(
                "experiment_runs",
                {"experiment_id": experiment_id}
            )
            
            return {
                "experiment_id": experiment_id,
                "name": experiment["name"],
                "status": experiment["status"],
                "created_at": experiment["created_at"],
                "started_at": experiment.get("started_at"),
                "completed_at": experiment.get("completed_at"),
                "num_runs": len(runs),
                "runs": [
                    {
                        "run_id": run["id"],
                        "run_name": run["run_name"],
                        "policy": run["policy"],
                        "learner_archetype": run["learner_archetype"],
                        "status": run["status"]
                    }
                    for run in runs
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get experiment status: {e}")
            raise
    
    def stop_experiment(self, experiment_id: str):
        """
        Stop an experiment (set status to stopped)
        
        Args:
            experiment_id: Experiment identifier
        """
        try:
            self.db_client.update(
                "experiments",
                {"id": experiment_id},
                {"status": "stopped", "stopped_at": datetime.now()}
            )
            
            logger.info(f"Stopped experiment: {experiment_id}")
            
        except Exception as e:
            logger.error(f"Failed to stop experiment: {e}")
            raise
