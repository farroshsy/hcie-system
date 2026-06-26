"""
C2.3.2 - Counterfactual Policy Replay

Replay same learner trajectory with different policy versions and compare outcomes.

This enables educational simulation science:
- Replay same trajectory with v1.0.0, v1.1.0, conservative pacing, aggressive pacing
- Compare mastery growth, pacing stability, misconception recurrence, intervention effectiveness
- Answer "what if" questions about pedagogical policy decisions

Builds on C2.3.1 Deterministic Canonical Replay Engine.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
import logging
import copy

from core.replay.deterministic_replay_engine import (
    ReplayEvent,
    ReplayEventType,
    ReplayCognitionState,
    ReplayProjectionState,
    ReplayAdaptationState,
    ReplayResult,
    DeterministicReplayEngine
)

logger = logging.getLogger(__name__)


class CounterfactualPolicy(Enum):
    """Counterfactual policy variants for comparison."""
    V1_0_0 = "v1.0.0"
    V1_1_0 = "v1.1.0"
    CONSERVATIVE_PACING = "conservative_pacing"
    AGGRESSIVE_PACING = "aggressive_pacing"
    NO_INTERVENTION = "no_intervention"
    MAX_REMEDIATION = "max_remediation"


@dataclass
class PolicyComparisonMetrics:
    """
    Metrics for comparing policy outcomes.
    
    Focus on pedagogical semantic trajectories (learning), NOT infrastructure metrics.
    """
    policy_version: str
    
    # Mastery growth metrics
    final_mastery: float
    mastery_growth: float
    mastery_velocity: float  # mastery per unit time
    
    # Pacing stability metrics
    pacing_variance: float
    pacing_oscillation_count: int
    average_adaptation_interval: float
    
    # Misconception recurrence metrics
    misconception_recurrence_rate: float
    remediation_success_rate: float
    stubborn_misconception_count: int
    
    # Intervention effectiveness metrics
    total_interventions: int
    successful_interventions: int
    intervention_effectiveness_rate: float
    
    # Overall pedagogical outcome
    learning_efficiency: float  # mastery growth per intervention
    engagement_stability: float  # consistency of engagement


@dataclass
class CounterfactualComparison:
    """
    Result of counterfactual policy comparison.
    
    Compares multiple policy replays of the same learner trajectory.
    """
    user_id: str
    original_policy: str
    counterfactual_policies: List[str]
    comparison_timestamp: datetime
    
    # Replay results per policy
    policy_replays: Dict[str, ReplayResult] = field(default_factory=dict)
    
    # Comparison metrics per policy
    policy_metrics: Dict[str, PolicyComparisonMetrics] = field(default_factory=dict)
    
    # Comparative analysis
    best_policy_for_mastery: Optional[str] = None
    best_policy_for_stability: Optional[str] = None
    best_policy_for_efficiency: Optional[str] = None
    
    # Statistical significance
    mastery_delta_significant: bool = False
    stability_delta_significant: bool = False


class CounterfactualReplayEngine:
    """
    Counterfactual policy replay engine for educational simulation science.
    
    Replays the same learner trajectory under different policy versions to compare:
    - Mastery growth trajectories
    - Pacing stability
    - Misconception recurrence patterns
    - Intervention effectiveness
    
    Uses deterministic replay from C2.3.1 with policy substitution.
    """
    
    def __init__(self, policy_snapshot_repository=None):
        """
        Initialize counterfactual replay engine.
        
        Args:
            policy_snapshot_repository: Repository for retrieving immutable policy snapshots
        """
        self._base_replay_engine = DeterministicReplayEngine(policy_snapshot_repository)
        self._policy_snapshot_repository = policy_snapshot_repository
    
    def replay_with_policy_substitution(
        self,
        user_id: str,
        events: List[ReplayEvent],
        target_policy: CounterfactualPolicy,
        initial_cognition: Optional[ReplayCognitionState] = None
    ) -> ReplayResult:
        """
        Replay learner trajectory with policy substitution.
        
        Substitutes the policy version in AdaptationGenerated events to simulate
        what would have happened under a different policy.
        
        Args:
            user_id: User ID to replay
            events: Original event stream
            target_policy: Counterfactual policy to substitute
            initial_cognition: Optional initial cognition state
            
        Returns:
            ReplayResult with counterfactual state reconstruction
        """
        logger.info(f"🔄 Replaying user {user_id} with counterfactual policy: {target_policy.value}")
        
        # Substitute policy in adaptation events
        counterfactual_events = self._substitute_policy_in_events(events, target_policy)
        
        # Replay with substituted events
        result = self._base_replay_engine.replay_learner_trajectory(
            user_id=user_id,
            events=counterfactual_events,
            initial_cognition=initial_cognition
        )
        
        logger.info(f"✅ Counterfactual replay completed for user {user_id} with policy {target_policy.value}")
        
        return result
    
    def _substitute_policy_in_events(
        self,
        events: List[ReplayEvent],
        target_policy: CounterfactualPolicy
    ) -> List[ReplayEvent]:
        """
        Substitute policy version in adaptation events.
        
        Creates a counterfactual event stream where AdaptationGenerated events
        use the target policy version instead of the original.
        
        Args:
            events: Original event stream
            target_policy: Target policy to substitute
            
        Returns:
            Counterfactual event stream with policy substitution
        """
        counterfactual_events = []
        
        for event in events:
            # Create deep copy to avoid mutating original
            counterfactual_event = copy.deepcopy(event)
            
            # Substitute policy in AdaptationGenerated events
            if event.event_type == ReplayEventType.ADAPTATION_GENERATED:
                counterfactual_event.policy_version = target_policy.value
                
                # Update payload to reflect policy substitution
                if counterfactual_event.payload:
                    counterfactual_event.payload["policy_version"] = target_policy.value
            
            counterfactual_events.append(counterfactual_event)
        
        return counterfactual_events
    
    def compare_counterfactual_policies(
        self,
        user_id: str,
        events: List[ReplayEvent],
        policies: List[CounterfactualPolicy],
        initial_cognition: Optional[ReplayCognitionState] = None
    ) -> CounterfactualComparison:
        """
        Compare multiple counterfactual policies for the same learner trajectory.
        
        Replays the same event stream under each policy and compares outcomes.
        
        Args:
            user_id: User ID to replay
            events: Original event stream
            policies: List of counterfactual policies to compare
            initial_cognition: Optional initial cognition state
            
        Returns:
            CounterfactualComparison with comparative analysis
        """
        logger.info(f"🔄 Comparing {len(policies)} counterfactual policies for user {user_id}")
        
        comparison = CounterfactualComparison(
            user_id=user_id,
            original_policy=self._extract_original_policy(events),
            counterfactual_policies=[p.value for p in policies],
            comparison_timestamp=datetime.utcnow()
        )
        
        # Replay under each policy
        for policy in policies:
            replay_result = self.replay_with_policy_substitution(
                user_id=user_id,
                events=events,
                target_policy=policy,
                initial_cognition=initial_cognition
            )
            
            comparison.policy_replays[policy.value] = replay_result
            
            # Compute comparison metrics
            metrics = self._compute_policy_metrics(replay_result, policy.value)
            comparison.policy_metrics[policy.value] = metrics
        
        # Perform comparative analysis
        comparison.best_policy_for_mastery = self._find_best_policy(
            comparison.policy_metrics, "mastery_growth"
        )
        comparison.best_policy_for_stability = self._find_best_policy(
            comparison.policy_metrics, "pacing_variance"
        )
        comparison.best_policy_for_efficiency = self._find_best_policy(
            comparison.policy_metrics, "learning_efficiency"
        )
        
        # Check statistical significance
        comparison.mastery_delta_significant = self._check_significance(
            comparison.policy_metrics, "mastery_growth"
        )
        comparison.stability_delta_significant = self._check_significance(
            comparison.policy_metrics, "pacing_variance"
        )
        
        logger.info(f"✅ Counterfactual comparison completed for user {user_id}")
        
        return comparison
    
    def _extract_original_policy(self, events: List[ReplayEvent]) -> str:
        """Extract original policy from event stream."""
        for event in events:
            if event.event_type == ReplayEventType.ADAPTATION_GENERATED:
                if event.policy_version:
                    return event.policy_version
        return "unknown"
    
    def _compute_policy_metrics(
        self,
        replay_result: ReplayResult,
        policy_version: str
    ) -> PolicyComparisonMetrics:
        """
        Compute comparison metrics for a policy replay.
        
        Args:
            replay_result: Result from replay
            policy_version: Policy version being evaluated
            
        Returns:
            PolicyComparisonMetrics with pedagogical trajectory metrics
        """
        final_cognition = replay_result.final_cognition
        
        # Mastery growth metrics
        final_mastery = final_cognition.mastery
        mastery_growth = final_mastery  # Assuming start from 0
        mastery_velocity = mastery_growth / max(replay_result.processing_time_seconds, 0.001)
        
        # Pacing stability metrics (simplified - would need full event analysis)
        pacing_variance = 0.1  # Placeholder - would compute from adaptation intervals
        pacing_oscillation_count = 0  # Placeholder
        average_adaptation_interval = 10.0  # Placeholder
        
        # Misconception recurrence metrics (simplified)
        misconception_recurrence_rate = 0.2  # Placeholder
        remediation_success_rate = 0.7  # Placeholder
        stubborn_misconception_count = 0  # Placeholder
        
        # Intervention effectiveness metrics
        total_interventions = len([e for e in replay_result.events_processed 
                                   if e.event_type == ReplayEventType.ADAPTATION_GENERATED])
        successful_interventions = int(total_interventions * 0.6)  # Placeholder
        intervention_effectiveness_rate = (successful_interventions / max(total_interventions, 1))
        
        # Overall pedagogical outcome
        learning_efficiency = mastery_growth / max(total_interventions, 1)
        engagement_stability = 0.8  # Placeholder
        
        return PolicyComparisonMetrics(
            policy_version=policy_version,
            final_mastery=final_mastery,
            mastery_growth=mastery_growth,
            mastery_velocity=mastery_velocity,
            pacing_variance=pacing_variance,
            pacing_oscillation_count=pacing_oscillation_count,
            average_adaptation_interval=average_adaptation_interval,
            misconception_recurrence_rate=misconception_recurrence_rate,
            remediation_success_rate=remediation_success_rate,
            stubborn_misconception_count=stubborn_misconception_count,
            total_interventions=total_interventions,
            successful_interventions=successful_interventions,
            intervention_effectiveness_rate=intervention_effectiveness_rate,
            learning_efficiency=learning_efficiency,
            engagement_stability=engagement_stability
        )
    
    def _find_best_policy(
        self,
        policy_metrics: Dict[str, PolicyComparisonMetrics],
        metric_name: str
    ) -> Optional[str]:
        """
        Find best policy for a given metric.
        
        Args:
            policy_metrics: Metrics per policy
            metric_name: Metric to optimize (e.g., "mastery_growth", "pacing_variance")
            
        Returns:
            Best policy for the metric
        """
        if not policy_metrics:
            return None
        
        best_policy = None
        best_value = None
        
        for policy, metrics in policy_metrics.items():
            value = getattr(metrics, metric_name, None)
            if value is None:
                continue
            
            # For variance metrics, lower is better
            if "variance" in metric_name or "recurrence" in metric_name:
                if best_value is None or value < best_value:
                    best_value = value
                    best_policy = policy
            else:
                # For growth metrics, higher is better
                if best_value is None or value > best_value:
                    best_value = value
                    best_policy = policy
        
        return best_policy
    
    def _check_significance(
        self,
        policy_metrics: Dict[str, PolicyComparisonMetrics],
        metric_name: str
    ) -> bool:
        """
        Check if metric differences are statistically significant.
        
        Simplified check - in production would use proper statistical tests.
        
        Args:
            policy_metrics: Metrics per policy
            metric_name: Metric to check
            
        Returns:
            True if differences are significant
        """
        values = [getattr(m, metric_name, 0) for m in policy_metrics.values()]
        
        if len(values) < 2:
            return False
        
        # Simple variance check
        mean_value = sum(values) / len(values)
        variance = sum((v - mean_value) ** 2 for v in values) / len(values)
        
        # Consider significant if variance > 10% of mean
        return variance > 0.1 * abs(mean_value)
