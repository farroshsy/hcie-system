"""
Policy Comparator

Compares two policies using comprehensive divergence metrics.
Provides statistical analysis and reporting for policy comparison.
"""

import logging
from typing import Dict, Any, Optional
from scipy.stats import ttest_ind, mannwhitneyu
import numpy as np

from infrastructure.experiment.behavioral_divergence import (
    compute_comprehensive_divergence,
    format_divergence_report
)

logger = logging.getLogger(__name__)


class PolicyComparator:
    """
    Compares two policies using comprehensive divergence metrics.
    
    RESPONSIBILITIES:
    - Compute divergence between policies
    - Test statistical significance
    - Generate divergence reports
    """
    
    def __init__(self, divergence_metrics=None):
        """
        Initialize policy comparator.
        
        Args:
            divergence_metrics: Optional custom divergence metrics module
        """
        self.divergence_metrics = divergence_metrics
    
    def compare_policies(
        self,
        policy_a_results: Dict[str, Any],
        policy_b_results: Dict[str, Any],
        policy_a_name: str = "Policy A",
        policy_b_name: str = "Policy B"
    ) -> Dict[str, Any]:
        """
        Compare two policies using comprehensive divergence metrics.
        
        Args:
            policy_a_results: Dict with trajectories, distributions, regret, JT
            policy_b_results: Dict with trajectories, distributions, regret, JT
            policy_a_name: Name of policy A
            policy_b_name: Name of policy B
            
        Returns:
            Dict with divergence metrics and statistical analysis
        """
        try:
            # Extract data from results
            trajectory_a = policy_a_results.get('trajectory', [])
            trajectory_b = policy_b_results.get('trajectory', [])
            distribution_a = policy_a_results.get('distribution', {})
            distribution_b = policy_b_results.get('distribution', {})
            regret_a = policy_a_results.get('regret', [])
            regret_b = policy_b_results.get('regret', [])
            jt_trajectory_a = policy_a_results.get('jt_trajectory', [])
            jt_trajectory_b = policy_b_results.get('jt_trajectory', [])
            
            # Compute comprehensive divergence
            divergence = compute_comprehensive_divergence(
                trajectory_a=trajectory_a,
                trajectory_b=trajectory_b,
                distribution_a=distribution_a,
                distribution_b=distribution_b,
                regret_a=regret_a,
                regret_b=regret_b,
                jt_trajectory_a=jt_trajectory_a,
                jt_trajectory_b=jt_trajectory_b
            )
            
            # Test statistical significance
            significance = self._test_significance(
                policy_a_results, policy_b_results, divergence
            )
            
            # Format report
            report = format_divergence_report(divergence)
            
            return {
                'policy_a': policy_a_name,
                'policy_b': policy_b_name,
                'divergence': divergence,
                'statistical_significance': significance,
                'report': report
            }
            
        except Exception as e:
            logger.error(f"Failed to compare policies: {e}")
            raise
    
    def _test_significance(
        self,
        policy_a_results: Dict[str, Any],
        policy_b_results: Dict[str, Any],
        divergence: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Test statistical significance of divergence.
        
        Args:
            policy_a_results: Results from policy A
            policy_b_results: Results from policy B
            divergence: Divergence metrics
            
        Returns:
            Statistical significance results
        """
        try:
            significance = {}
            
            # Test regret difference significance
            regret_a = policy_a_results.get('regret', [])
            regret_b = policy_b_results.get('regret', [])
            
            if regret_a and regret_b:
                # t-test for regret
                t_stat, t_pvalue = ttest_ind(regret_a, regret_b)
                # Mann-Whitney U test (non-parametric)
                u_stat, u_pvalue = mannwhitneyu(regret_a, regret_b)
                
                significance['regret_t_test'] = {
                    'statistic': t_stat,
                    'p_value': t_pvalue,
                    'significant': t_pvalue < 0.05
                }
                significance['regret_mann_whitney'] = {
                    'statistic': u_stat,
                    'p_value': u_pvalue,
                    'significant': u_pvalue < 0.05
                }
            
            # Test learning outcomes significance
            outcomes_a = policy_a_results.get('learning_outcomes', {})
            outcomes_b = policy_b_results.get('learning_outcomes', {})
            
            final_mastery_a = outcomes_a.get('final_mastery', 0)
            final_mastery_b = outcomes_b.get('final_mastery', 0)
            
            # Simple difference test for final mastery
            mastery_diff = abs(final_mastery_a - final_mastery_b)
            significance['mastery_difference'] = {
                'difference': mastery_diff,
                'policy_a_mastery': final_mastery_a,
                'policy_b_mastery': final_mastery_b,
                'significant': mastery_diff > 0.1  # Threshold for significance
            }
            
            return significance
            
        except Exception as e:
            logger.error(f"Failed to test significance: {e}")
            return {'error': str(e)}
