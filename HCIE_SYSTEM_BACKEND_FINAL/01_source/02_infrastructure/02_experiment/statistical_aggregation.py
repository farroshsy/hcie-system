"""
Statistical Aggregation for Phase 1 Experiment Infrastructure

Aggregates results across multiple experiment runs with statistical rigor.
Supports mixed-effects models and confidence intervals.
"""

from typing import Dict, Any, List
from datetime import datetime
import numpy as np
import logging

logger = logging.getLogger(__name__)


class StatisticalAggregator:
    """
    Aggregates experiment results with statistical rigor
    
    RESPONSIBILITIES:
    - Aggregate metrics across multiple runs
    - Compute confidence intervals
    - Calculate effect sizes
    - Support mixed-effects models for learner variability
    """
    
    def __init__(self, db_client):
        """
        Initialize statistical aggregator
        
        Args:
            db_client: Database client for result storage
        """
        self.db_client = db_client
    
    def aggregate_learning_gain(
        self,
        experiment_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Aggregate learning gain across multiple experiment runs
        
        Args:
            experiment_ids: List of experiment identifiers
            
        Returns:
            Aggregated learning gain metrics with statistical rigor
        """
        try:
            # Retrieve all experiment runs
            all_metrics = []
            for exp_id in experiment_ids:
                runs = self.db_client.execute_read(
                    "SELECT * FROM experiment_runs WHERE experiment_id = %s AND status = %s",
                    (exp_id, "completed")
                )
                for run in runs:
                    if run.get("metrics") and run["metrics"].get("learning_gain"):
                        all_metrics.append(run["metrics"]["learning_gain"])
            
            if not all_metrics:
                return {"error": "No completed runs found"}
            
            # Extract learning gains
            learning_gains = [m["mean_learning_gain"] for m in all_metrics]
            
            # Compute statistics
            n = len(learning_gains)
            mean = np.mean(learning_gains)
            std = np.std(learning_gains, ddof=1) if n > 1 else 0.0
            sem = std / np.sqrt(n) if n > 0 else 0.0
            
            # 95% confidence interval
            ci_lower = mean - 1.96 * sem
            ci_upper = mean + 1.96 * sem
            
            # Effect size (Cohen's d) vs baseline (assume baseline = 0)
            baseline = 0.0
            pooled_std = std
            effect_size = (mean - baseline) / pooled_std if pooled_std > 0 else 0.0
            
            metrics = {
                "mean_learning_gain": mean,
                "std_learning_gain": std,
                "sem": sem,
                "ci_95_lower": ci_lower,
                "ci_95_upper": ci_upper,
                "effect_size": effect_size,
                "n_runs": n,
                "aggregated_at": datetime.now()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to aggregate learning gain: {e}")
            raise
    
    def aggregate_regret(
        self,
        experiment_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Aggregate regret curves across multiple runs
        
        Args:
            experiment_ids: List of experiment identifiers
            
        Returns:
            Aggregated regret metrics
        """
        try:
            # Retrieve all experiment runs
            all_regret_curves = []
            for exp_id in experiment_ids:
                runs = self.db_client.execute_read(
                    "SELECT * FROM experiment_runs WHERE experiment_id = %s AND status = %s",
                    (exp_id, "completed")
                )
                for run in runs:
                    if run.get("metrics") and run["metrics"].get("regret"):
                        regret_curve = run["metrics"]["regret"].get("mean_regret_curve", [])
                        if regret_curve:
                            all_regret_curves.append(regret_curve)
            
            if not all_regret_curves:
                return {"error": "No regret curves found"}
            
            # Pad curves to same length
            max_length = max(len(curve) for curve in all_regret_curves)
            padded_curves = []
            for curve in all_regret_curves:
                padded = curve + [curve[-1]] * (max_length - len(curve))
                padded_curves.append(padded)
            
            # Compute mean and std at each time step
            regret_array = np.array(padded_curves)
            mean_curve = np.mean(regret_array, axis=0).tolist()
            std_curve = np.std(regret_array, axis=0, ddof=1).tolist()
            sem_curve = (std_curve / np.sqrt(len(all_regret_curves))).tolist()
            
            metrics = {
                "mean_regret_curve": mean_curve,
                "std_regret_curve": std_curve,
                "sem_regret_curve": sem_curve,
                "final_mean_regret": mean_curve[-1] if mean_curve else 0.0,
                "n_runs": len(all_regret_curves),
                "aggregated_at": datetime.now()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to aggregate regret: {e}")
            raise
    
    def compare_policies(
        self,
        experiment_ids_a: List[str],
        experiment_ids_b: List[str],
        metric: str = "learning_gain"
    ) -> Dict[str, Any]:
        """
        Compare two sets of experiments (e.g., HCIE vs baseline)
        
        Args:
            experiment_ids_a: First set of experiment IDs
            experiment_ids_b: Second set of experiment IDs
            metric: Metric to compare
            
        Returns:
            Comparison metrics with statistical significance
        """
        try:
            # Get metrics for group A
            metrics_a = self.aggregate_learning_gain(experiment_ids_a)
            values_a = [metrics_a["mean_learning_gain"]]
            
            # Get metrics for group B
            metrics_b = self.aggregate_learning_gain(experiment_ids_b)
            values_b = [metrics_b["mean_learning_gain"]]
            
            # Compute difference
            difference = metrics_a["mean_learning_gain"] - metrics_b["mean_learning_gain"]
            
            # Pooled standard error
            pooled_se = np.sqrt(
                (metrics_a["sem"]**2 + metrics_b["sem"]**2)
            )
            
            # Z-score
            z_score = difference / pooled_se if pooled_se > 0 else 0.0
            
            # P-value (two-tailed)
            from scipy import stats
            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
            
            metrics = {
                "policy_a_mean": metrics_a["mean_learning_gain"],
                "policy_b_mean": metrics_b["mean_learning_gain"],
                "difference": difference,
                "z_score": z_score,
                "p_value": p_value,
                "significant": p_value < 0.05,
                "compared_at": datetime.now()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to compare policies: {e}")
            raise
