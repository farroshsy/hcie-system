"""
Evaluation Engine Service for Phase 1 Experiment Infrastructure

Evaluates experiment results and computes metrics for contribution validation.
Supports Contribution A (System Design), B (Decision-Making), C (Empirical Validation).

Key Features:
- Evaluation windows: 5, 10, 20 interactions (configurable)
- Metric computation per window
- Confidence intervals (95%)
- Effect sizes (Cohen's d, Cliff's delta)
- Significance testing (t-test, Wilcoxon, Bayesian)
- Stability metrics (variance, autocorrelation)
- Aggregation across learners (mean, median, variance)
"""

from typing import Dict, Any, List
from datetime import datetime
import numpy as np
import logging
from scipy import stats
from scipy.stats import mannwhitneyu, ttest_ind, norm

logger = logging.getLogger(__name__)


class EvaluationEngine:
    """
    Evaluates experiment results and computes metrics
    
    RESPONSIBILITIES:
    - Compute learning gain metrics
    - Calculate regret curves
    - Aggregate statistical results
    - Support contribution-specific metrics
    """
    
    def __init__(self, db_client):
        """
        Initialize evaluation engine
        
        Args:
            db_client: Database client for result storage
        """
        self.db_client = db_client
        # Default evaluation windows
        self.default_windows = [5, 10, 20]
        # Default confidence level
        self.default_confidence = 0.95
    
    def evaluate_learning_gain(
        self,
        experiment_run_id: str,
        evaluation_windows: List[int] = None,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Evaluate learning gain over evaluation windows
        
        Contribution C (Empirical Validation) metric
        
        Args:
            experiment_run_id: Experiment run identifier
            evaluation_windows: List of interaction windows to evaluate (default: [5, 10, 20])
            confidence_level: Confidence level for intervals (default: 0.95)
            
        Returns:
            Learning gain metrics per window with confidence intervals
        """
        if evaluation_windows is None:
            evaluation_windows = self.default_windows
        
        try:
            # Retrieve trajectories for this run
            trajectories = self.db_client.execute_read(
                "SELECT * FROM experiment_trajectories WHERE experiment_run_id = %s ORDER BY interaction_number ASC",
                (experiment_run_id,)
            )
            
            # Group by user
            user_trajectories = {}
            for traj in trajectories:
                user_id = traj["user_id"]
                if user_id not in user_trajectories:
                    user_trajectories[user_id] = []
                user_trajectories[user_id].append(traj)
            
            # Sort each user's trajectory by interaction_number
            for user_id in user_trajectories:
                user_trajectories[user_id].sort(key=lambda x: x["interaction_number"])
            
            # Compute learning gain per window
            window_metrics = {}
            
            for window in evaluation_windows:
                learning_gains = []
                time_to_threshold = []
                
                for user_id, user_traj in user_trajectories.items():
                    if len(user_traj) < 2:
                        continue
                    
                    # Limit to window size
                    window_traj = user_traj[:window]
                    
                    # Initial and final mastery in window
                    initial_mastery = window_traj[0]["mastery_before"]
                    final_mastery = window_traj[-1]["mastery_after"]
                    
                    learning_gain = final_mastery - initial_mastery
                    learning_gains.append(learning_gain)
                
                if learning_gains:
                    # Compute statistics
                    mean_gain = np.mean(learning_gains)
                    std_gain = np.std(learning_gains)
                    median_gain = np.median(learning_gains)
                    
                    # Compute confidence interval
                    n = len(learning_gains)
                    if n > 1:
                        se = std_gain / np.sqrt(n)
                        z_score = norm.ppf((1 + confidence_level) / 2)
                        ci_lower = mean_gain - z_score * se
                        ci_upper = mean_gain + z_score * se
                    else:
                        ci_lower = mean_gain
                        ci_upper = mean_gain
                    
                    window_metrics[f"window_{window}"] = {
                        "mean_learning_gain": mean_gain,
                        "std_learning_gain": std_gain,
                        "median_learning_gain": median_gain,
                        "confidence_interval": {
                            "lower": ci_lower,
                            "upper": ci_upper,
                            "level": confidence_level
                        },
                        "num_learners": len(learning_gains)
                    }
            
            metrics = {
                "window_metrics": window_metrics,
                "num_learners_total": len(user_trajectories),
                "evaluation_windows": evaluation_windows,
                "confidence_level": confidence_level
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to evaluate learning gain: {e}")
            raise
    
    def evaluate_regret(
        self,
        experiment_run_id: str,
        evaluation_windows: List[int] = None,
        oracle_policy: str = "hcie"
    ) -> Dict[str, Any]:
        """
        Evaluate regret curves over evaluation windows
        
        Contribution B (Decision-Making) metric
        
        Args:
            experiment_run_id: Experiment run identifier
            evaluation_windows: List of interaction windows to evaluate (default: [5, 10, 20])
            oracle_policy: Policy used as oracle reference
            
        Returns:
            Regret metrics per window
        """
        if evaluation_windows is None:
            evaluation_windows = self.default_windows
        
        try:
            # Retrieve trajectories
            trajectories = self.db_client.execute_read(
                "SELECT * FROM experiment_trajectories WHERE experiment_run_id = %s ORDER BY interaction_number ASC",
                (experiment_run_id,)
            )
            
            # Group by user
            user_trajectories = {}
            for traj in trajectories:
                user_id = traj["user_id"]
                if user_id not in user_trajectories:
                    user_trajectories[user_id] = []
                user_trajectories[user_id].append(traj)
            
            # Sort each user's trajectory
            for user_id in user_trajectories:
                user_trajectories[user_id].sort(key=lambda x: x["interaction_number"])
            
            # Compute regret per window
            window_metrics = {}
            
            for window in evaluation_windows:
                cumulative_regrets = []
                
                for user_id, user_traj in user_trajectories.items():
                    # Limit to window size
                    window_traj = user_traj[:window]
                    
                    cumulative_regret = 0.0
                    user_regret_curve = []
                    
                    for traj in window_traj:
                        # Simplified regret: 1 - JT (higher JT = lower regret)
                        actual_jt = traj.get("jt_value", 0.5)
                        regret = 1.0 - actual_jt
                        cumulative_regret += regret
                        user_regret_curve.append(cumulative_regret)
                    
                    if user_regret_curve:
                        cumulative_regrets.append(user_regret_curve[-1])
                
                if cumulative_regrets:
                    window_metrics[f"window_{window}"] = {
                        "mean_cumulative_regret": np.mean(cumulative_regrets),
                        "std_cumulative_regret": np.std(cumulative_regrets),
                        "median_cumulative_regret": np.median(cumulative_regrets),
                        "num_learners": len(cumulative_regrets)
                    }
            
            metrics = {
                "window_metrics": window_metrics,
                "num_learners_total": len(user_trajectories),
                "evaluation_windows": evaluation_windows,
                "oracle_policy": oracle_policy
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to evaluate regret: {e}")
            raise
    
    def evaluate_stability(
        self,
        experiment_run_id: str,
        evaluation_windows: List[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluate system stability with variance and autocorrelation
        
        Contribution A (System Design) metric
        
        Args:
            experiment_run_id: Experiment run identifier
            evaluation_windows: List of interaction windows to evaluate (default: [5, 10, 20])
            
        Returns:
            Stability metrics per window with variance and autocorrelation
        """
        if evaluation_windows is None:
            evaluation_windows = self.default_windows
        
        try:
            # Retrieve trajectories
            trajectories = self.db_client.execute_read(
                "SELECT * FROM experiment_trajectories WHERE experiment_run_id = %s ORDER BY interaction_number ASC",
                (experiment_run_id,)
            )
            
            # Group by user
            user_trajectories = {}
            for traj in trajectories:
                user_id = traj["user_id"]
                if user_id not in user_trajectories:
                    user_trajectories[user_id] = []
                user_trajectories[user_id].append(traj)
            
            # Sort each user's trajectory
            for user_id in user_trajectories:
                user_trajectories[user_id].sort(key=lambda x: x["interaction_number"])
            
            # Compute stability per window
            window_metrics = {}
            
            for window in evaluation_windows:
                stability_indices = []
                jt_volatilities = []
                mastery_variances = []
                autocorrelations = []
                
                for user_id, user_traj in user_trajectories.items():
                    # Limit to window size
                    window_traj = user_traj[:window]
                    
                    if len(window_traj) < 2:
                        continue
                    
                    # Extract stability indices
                    user_stability = [traj.get("stability_index", 1.0) for traj in window_traj]
                    stability_indices.extend(user_stability)
                    
                    # Extract JT volatilities
                    user_jt_vol = [traj.get("jt_volatility", 0.0) for traj in window_traj]
                    jt_volatilities.extend(user_jt_vol)
                    
                    # Extract mastery values for variance
                    user_mastery = [traj.get("mastery_after", 0.5) for traj in window_traj]
                    mastery_variances.append(np.var(user_mastery))
                    
                    # Compute autocorrelation of mastery
                    if len(user_mastery) > 1:
                        autocorr = np.corrcoef(user_mastery[:-1], user_mastery[1:])[0, 1]
                        if not np.isnan(autocorr):
                            autocorrelations.append(autocorr)
                
                if stability_indices:
                    window_metrics[f"window_{window}"] = {
                        "mean_stability_index": np.mean(stability_indices),
                        "std_stability_index": np.std(stability_indices),
                        "min_stability_index": np.min(stability_indices),
                        "mean_jt_volatility": np.mean(jt_volatilities),
                        "std_jt_volatility": np.std(jt_volatilities),
                        "mean_mastery_variance": np.mean(mastery_variances) if mastery_variances else 0.0,
                        "mean_autocorrelation": np.mean(autocorrelations) if autocorrelations else 0.0,
                        "num_interactions": len(stability_indices),
                        "num_learners": len([t for t in user_trajectories.values() if len(t) >= 2])
                    }
            
            metrics = {
                "window_metrics": window_metrics,
                "num_learners_total": len(user_trajectories),
                "evaluation_windows": evaluation_windows
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to evaluate stability: {e}")
            raise
    
    def compute_cohens_d(
        self,
        group1: List[float],
        group2: List[float]
    ) -> float:
        """
        Compute Cohen's d effect size
        
        Args:
            group1: First group of values
            group2: Second group of values
            
        Returns:
            Cohen's d effect size
        """
        if len(group1) < 2 or len(group2) < 2:
            return 0.0
        
        mean1, mean2 = np.mean(group1), np.mean(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        n1, n2 = len(group1), len(group2)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            return 0.0
        
        cohens_d = (mean1 - mean2) / pooled_std
        return cohens_d
    
    def compute_cliffs_delta(
        self,
        group1: List[float],
        group2: List[float]
    ) -> float:
        """
        Compute Cliff's delta effect size (non-parametric)
        
        Args:
            group1: First group of values
            group2: Second group of values
            
        Returns:
            Cliff's delta effect size
        """
        if len(group1) == 0 or len(group2) == 0:
            return 0.0
        
        # Count number of times value from group1 > value from group2
        greater_count = 0
        for val1 in group1:
            for val2 in group2:
                if val1 > val2:
                    greater_count += 1
                elif val1 == val2:
                    greater_count += 0.5
        
        n1, n2 = len(group1), len(group2)
        cliffs_delta = greater_count / (n1 * n2)
        
        # Normalize to [-1, 1]
        cliffs_delta = 2 * cliffs_delta - 1
        return cliffs_delta
    
    def perform_significance_test(
        self,
        group1: List[float],
        group2: List[float],
        method: str = "frequentist"
    ) -> Dict[str, Any]:
        """
        Perform significance test between two groups
        
        Args:
            group1: First group of values
            group2: Second group of values
            method: Statistical method ("frequentist" or "bayesian")
            
        Returns:
            Test results with p-value and effect size
        """
        if len(group1) < 2 or len(group2) < 2:
            return {
                "p_value": 1.0,
                "significant": False,
                "method": method,
                "cohens_d": 0.0,
                "cliffs_delta": 0.0
            }
        
        try:
            if method == "frequentist":
                # Perform t-test
                t_stat, p_value = ttest_ind(group1, group2)
                
                # Also perform Wilcoxon rank-sum test (non-parametric)
                try:
                    u_stat, wilcoxon_p = mannwhitneyu(group1, group2, alternative='two-sided')
                except:
                    wilcoxon_p = 1.0
                
                # Compute effect sizes
                cohens_d = self.compute_cohens_d(group1, group2)
                cliffs_delta = self.compute_cliffs_delta(group1, group2)
                
                return {
                    "p_value": float(p_value),
                    "significant": p_value < 0.05,
                    "method": "frequentist",
                    "t_statistic": float(t_stat),
                    "wilcoxon_p_value": float(wilcoxon_p),
                    "cohens_d": cohens_d,
                    "cliffs_delta": cliffs_delta
                }
            
            elif method == "bayesian":
                # Simplified Bayesian approach using effect size as prior
                cohens_d = self.compute_cohens_d(group1, group2)
                
                # Approximate Bayesian p-value using effect size
                # This is a simplification - full Bayesian analysis would require more computation
                n = len(group1) + len(group2)
                t_stat = cohens_d * np.sqrt(n / 4)  # Approximate t-statistic from effect size
                p_value = 2 * (1 - norm.cdf(abs(t_stat)))
                
                return {
                    "p_value": float(p_value),
                    "significant": p_value < 0.05,
                    "method": "bayesian",
                    "cohens_d": cohens_d,
                    "cliffs_delta": self.compute_cliffs_delta(group1, group2),
                    "note": "Simplified Bayesian approximation"
                }
            
            else:
                raise ValueError(f"Unknown statistical method: {method}")
                
        except Exception as e:
            logger.error(f"Failed to perform significance test: {e}")
            return {
                "p_value": 1.0,
                "significant": False,
                "method": method,
                "error": str(e)
            }
    
    def compare_experiment_runs(
        self,
        experiment_run_id_1: str,
        experiment_run_id_2: str,
        metric: str = "learning_gain",
        evaluation_window: int = 20,
        statistical_method: str = "frequentist",
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Compare two experiment runs with statistical testing
        
        Args:
            experiment_run_id_1: First experiment run identifier
            experiment_run_id_2: Second experiment run identifier
            metric: Metric to compare (learning_gain, regret, stability)
            evaluation_window: Interaction window to evaluate
            statistical_method: Statistical method ("frequentist" or "bayesian")
            confidence_level: Confidence level for intervals
            
        Returns:
            Comparison results with significance testing
        """
        try:
            # Get metrics for both runs
            if metric == "learning_gain":
                metrics1 = self.evaluate_learning_gain(experiment_run_id_1, [evaluation_window], confidence_level)
                metrics2 = self.evaluate_learning_gain(experiment_run_id_2, [evaluation_window], confidence_level)
                
                # Extract learning gains for comparison
                trajectories1 = self.db_client.execute_read(
                    "SELECT * FROM experiment_trajectories WHERE experiment_run_id = %s ORDER BY interaction_number ASC",
                    (experiment_run_id_1,)
                )
                trajectories2 = self.db_client.execute_read(
                    "SELECT * FROM experiment_trajectories WHERE experiment_run_id = %s ORDER BY interaction_number ASC",
                    (experiment_run_id_2,)
                )
                
                # Extract learning gains per user
                gains1 = self._extract_metric_per_user(trajectories1, evaluation_window, "learning_gain")
                gains2 = self._extract_metric_per_user(trajectories2, evaluation_window, "learning_gain")
                
                # Perform significance test
                test_results = self.perform_significance_test(gains1, gains2, statistical_method)
                
                comparison = {
                    "metric": metric,
                    "evaluation_window": evaluation_window,
                    "run_1": {
                        "id": experiment_run_id_1,
                        "metrics": metrics1["window_metrics"][f"window_{evaluation_window}"]
                    },
                    "run_2": {
                        "id": experiment_run_id_2,
                        "metrics": metrics2["window_metrics"][f"window_{evaluation_window}"]
                    },
                    "statistical_test": test_results,
                    "confidence_level": confidence_level
                }
            
            elif metric == "regret":
                metrics1 = self.evaluate_regret(experiment_run_id_1, [evaluation_window])
                metrics2 = self.evaluate_regret(experiment_run_id_2, [evaluation_window])
                
                # Extract regrets for comparison
                trajectories1 = self.db_client.execute_read(
                    "SELECT * FROM experiment_trajectories WHERE experiment_run_id = %s ORDER BY interaction_number ASC",
                    (experiment_run_id_1,)
                )
                trajectories2 = self.db_client.execute_read(
                    "SELECT * FROM experiment_trajectories WHERE experiment_run_id = %s ORDER BY interaction_number ASC",
                    (experiment_run_id_2,)
                )
                
                regrets1 = self._extract_metric_per_user(trajectories1, evaluation_window, "regret")
                regrets2 = self._extract_metric_per_user(trajectories2, evaluation_window, "regret")
                
                # Perform significance test
                test_results = self.perform_significance_test(regrets1, regrets2, statistical_method)
                
                comparison = {
                    "metric": metric,
                    "evaluation_window": evaluation_window,
                    "run_1": {
                        "id": experiment_run_id_1,
                        "metrics": metrics1["window_metrics"][f"window_{evaluation_window}"]
                    },
                    "run_2": {
                        "id": experiment_run_id_2,
                        "metrics": metrics2["window_metrics"][f"window_{evaluation_window}"]
                    },
                    "statistical_test": test_results,
                    "confidence_level": confidence_level
                }
            
            else:
                raise ValueError(f"Unknown metric: {metric}")
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare experiment runs: {e}")
            raise
    
    def _extract_metric_per_user(
        self,
        trajectories: List[Dict[str, Any]],
        window: int,
        metric: str
    ) -> List[float]:
        """
        Extract metric values per user for statistical comparison
        
        Args:
            trajectories: List of trajectory records
            window: Evaluation window
            metric: Metric to extract (learning_gain, regret)
            
        Returns:
            List of metric values per user
        """
        # Group by user
        user_trajectories = {}
        for traj in trajectories:
            user_id = traj["user_id"]
            if user_id not in user_trajectories:
                user_trajectories[user_id] = []
            user_trajectories[user_id].append(traj)
        
        # Sort each user's trajectory
        for user_id in user_trajectories:
            user_trajectories[user_id].sort(key=lambda x: x["interaction_number"])
        
        # Extract metric per user
        metric_values = []
        
        for user_id, user_traj in user_trajectories.items():
            if len(user_traj) < 2:
                continue
            
            # Limit to window size
            window_traj = user_traj[:window]
            
            if metric == "learning_gain":
                initial_mastery = window_traj[0]["mastery_before"]
                final_mastery = window_traj[-1]["mastery_after"]
                metric_values.append(final_mastery - initial_mastery)
            
            elif metric == "regret":
                cumulative_regret = 0.0
                for traj in window_traj:
                    actual_jt = traj.get("jt_value", 0.5)
                    regret = 1.0 - actual_jt
                    cumulative_regret += regret
                metric_values.append(cumulative_regret)
        
        return metric_values
    
    def evaluate_experiment_run(
        self,
        experiment_run_id: str,
        evaluation_windows: List[int] = None,
        metrics: List[str] = None,
        statistical_method: str = "frequentist",
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Complete evaluation of an experiment run
        
        Args:
            experiment_run_id: Experiment run identifier
            evaluation_windows: List of interaction windows to evaluate (default: [5, 10, 20])
            metrics: List of metrics to compute (default: all)
            statistical_method: Statistical method ("frequentist" or "bayesian")
            confidence_level: Confidence level for intervals
            
        Returns:
            Complete evaluation metrics
        """
        if evaluation_windows is None:
            evaluation_windows = self.default_windows
        
        if metrics is None:
            metrics = ["learning_gain", "regret", "stability"]
        
        try:
            complete_metrics = {
                "experiment_run_id": experiment_run_id,
                "evaluation_windows": evaluation_windows,
                "metrics": metrics,
                "statistical_method": statistical_method,
                "confidence_level": confidence_level,
                "evaluated_at": datetime.now().isoformat()
            }
            
            # Compute requested metrics
            if "learning_gain" in metrics:
                complete_metrics["learning_gain"] = self.evaluate_learning_gain(
                    experiment_run_id, evaluation_windows, confidence_level
                )
            
            if "regret" in metrics:
                complete_metrics["regret"] = self.evaluate_regret(
                    experiment_run_id, evaluation_windows
                )
            
            if "stability" in metrics:
                complete_metrics["stability"] = self.evaluate_stability(
                    experiment_run_id, evaluation_windows
                )
            
            logger.info(f"Evaluation complete for experiment run {experiment_run_id}")
            
            return complete_metrics
            
        except Exception as e:
            logger.error(f"Failed to evaluate experiment run: {e}")
            raise
