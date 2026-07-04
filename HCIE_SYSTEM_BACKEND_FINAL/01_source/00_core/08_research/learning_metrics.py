"""
🔥 Learning Metrics Layer
Research-grade measurement system for UnifiedLearningBrain

This provides the foundation for objective function definition
by measuring what the system can actually observe reliably.
"""

import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class InteractionMetrics:
    """Metrics for a single learning interaction"""
    
    # Core learning metrics
    user_id: str
    concept: str
    timestamp: datetime
    
    # Before/after states
    mastery_before: float
    mastery_after: float
    learning_gain: float  # ΔM
    
    # Transfer metrics
    transfer_amount: float
    transfer_contribution: float  # ΔM_transfer (when we can measure)
    
    # Policy metrics
    selected_action: str
    bandit_reward: float
    policy_multiplier: float
    
    # Performance metrics
    response_time: float
    difficulty: float
    zpd_gap: float
    
    # Learner insights
    lyapunov_mastery: float
    bayesian_mastery: float
    kalman_mastery: float
    ensemble_variance: float
    
    # Pseudo-regret (until true regret is available)
    pseudo_regret: float = 0.0  # Will be updated later
    
    # 🔥 PHASE 2: Per-interaction objective function
    J_value: float = 0.0  # J_t computed from causal signals

@dataclass
class RollingMetrics:
    """Rolling statistics over multiple interactions"""
    
    # Learning velocity
    cumulative_gain: float = 0.0
    avg_gain_per_interaction: float = 0.0
    gain_variance: float = 0.0
    
    # Convergence metrics
    interactions_to_mastery: Dict[float, int] = field(default_factory=dict)
    # e.g., {0.5: 5, 0.8: 12} - took 5 interactions to reach 0.5 mastery
    
    # Transfer effectiveness
    total_transfer: float = 0.0
    transfer_efficiency_avg: float = 0.0
    total_transfer_contribution: float = 0.0  # 🔥 NEW: True transfer attribution
    
    # Policy performance
    cumulative_reward: float = 0.0
    avg_reward_per_interaction: float = 0.0
    
    # Performance metrics
    avg_response_time: float = 0.0
    zpd_alignment_avg: float = 0.0
    
    # Regret tracking
    cumulative_pseudo_regret: float = 0.0
    
    # 🔥 NEW: Per-user/concept convergence tracking
    mastery_crossings: Dict[Tuple[str, str, float], int] = field(default_factory=dict)
    
    # Sample size
    total_interactions: int = 0

