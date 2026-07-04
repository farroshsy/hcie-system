"""
Experiment Control API for Phase 1 Experiment Infrastructure

API for experiment control (start, stop, monitor, retrieve results).
Integrates with FastAPI for HTTP endpoints.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class ExperimentControlAPI:
    """
    API for experiment control
    
    RESPONSIBILITIES:
    - Start experiment runs
    - Stop experiment runs
    - Monitor experiment status
    - Retrieve experiment results
    - List experiments and runs
    """
    
    def __init__(self, cohort_runner, evaluation_engine, statistical_aggregator, db_client):
        """
        Initialize experiment control API
        
        Args:
            cohort_runner: CohortRunner instance
            evaluation_engine: EvaluationEngine instance
            statistical_aggregator: StatisticalAggregator instance
            db_client: Database client
        """
        self.cohort_runner = cohort_runner
        self.evaluation_engine = evaluation_engine
        self.statistical_aggregator = statistical_aggregator
        self.db_client = db_client
    
    def start_experiment(
        self,
        experiment_id: str,
        run_name: str,
        policy: str,
        learner_archetype: str,
        num_learners: int,
        num_concepts: int,
        num_interactions: int,
        user_ids: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a new experiment run
        
        Args:
            experiment_id: Experiment identifier
            run_name: Run name
            policy: Policy to use
            learner_archetype: Learner archetype
            num_learners: Number of learners
            num_concepts: Number of concepts
            num_interactions: Number of interactions per learner
            user_ids: Optional list of user IDs (auto-generated if not provided)
            config: Additional configuration
            
        Returns:
            Experiment run details
        """
        try:
            # Generate user IDs if not provided
            if not user_ids:
                user_ids = [f"learner_{i:04d}" for i in range(num_learners)]
            
            # Create experiment run
            run_id = self.cohort_runner.create_experiment_run(
                experiment_id=experiment_id,
                run_name=run_name,
                policy=policy,
                learner_archetype=learner_archetype,
                num_learners=num_learners,
                num_concepts=num_concepts,
                num_interactions=num_interactions,
                config=config
            )
            
            # Assign cohorts
            self.cohort_runner.assign_cohorts(
                experiment_run_id=run_id,
                user_ids=user_ids,
                cohort_name="default"
            )
            
            logger.info(f"Started experiment run {run_id}")
            
            return {
                "run_id": run_id,
                "experiment_id": experiment_id,
                "run_name": run_name,
                "policy": policy,
                "learner_archetype": learner_archetype,
                "num_learners": num_learners,
                "status": "created"
            }
            
        except Exception as e:
            logger.error(f"Failed to start experiment: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def execute_run(
        self,
        run_id: str,
        interaction_scheduler
    ) -> Dict[str, Any]:
        """
        Execute an experiment run
        
        Args:
            run_id: Experiment run identifier
            interaction_scheduler: InteractionScheduler instance
            
        Returns:
            Execution metrics
        """
        try:
            metrics = self.cohort_runner.execute_run(
                experiment_run_id=run_id,
                interaction_scheduler=interaction_scheduler
            )
            
            # Auto-evaluate after execution
            self.evaluation_engine.evaluate_experiment_run(run_id)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to execute run: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get experiment run status
        
        Args:
            run_id: Experiment run identifier
            
        Returns:
            Run status details
        """
        try:
            runs = self.db_client.query(
                "experiment_runs",
                {"id": run_id}
            )
            
            if not runs:
                raise HTTPException(status_code=404, detail="Run not found")
            
            run = runs[0]
            
            return {
                "run_id": run["id"],
                "status": run["status"],
                "started_at": run.get("started_at"),
                "completed_at": run.get("completed_at"),
                "config": run["config"]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get run status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_run_results(self, run_id: str) -> Dict[str, Any]:
        """
        Get experiment run results
        
        Args:
            run_id: Experiment run identifier
            
        Returns:
            Run results with metrics
        """
        try:
            runs = self.db_client.query(
                "experiment_runs",
                {"id": run_id}
            )
            
            if not runs:
                raise HTTPException(status_code=404, detail="Run not found")
            
            run = runs[0]
            
            return {
                "run_id": run["id"],
                "status": run["status"],
                "config": run["config"],
                "metrics": run.get("metrics"),
                "results": run.get("results")
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get run results: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def list_experiments(self) -> List[Dict[str, Any]]:
        """
        List all experiments
        
        Returns:
            List of experiments
        """
        try:
            experiments = self.db_client.query("experiments", {})
            
            return [
                {
                    "id": exp["id"],
                    "name": exp["name"],
                    "status": exp["status"],
                    "created_at": exp["created_at"]
                }
                for exp in experiments
            ]
            
        except Exception as e:
            logger.error(f"Failed to list experiments: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def list_runs(self, experiment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List experiment runs
        
        Args:
            experiment_id: Optional experiment filter
            
        Returns:
            List of experiment runs
        """
        try:
            query = {}
            if experiment_id:
                query["experiment_id"] = experiment_id
            
            runs = self.db_client.query("experiment_runs", query)
            
            return [
                {
                    "id": run["id"],
                    "experiment_id": run["experiment_id"],
                    "run_name": run["run_name"],
                    "policy": run["policy"],
                    "learner_archetype": run["learner_archetype"],
                    "status": run["status"],
                    "created_at": run["created_at"]
                }
                for run in runs
            ]
            
        except Exception as e:
            logger.error(f"Failed to list runs: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def aggregate_experiment_results(
        self,
        experiment_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Aggregate results across multiple experiments
        
        Args:
            experiment_ids: List of experiment identifiers
            
        Returns:
            Aggregated metrics
        """
        try:
            # Aggregate learning gain
            learning_gain = self.statistical_aggregator.aggregate_learning_gain(
                experiment_ids
            )
            
            # Aggregate regret
            regret = self.statistical_aggregator.aggregate_regret(
                experiment_ids
            )
            
            return {
                "learning_gain": learning_gain,
                "regret": regret,
                "aggregated_at": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to aggregate results: {e}")
            raise HTTPException(status_code=500, detail=str(e))
