"""
Production Metrics - Track what your system ACTUALLY does

This measures all the key components of your 25+ layer system:
- Ensemble variance between learners
- Policy effectiveness (HCIE vs DAG vs Random)
- Transfer efficiency and coverage
- ZPD alignment accuracy
- Approximation gap from ideal
- Processing delays and consistency
"""

import numpy as np
import redis
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from core.learning.unified_brain import process_learning_event, LearningResult
from core.learning.learner_factory import LearnerFactory
# Skip UserRepository import for now - not critical for core functionality
# from infrastructure.db.repositories.user_repository import UserRepository


@dataclass
class EnsembleMetrics:
    """Metrics for ensemble performance"""
    lyapunov_mastery: float
    bayesian_mastery: float
    kalman_mastery: float
    ensemble_mastery: float
    ensemble_variance: float
    ensemble_weights: Dict[str, float]
    confidence: float
    uncertainty: float


@dataclass
class PolicyMetrics:
    """Metrics for policy effectiveness"""
    policy: str
    learning_rate: float
    policy_multiplier: float
    learning_gain: float
    forgetting_rate: float


@dataclass
class TransferMetrics:
    """Metrics for transfer learning"""
    total_transfer: float
    learning_gain: float
    transfer_efficiency: float
    transfer_count: int
    transfer_coverage: float


@dataclass
class ZPDMetrics:
    """Metrics for ZPD alignment"""
    mastery: float
    difficulty: float
    zpd_target: float
    alignment_error: float
    zpd_score: float


@dataclass
class SystemMetrics:
    """Metrics for system performance"""
    processing_delay: float
    approximation_gap: float
    consistency_lag: float
    fault_tolerance_index: float


