"""
Evaluation Engine Service

Separate service for computing metrics across evaluation windows with statistical rigor.
Provides API endpoints for experiment evaluation as specified in EXPERIMENT_INFRASTRUCTURE_DESIGN.md.

Design Principles:
- Separate service (not integrated into existing code)
- Provides REST API for evaluation requests
- Uses existing EvaluationEngine class for computation
- Supports multiple evaluation windows and statistical methods
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

from infrastructure.experiment.evaluation_engine import EvaluationEngine
from storage.postgres_store.interaction_store import PostgresInteractionStore

logger = logging.getLogger(__name__)


class EvaluationEngineService:
    """
    Service for experiment evaluation with API interface
    
    RESPONSIBILITIES:
    - Provide REST API for evaluation requests
    - Compute metrics across evaluation windows
    - Support statistical testing and effect sizes
    - Generate confidence intervals
    - Aggregate across learners
    """
    
    def __init__(self):
        """Initialize evaluation engine service"""
        self.db_store = PostgresInteractionStore()
        self.evaluation_engine = EvaluationEngine(self.db_store)
    
    def evaluate_experiment(
        self,
        experiment_id: str,
        evaluation_windows: List[int] = None,
        metrics: List[str] = None,
        statistical_method: str = "frequentist",
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Evaluate an experiment with specified metrics and windows
        
        API: POST /experiments/evaluate
        
        Args:
            experiment_id: Experiment identifier
            evaluation_windows: List of interaction windows to evaluate (default: [5, 10, 20])
            metrics: List of metrics to compute (default: all)
            statistical_method: Statistical method ("frequentist" or "bayesian")
            confidence_level: Confidence level for intervals
            
        Returns:
            Evaluation results per window with statistical rigor
        """
        try:
            if evaluation_windows is None:
                evaluation_windows = [5, 10, 20]
            
            if metrics is None:
                metrics = ["learning_gain", "regret", "accuracy"]
            
            # Evaluate experiment run using existing EvaluationEngine
            results = self.evaluation_engine.evaluate_experiment_run(
                experiment_run_id=experiment_id,
                evaluation_windows=evaluation_windows,
                metrics=metrics,
                statistical_method=statistical_method,
                confidence_level=confidence_level
            )
            
            # Format response according to API specification
            formatted_response = {
                "experiment_id": experiment_id,
                "evaluation_windows": evaluation_windows,
                "metrics": metrics,
                "statistical_method": statistical_method,
                "confidence_level": confidence_level,
                "evaluated_at": results.get("evaluated_at"),
                "window_results": self._format_window_results(results, evaluation_windows)
            }
            
            logger.info(f"Evaluation completed for experiment {experiment_id}")
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Failed to evaluate experiment {experiment_id}: {e}")
            raise
    
    def _format_window_results(self, results: Dict[str, Any], windows: List[int]) -> Dict[str, Any]:
        """
        Format results according to API specification
        
        Args:
            results: Raw evaluation results
            windows: Evaluation windows
            
        Returns:
            Formatted results per window
        """
        window_results = {}
        
        for window in windows:
            window_key = f"window_{window}"
            window_data = {}
            
            # Extract learning gain metrics
            if "learning_gain" in results and window_key in results["learning_gain"]["window_metrics"]:
                lg_metrics = results["learning_gain"]["window_metrics"][window_key]
                window_data["learning_gain"] = {
                    "mean": lg_metrics["mean_learning_gain"],
                    "std": lg_metrics["std_learning_gain"],
                    "median": lg_metrics["median_learning_gain"],
                    "ci_lower": lg_metrics["confidence_interval"]["lower"],
                    "ci_upper": lg_metrics["confidence_interval"]["upper"],
                    "num_learners": lg_metrics["num_learners"]
                }
            
            # Extract regret metrics
            if "regret" in results and window_key in results["regret"]["window_metrics"]:
                regret_metrics = results["regret"]["window_metrics"][window_key]
                window_data["regret"] = {
                    "mean_cumulative_regret": regret_metrics["mean_cumulative_regret"],
                    "std_cumulative_regret": regret_metrics["std_cumulative_regret"],
                    "median_cumulative_regret": regret_metrics["median_cumulative_regret"],
                    "num_learners": regret_metrics["num_learners"]
                }
            
            # Extract stability metrics
            if "stability" in results and window_key in results["stability"]["window_metrics"]:
                stability_metrics = results["stability"]["window_metrics"][window_key]
                window_data["stability"] = {
                    "mean_stability_index": stability_metrics["mean_stability_index"],
                    "std_stability_index": stability_metrics["std_stability_index"],
                    "mean_jt_volatility": stability_metrics["mean_jt_volatility"],
                    "mean_mastery_variance": stability_metrics["mean_mastery_variance"],
                    "mean_autocorrelation": stability_metrics["mean_autocorrelation"],
                    "num_learners": stability_metrics["num_learners"]
                }
            
            window_results[f"window_{window}"] = window_data
        
        return window_results
    
    def compare_experiments(
        self,
        experiment_id_1: str,
        experiment_id_2: str,
        metric: str = "learning_gain",
        evaluation_window: int = 20,
        statistical_method: str = "frequentist",
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Compare two experiments with statistical testing
        
        API: POST /experiments/compare
        
        Args:
            experiment_id_1: First experiment identifier
            experiment_id_2: Second experiment identifier
            metric: Metric to compare
            evaluation_window: Interaction window to evaluate
            statistical_method: Statistical method
            confidence_level: Confidence level for intervals
            
        Returns:
            Comparison results with significance testing
        """
        try:
            # Compare experiments using existing EvaluationEngine
            comparison = self.evaluation_engine.compare_experiment_runs(
                experiment_run_id_1=experiment_id_1,
                experiment_run_id_2=experiment_id_2,
                metric=metric,
                evaluation_window=evaluation_window,
                statistical_method=statistical_method,
                confidence_level=confidence_level
            )
            
            # Format response
            formatted_response = {
                "experiment_id_1": experiment_id_1,
                "experiment_id_2": experiment_id_2,
                "metric": metric,
                "evaluation_window": evaluation_window,
                "statistical_method": statistical_method,
                "confidence_level": confidence_level,
                "comparison": comparison
            }
            
            logger.info(f"Comparison completed for experiments {experiment_id_1} and {experiment_id_2}")
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Failed to compare experiments: {e}")
            raise


def main():
    """Main entry point for evaluation engine service"""
    import os
    from fastapi import FastAPI
    from pydantic import BaseModel
    
    # Create FastAPI app
    app = FastAPI(title="Evaluation Engine Service")
    
    # Initialize service
    service = EvaluationEngineService()
    
    # Pydantic models for API
    class EvaluationRequest(BaseModel):
        experiment_id: str
        evaluation_windows: List[int] = [5, 10, 20]
        metrics: List[str] = ["learning_gain", "regret", "accuracy"]
        statistical_method: str = "frequentist"
        confidence_level: float = 0.95
    
    class ComparisonRequest(BaseModel):
        experiment_id_1: str
        experiment_id_2: str
        metric: str = "learning_gain"
        evaluation_window: int = 20
        statistical_method: str = "frequentist"
        confidence_level: float = 0.95
    
    # API endpoints
    @app.post("/evaluate")
    async def evaluate(request: EvaluationRequest):
        """Evaluate experiment with specified metrics and windows"""
        return service.evaluate_experiment(
            experiment_id=request.experiment_id,
            evaluation_windows=request.evaluation_windows,
            metrics=request.metrics,
            statistical_method=request.statistical_method,
            confidence_level=request.confidence_level
        )
    
    @app.post("/compare")
    async def compare(request: ComparisonRequest):
        """Compare two experiments with statistical testing"""
        return service.compare_experiments(
            experiment_id_1=request.experiment_id_1,
            experiment_id_2=request.experiment_id_2,
            metric=request.metric,
            evaluation_window=request.evaluation_window,
            statistical_method=request.statistical_method,
            confidence_level=request.confidence_level
        )
    
    # Run service
    import uvicorn
    port = int(os.getenv("EVALUATION_ENGINE_PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