class LearningMetricsAggregator:
    """
    Research-grade metrics aggregation for UnifiedLearningBrain
    
    Provides the measurement foundation for objective function definition
    """
    
    def __init__(self):
        self.interaction_history: List[InteractionMetrics] = []
        self.rolling_metrics = RollingMetrics()
        self.convergence_thresholds = [0.5, 0.7, 0.8, 0.9]
        
    def record_interaction(self, 
                      user_id: str,
                      concept: str,
                      mastery_before: float,
                      mastery_after: float,
                      transfer_amount: float = 0.0,
                      transfer_contribution: float = 0.0,  # 🔥 NEW: True transfer attribution
                      selected_action: str = "",
                      bandit_reward: float = 0.0,
                      policy_multiplier: float = 1.0,
                      response_time: float = 0.0,
                      difficulty: float = 0.5,
                      lyapunov_mastery: float = 0.3,
                      bayesian_mastery: float = 0.3,
                      kalman_mastery: float = 0.3,
                      ensemble_variance: float = 0.02,
                      J_value: float = 0.0) -> InteractionMetrics:  # 🔥 PHASE 2: Per-interaction J_t
        """
        Record a single learning interaction with all measurable signals
        """
        
        # Calculate learning gain
        learning_gain = mastery_after - mastery_before
        
        # Calculate ZPD gap
        zpd_target = mastery_before + 0.1  # ZPD target
        zpd_gap = abs(difficulty - zpd_target)
        
        # Create interaction metrics
        interaction = InteractionMetrics(
            user_id=user_id,
            concept=concept,
            timestamp=datetime.now(),
            
            # Core metrics
            mastery_before=mastery_before,
            mastery_after=mastery_after,
            learning_gain=learning_gain,
            
            # Transfer metrics
            transfer_amount=transfer_amount,
            transfer_contribution=transfer_contribution,  # 🔥 FIXED: Use the parameter value
            
            # Policy metrics
            selected_action=selected_action,
            bandit_reward=bandit_reward,
            policy_multiplier=policy_multiplier,
            
            # Performance metrics
            response_time=response_time,
            difficulty=difficulty,
            zpd_gap=zpd_gap,
            
            # Learner insights
            lyapunov_mastery=lyapunov_mastery,
            bayesian_mastery=bayesian_mastery,
            kalman_mastery=kalman_mastery,
            ensemble_variance=ensemble_variance,
            
            # 🔥 PHASE 2: Per-interaction objective function
            J_value=J_value
        )
        
        # Store and update rolling metrics
        self.interaction_history.append(interaction)
        self._update_rolling_metrics(interaction)
        
        logger.info(f"🔥 Recorded interaction: {user_id}/{concept} ΔM={learning_gain:.4f}, Transfer={transfer_amount:.4f}")
        
        return interaction
    
    def _update_rolling_metrics(self, interaction: InteractionMetrics):
        """Update rolling statistics after each interaction"""
        
        self.rolling_metrics.total_interactions += 1
        
        # Learning velocity
        self.rolling_metrics.cumulative_gain += interaction.learning_gain
        gains = [i.learning_gain for i in self.interaction_history]
        self.rolling_metrics.avg_gain_per_interaction = np.mean(gains)
        self.rolling_metrics.gain_variance = np.var(gains) if len(gains) > 1 else 0.0
        
        # 🔥 FIXED: Convergence tracking with per-user/concept thresholds
        current_mastery = interaction.mastery_after
        for threshold in self.convergence_thresholds:
            if current_mastery >= threshold:
                key = (interaction.user_id, interaction.concept, threshold)
                if key not in self.rolling_metrics.interactions_to_mastery:
                    self.rolling_metrics.interactions_to_mastery[key] = self.rolling_metrics.total_interactions
        
        # 🔥 FIXED: Transfer effectiveness with true attribution
        self.rolling_metrics.total_transfer += interaction.transfer_amount
        # 🔥 BULLETPROOF: Handle both float and dict for transfer_contribution
        if isinstance(interaction.transfer_contribution, dict):
            self.rolling_metrics.total_transfer_contribution += sum(interaction.transfer_contribution.values())
        else:
            self.rolling_metrics.total_transfer_contribution += float(interaction.transfer_contribution or 0.0)
        if self.rolling_metrics.cumulative_gain > 0:
            self.rolling_metrics.transfer_efficiency_avg = (
                self.rolling_metrics.total_transfer / self.rolling_metrics.cumulative_gain
            ) if self.rolling_metrics.cumulative_gain > 0 else 0.0
        
        # Policy performance
        self.rolling_metrics.cumulative_reward += interaction.bandit_reward
        rewards = [i.bandit_reward for i in self.interaction_history]
        self.rolling_metrics.avg_reward_per_interaction = np.mean(rewards) if rewards else 0.0
        
        # Performance metrics
        response_times = [i.response_time for i in self.interaction_history]
        self.rolling_metrics.avg_response_time = np.mean(response_times) if response_times else 0.0
        
        zpd_gaps = [i.zpd_gap for i in self.interaction_history]
        self.rolling_metrics.zpd_alignment_avg = np.mean(zpd_gaps) if zpd_gaps else 0.0
    
    def get_learning_velocity(self) -> float:
        """Calculate learning velocity (mastery per interaction)"""
        return self.rolling_metrics.avg_gain_per_interaction
    
    def get_convergence_time(self, mastery_threshold: float) -> Optional[int]:
        """Get interactions needed to reach mastery threshold"""
        return self.rolling_metrics.interactions_to_mastery.get(mastery_threshold)
    
    def get_transfer_efficiency(self) -> float:
        """Calculate transfer efficiency (transfer per learning gain)"""
        return self.rolling_metrics.transfer_efficiency_avg
    
    def get_policy_performance(self) -> float:
        """Get average policy reward"""
        return self.rolling_metrics.avg_reward_per_interaction
    
    def get_pseudo_regret(self) -> float:
        """Get cumulative pseudo-regret (placeholder until true regret)"""
        return self.rolling_metrics.cumulative_pseudo_regret
    
    def get_research_summary(self) -> Dict[str, float]:
        """
        Get research-grade summary of all metrics
        
        This is what we'll use to define the objective function
        """
        return {
            # Learning metrics
            'learning_velocity': self.get_learning_velocity(),
            'cumulative_gain': self.rolling_metrics.cumulative_gain,
            'gain_variance': self.rolling_metrics.gain_variance,
            
            # 🔥 FIXED: Convergence metrics with proper tracking
            'time_to_0.5_mastery': self._get_convergence_time_for_user_concept(0.5),
            'time_to_0.8_mastery': self._get_convergence_time_for_user_concept(0.8),
            
            # 🔥 FIXED: Transfer metrics with true attribution
            'transfer_efficiency': self.get_transfer_efficiency(),
            'total_transfer': self.rolling_metrics.total_transfer,
            'total_transfer_contribution': self.rolling_metrics.total_transfer_contribution,
            
            # Policy metrics
            'avg_reward': self.get_policy_performance(),
            'cumulative_reward': self.rolling_metrics.cumulative_reward,
            
            # Performance metrics
            'avg_response_time': self.rolling_metrics.avg_response_time,
            'zpd_alignment': self.rolling_metrics.zpd_alignment_avg,
            
            # Sample size
            'total_interactions': self.rolling_metrics.total_interactions,
            
            # Pseudo-regret
            'pseudo_regret': self.get_pseudo_regret(),
            
            # 🔥 PHASE 2: Objective function components
            'objective_function': self.compute_objective_function()
        }
    
    def compute_objective_function(self) -> float:
        """
        🔥 PHASE 2 CORRECTED: Research-grade objective function J
        
        CORRECTED: J = E[J_t] where J_t is computed per-interaction from causal signals
        
        This is the system's north star - what "good" means globally
        """
        # 🔥 CORRECTED: Use per-interaction J_t values, not aggregated metrics
        if not self.interaction_history:
            return 0.0
        
        # Get J_t values from enhanced interactions only (causal measurements)
        enhanced_interactions = [i for i in self.interaction_history if i.user_id.endswith('_enhanced')]
        
        if not enhanced_interactions:
            return 0.0
        
        # Compute J as expectation of J_t values
        J_values = [i.J_value for i in enhanced_interactions]
        J = sum(J_values) / len(J_values)
        
        return J
    
    def get_baseline_vs_enhanced_comparison(self) -> Dict[str, float]:
        """
        Get baseline vs enhanced comparison for causal analysis
        
        Returns comparison metrics between baseline and enhanced interactions
        """
        baseline_interactions = [i for i in self.interaction_history if i.user_id.endswith('_baseline')]
        enhanced_interactions = [i for i in self.interaction_history if i.user_id.endswith('_enhanced')]
        
        if not baseline_interactions or not enhanced_interactions:
            return {}
        
        # Get the most recent baseline and enhanced interactions
        baseline = baseline_interactions[0] if baseline_interactions else None
        enhanced = enhanced_interactions[0] if enhanced_interactions else None
        
        if not baseline or not enhanced:
            return {}
        
        # Calculate comparison metrics
        true_learning_gain = enhanced.mastery_after - baseline.mastery_before if baseline else 0.0
        total_learning_gain = enhanced.mastery_after - baseline.mastery_before if baseline else 0.0
        transfer_contribution = enhanced.transfer_contribution if enhanced else 0.0
        
        return {
            'baseline_mastery': baseline.mastery_after if baseline else 0.0,
            'enhanced_mastery': enhanced.mastery_after if enhanced else 0.0,
            'true_learning_gain': true_learning_gain,
            'total_learning_gain': total_learning_gain,
            'transfer_contribution': transfer_contribution,
            'transfer_efficiency': transfer_contribution / true_learning_gain if true_learning_gain > 0.001 else 0.0
        }
    
    def _get_convergence_time_for_user_concept(self, threshold: float) -> int:
        """🔥 FIXED: Get convergence time for current user/concept"""
        # This is a placeholder - in real implementation, we'd track the current user/concept
        # For now, return the first matching threshold found
        for key, interaction_num in self.rolling_metrics.interactions_to_mastery.items():
            if key[0] == self.interaction_history[-1].user_id and key[1] == self.interaction_history[-1].concept:
                if key[2] == threshold:
                    return interaction_num
        return 0
    
    def export_for_analysis(self) -> List[Dict]:
        """Export all interaction data for external analysis"""
        return [
            {
                'user_id': i.user_id,
                'concept': i.concept,
                'timestamp': i.timestamp.isoformat(),
                'mastery_before': i.mastery_before,
                'mastery_after': i.mastery_after,
                'learning_gain': i.learning_gain,
                'transfer_amount': i.transfer_amount,
                'bandit_reward': i.bandit_reward,
                'response_time': i.response_time,
                'difficulty': i.difficulty,
                'zpd_gap': i.zpd_gap,
                'ensemble_variance': i.ensemble_variance
            }
            for i in self.interaction_history
        ]