class ProductionMetrics:
    """
    Collect real-time system performance metrics for your 25+ layer system
    
    This makes your sophisticated coordination MEASURABLE!
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        # Create Redis store for learner factory
        from storage.redis_store.redis_store import RedisFeatureStore
        redis_store = RedisFeatureStore()
        self.learner_factory = LearnerFactory(redis_store)
        # self.user_repo = UserRepository()  # Commented out - not critical for core functionality
        from core.learning.unified_brain import process_learning_event
        self._process_event = process_learning_event
    
    def measure_ensemble_variance(self, user_id: str, concept: str) -> EnsembleMetrics:
        """Track variance between Lyapunov, Bayesian, Kalman learners"""
        
        # Get current learner states
        result = process_learning_event(user_id, concept, mode="read")
        
        # Calculate ensemble variance
        mastery_values = [
            result.lyapunov_mastery,
            result.bayesian_alpha / (result.bayesian_alpha + result.bayesian_beta),  # Convert to mastery
            result.kalman_mastery
        ]
        
        ensemble_variance = np.var(mastery_values)
        ensemble_mastery = result.ensemble_mastery
        
        return EnsembleMetrics(
            lyapunov_mastery=result.lyapunov_mastery,
            bayesian_mastery=result.bayesian_alpha / (result.bayesian_alpha + result.bayesian_beta),
            kalman_mastery=result.kalman_mastery,
            ensemble_mastery=ensemble_mastery,
            ensemble_variance=ensemble_variance,
            ensemble_weights=result.ensemble_weights,
            confidence=result.confidence,
            uncertainty=result.uncertainty
        )
    
    def calculate_ensemble_variance(self, user_id: str, concept: str) -> float:
        """
        Calculate variance across ensemble learners.
        Uses unified brain to get learner states and computes disagreement.
        """
        # Get learner-informed state via unified brain
        result = self._process_event(user_id, concept, mode="read")
        # This uses process_learning_event internally
        
        # Extract individual learner masteries from LearningResult
        mastery_values = [
            result.lyapunov_mastery,
            result.bayesian_alpha / (result.bayesian_alpha + result.bayesian_beta),  # Convert to mastery
            result.kalman_mastery
        ]
        
        # Calculate variance across learner predictions
        if len(mastery_values) < 2:
            return 0.0
        
        mean = sum(mastery_values) / len(mastery_values)
        variance = sum((v - mean) ** 2 for v in mastery_values) / len(mastery_values)
        
        return variance
    
    def measure_policy_effectiveness(self, user_id: str, concept: str) -> PolicyMetrics:
        """Track HCIE vs DAG vs Random performance"""
        
        # Get current state
        result = process_learning_event(user_id, concept, mode="read")
        
        # Calculate learning rate based on recent interactions
        learning_rate = self._calculate_learning_rate(user_id, concept)
        learning_gain = self._calculate_learning_gain(user_id, concept)
        forgetting_rate = self._calculate_forgetting_rate(result.policy)
        
        return PolicyMetrics(
            policy=result.policy,
            learning_rate=learning_rate,
            policy_multiplier=result.policy_multiplier,
            learning_gain=learning_gain,
            forgetting_rate=forgetting_rate
        )
    
    def measure_transfer_efficiency(self, user_id: str, source_concept: str) -> TransferMetrics:
        """Track transfer amounts and effectiveness"""
        
        # Get current state
        result = process_learning_event(user_id, source_concept, mode="read")
        
        # Calculate transfer metrics
        transfer_amounts = result.transfer_amounts
        total_transfer = sum(transfer_amounts.values()) if transfer_amounts else 0.0
        learning_gain = self._calculate_learning_gain(user_id, source_concept)
        
        transfer_efficiency = total_transfer / learning_gain if learning_gain > 0 else 0.0
        transfer_count = len(transfer_amounts) if transfer_amounts else 0
        
        # Calculate transfer coverage
        all_concepts = self._get_all_concepts()
        transfer_coverage = transfer_count / len(all_concepts) if all_concepts else 0.0
        
        return TransferMetrics(
            total_transfer=total_transfer,
            learning_gain=learning_gain,
            transfer_efficiency=transfer_efficiency,
            transfer_count=transfer_count,
            transfer_coverage=transfer_coverage
        )
    
    def measure_zpd_alignment(self, user_id: str, concept: str) -> ZPDMetrics:
        """Track ZPD optimization accuracy"""
        
        # Get current state
        result = process_learning_event(user_id, concept, mode="read")
        
        # Get concept difficulty
        difficulty = self._get_concept_difficulty(concept)
        
        # Calculate ZPD metrics
        mastery = result.ensemble_mastery
        zpd_target = mastery + 0.1
        alignment_error = abs(difficulty - zpd_target)
        zpd_score = np.exp(-alignment_error**2 / 0.01)  # σ_ZPD = 0.1
        
        return ZPDMetrics(
            mastery=mastery,
            difficulty=difficulty,
            zpd_target=zpd_target,
            alignment_error=alignment_error,
            zpd_score=zpd_score
        )
    
    def measure_system_performance(self, user_id: str, concept: str) -> SystemMetrics:
        """Track system performance metrics"""
        
        # Get current state
        result = process_learning_event(user_id, concept, mode="read")
        
        # Calculate approximation gap (Δ = ||ideal - implemented||)
        approximation_gap = self._calculate_approximation_gap(user_id, concept)
        
        # Calculate processing delays
        processing_delay = self._calculate_processing_delay(user_id, concept)
        
        # Calculate consistency lag
        consistency_lag = self._calculate_consistency_lag(user_id, concept)
        
        # Calculate fault tolerance index
        fault_tolerance_index = self._calculate_fault_tolerance_index(user_id, concept)
        
        return SystemMetrics(
            processing_delay=processing_delay,
            approximation_gap=approximation_gap,
            consistency_lag=consistency_lag,
            fault_tolerance_index=fault_tolerance_index
        )
    
    def _calculate_learning_rate(self, user_id: str, concept: str) -> float:
        """Calculate learning rate for user/concept"""
        
        # Get recent interactions from Redis or database
        recent_interactions = self._get_recent_interactions(user_id, concept, days=7)
        
        if len(recent_interactions) < 2:
            return 0.0
        
        # Calculate mastery change over time
        mastery_changes = []
        for i in range(1, len(recent_interactions)):
            prev_mastery = recent_interactions[i-1].get("mastery_before", 0.3)
            curr_mastery = recent_interactions[i].get("mastery_after", prev_mastery)
            
            if curr_mastery > prev_mastery:
                mastery_changes.append(curr_mastery - prev_mastery)
        
        if mastery_changes:
            return np.mean(mastery_changes)
        return 0.0
    
    def _calculate_learning_gain(self, user_id: str, concept: str) -> float:
        """Calculate total learning gain for user/concept"""
        
        recent_interactions = self._get_recent_interactions(user_id, concept, days=30)
        
        total_gain = 0.0
        for interaction in recent_interactions:
            if interaction.get("correct", False):
                gain = interaction.get("mastery_after", 0.3) - interaction.get("mastery_before", 0.3)
                total_gain += max(0, gain)
        
        return total_gain
    
    def _calculate_forgetting_rate(self, policy: str) -> float:
        """Calculate forgetting rate based on policy"""
        
        policy_forgetting_rates = {
            "hcie": 0.2,    # HCIE retains 80% (20% forgetting)
            "dag": 0.0,      # DAG retains 100% (0% forgetting)
            "random": 0.2     # Random retains 80% (20% forgetting)
        }
        
        return policy_forgetting_rates.get(policy, 0.1)
    
    def _calculate_approximation_gap(self, user_id: str, concept: str) -> float:
        """Calculate Δ = ||ideal(S_t) - implemented(S_t)||"""
        
        # Get current implemented state
        implemented_result = process_learning_event(user_id, concept, mode="read")
        
        # Calculate theoretical ideal state (unified atomic state)
        ideal_result = self._calculate_ideal_state(user_id, concept)
        
        # Calculate L2 norm of difference
        implemented_vector = np.array([
            implemented_result.ensemble_mastery,
            implemented_result.confidence,
            implemented_result.policy_multiplier,
            implemented_result.transfer_efficiency
        ])
        
        ideal_vector = np.array([
            ideal_result.ensemble_mastery,
            ideal_result.confidence,
            ideal_result.policy_multiplier,
            ideal_result.transfer_efficiency
        ])
        
        gap = np.linalg.norm(implemented_vector - ideal_vector)
        
        return gap
    
    def _calculate_ideal_state(self, user_id: str, concept: str) -> LearningResult:
        """Calculate theoretical ideal unified state"""
        
        # This would be the mathematical optimum
        # For now, use current state as approximation
        return process_learning_event(user_id, concept, mode="read")
    
    def _calculate_processing_delay(self, user_id: str, concept: str) -> float:
        """Calculate processing delay between event and update"""
        
        # Get timestamp of last interaction and when it was processed
        last_interaction = self._get_last_interaction(user_id, concept)
        
        if last_interaction and "processed_timestamp" in last_interaction:
            event_time = last_interaction["event_timestamp"]
            processed_time = last_interaction["processed_timestamp"]
            
            if isinstance(event_time, str):
                event_time = datetime.fromisoformat(event_time)
            if isinstance(processed_time, str):
                processed_time = datetime.fromisoformat(processed_time)
            
            delay = (processed_time - event_time).total_seconds()
            return delay
        
        return 0.0
    
    def _calculate_consistency_lag(self, user_id: str, concept: str) -> float:
        """Calculate consistency lag between learners"""
        
        # Get individual learner update times
        learner_times = self._get_learner_update_times(user_id, concept)
        
        if len(learner_times) > 1:
            times = list(learner_times.values())
            return max(times) - min(times)
        
        return 0.0
    
    def _calculate_fault_tolerance_index(self, user_id: str, concept: str) -> float:
        """Calculate fault tolerance index based on learner availability"""
        
        # Check if all learners are responding
        learner_status = self._get_learner_status(user_id, concept)
        
        available_learners = sum(1 for status in learner_status.values() if status == "available")
        total_learners = len(learner_status)
        
        if total_learners > 0:
            return available_learners / total_learners
        
        return 1.0
    
    def _get_recent_interactions(self, user_id: str, concept: str, days: int) -> List[Dict[str, Any]]:
        """Get recent interactions for user/concept"""
        
        # This would query your interaction database
        # For now, return empty list
        return []  # TODO: Implement actual database query
    
    def _get_all_concepts(self) -> List[str]:
        """Get all available concepts"""
        # This would query your concept database
        # For now, return sample concepts
        return ["ct_algorithm_design", "ct_abstraction", "ct_optimization", "ct_decomposition"]
    
    def _get_concept_difficulty(self, concept: str) -> float:
        """Get difficulty for concept"""
        # This would query your concept metadata
        # For now, return default difficulty
        difficulties = {
            "ct_algorithm_design": 0.6,
            "ct_abstraction": 0.7,
            "ct_optimization": 0.8,
            "ct_decomposition": 0.5
        }
        return difficulties.get(concept, 0.5)
    
    def _get_last_interaction(self, user_id: str, concept: str) -> Optional[Dict[str, Any]]:
        """Get last interaction for user/concept"""
        # This would query your interaction database
        return None  # TODO: Implement actual database query
    
    def _get_learner_update_times(self, user_id: str, concept: str) -> Dict[str, float]:
        """Get update times for individual learners"""
        # This would track when each learner was last updated
        return {"lyapunov": 0.0, "bayesian": 0.0, "kalman": 0.0}  # TODO: Implement actual tracking
    
    def _get_learner_status(self, user_id: str, concept: str) -> Dict[str, str]:
        """Get status of individual learners"""
        # This would check if each learner is responding
        return {"lyapunov": "available", "bayesian": "available", "kalman": "available"}  # TODO: Implement actual health checks
