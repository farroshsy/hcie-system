"""
Divergence Analyzer

Analyzes divergence across all policies in an experiment.
Generates divergence matrix and pairwise comparisons.
"""

import logging
from typing import Dict, Any, List, Optional
from itertools import combinations

from infrastructure.experiment.policy_comparator import PolicyComparator

logger = logging.getLogger(__name__)


class DivergenceAnalyzer:
    """
    Analyzes divergence across all policies in an experiment.
    
    RESPONSIBILITIES:
    - Generate divergence matrix for all policy pairs
    - Compute summary statistics
    - Generate recommendations
    """
    
    def __init__(self, policy_comparator: Optional[PolicyComparator] = None):
        """
        Initialize divergence analyzer.
        
        Args:
            policy_comparator: Optional PolicyComparator instance
        """
        self.comparator = policy_comparator or PolicyComparator()
    
    def analyze_experiment_divergence(
        self,
        experiment_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze divergence across all policies in an experiment.
        
        Args:
            experiment_results: Dict mapping policy_id to results
            
        Returns:
            Divergence matrix and pairwise comparisons
        """
        try:
            policies = list(experiment_results.keys())
            
            if len(policies) < 2:
                logger.warning("Need at least 2 policies for divergence analysis")
                return {
                    'divergence_matrix': {},
                    'summary': 'Need at least 2 policies for divergence analysis'
                }
            
            divergence_matrix = {}
            
            # Compute pairwise divergence
            for policy_a, policy_b in combinations(policies, 2):
                comparison = self.comparator.compare_policies(
                    policy_a_results=experiment_results[policy_a],
                    policy_b_results=experiment_results[policy_b],
                    policy_a_name=policy_a,
                    policy_b_name=policy_b
                )
                
                divergence_matrix[(policy_a, policy_b)] = comparison
            
            # Generate summary
            summary = self._generate_summary(divergence_matrix, policies)
            
            return {
                'divergence_matrix': divergence_matrix,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze experiment divergence: {e}")
            raise
    
    def _generate_summary(
        self,
        divergence_matrix: Dict[tuple, Dict[str, Any]],
        policies: List[str]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics from divergence matrix.
        
        Args:
            divergence_matrix: Matrix of pairwise divergences
            policies: List of policy names
            
        Returns:
            Summary statistics
        """
        try:
            # Extract weighted divergences
            divergences = []
            for pair, comparison in divergence_matrix.items():
                divergence = comparison['divergence'].get('weighted_divergence', 0)
                divergences.append({
                    'pair': pair,
                    'divergence': divergence
                })
            
            # Compute statistics
            if divergences:
                divergence_values = [d['divergence'] for d in divergences]
                avg_divergence = sum(divergence_values) / len(divergence_values)
                max_divergence = max(divergence_values)
                min_divergence = min(divergence_values)
                
                # Find most and least divergent pairs
                most_divergent = max(divergences, key=lambda x: x['divergence'])
                least_divergent = min(divergences, key=lambda x: x['divergence'])
            else:
                avg_divergence = 0
                max_divergence = 0
                min_divergence = 0
                most_divergent = None
                least_divergent = None
            
            summary = {
                'num_policies': len(policies),
                'num_comparisons': len(divergences),
                'average_divergence': avg_divergence,
                'max_divergence': max_divergence,
                'min_divergence': min_divergence,
                'most_divergent_pair': most_divergent,
                'least_divergent_pair': least_divergent
            }
            
            # Generate recommendations
            summary['recommendations'] = self._generate_recommendations(summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on divergence analysis.
        
        Args:
            summary: Summary statistics
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        avg_divergence = summary.get('average_divergence', 0)
        max_divergence = summary.get('max_divergence', 0)
        
        if avg_divergence < 0.1:
            recommendations.append(
                "Policies show very low behavioral divergence. "
                "Consider more diverse policy configurations."
            )
        elif avg_divergence > 0.5:
            recommendations.append(
                "Policies show high behavioral divergence. "
                "This is good for policy comparison experiments."
            )
        else:
            recommendations.append(
                "Policies show moderate behavioral divergence. "
                "Good for policy comparison experiments."
            )
        
        if summary.get('most_divergent_pair'):
            pair = summary['most_divergent_pair']['pair']
            recommendations.append(
                f"Most divergent pair: {pair[0]} vs {pair[1]} "
                f"(divergence={summary['most_divergent_pair']['divergence']:.3f})"
            )
        
        return recommendations
