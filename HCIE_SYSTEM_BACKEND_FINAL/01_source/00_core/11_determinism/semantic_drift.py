"""
C2.3.3 - Semantic Drift Analysis

Detect same learner trajectory → different semantic interpretations caused by policy evolution.

This detects:
- Ontology drift (semantic meaning changes across policy versions)
- Semantic instability (inconsistent interpretations)
- Pedagogical inconsistency (different narratives for same state)
- Replay invalidation risk (replay no longer valid due to drift)

Focus on pedagogical semantic trajectories (learning), NOT infrastructure metrics.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import logging

from core.replay.deterministic_replay_engine import (
    ReplayEvent,
    ReplayEventType,
    ReplayCognitionState,
    ReplayProjectionState,
    ReplayAdaptationState,
    ReplayResult,
    DeterministicReplayEngine
)
from core.replay.counterfactual_replay import (
    CounterfactualPolicy,
    CounterfactualReplayEngine
)

logger = logging.getLogger(__name__)


class SemanticDriftType(Enum):
    """Types of semantic drift to detect."""
    READINESS_SEMANTICS = "readiness_semantics"
    INTERVENTION_TIMING = "intervention_timing"
    PEDAGOGICAL_NARRATIVE = "pedagogical_narrative"
    PACING_SEMANTICS = "pacing_semantics"
    ADAPTATION_TYPE = "adaptation_type"
    RECOMMENDATION_SEMANTICS = "recommendation_semantics"


@dataclass
class SemanticDifference:
    """
    Represents a semantic difference between two policy interpretations.
    
    Captures how the same learner trajectory is interpreted differently
    under different policy versions.
    """
    drift_type: SemanticDriftType
    policy_a: str
    policy_b: str
    
    # Cognition state that triggered the difference
    trigger_cognition: ReplayCognitionState
    
    # Different interpretations
    interpretation_a: Any
    interpretation_b: Any
    
    # Magnitude of difference (normalized 0-1)
    difference_magnitude: float
    
    # Impact assessment
    impact_level: str  # low, medium, high, critical
    
    # Context
    event_timestamp: datetime
    concept_id: Optional[str] = None


@dataclass
class SemanticDriftReport:
    """
    Comprehensive semantic drift analysis report.
    
    Summarizes all detected semantic differences across policy versions.
    """
    user_id: str
    analysis_timestamp: datetime
    
    # Policies compared
    policies_compared: List[str]
    
    # Detected drifts
    semantic_differences: List[SemanticDifference] = field(default_factory=list)
    
    # Drift summary by type
    drift_summary: Dict[SemanticDriftType, int] = field(default_factory=dict)
    
    # Overall drift assessment
    overall_drift_score: float = 0.0  # 0-1, higher = more drift
    drift_severity: str = "none"  # none, low, medium, high, critical
    
    # Replay validity assessment
    replay_valid: bool = True
    replay_invalidation_reason: Optional[str] = None
    
    # Pedagogical consistency
    pedagogical_consistency_score: float = 1.0  # 0-1, higher = more consistent


class SemanticDriftAnalyzer:
    """
    Analyzes semantic drift across policy versions.
    
    Detects how the same learner trajectory is interpreted differently
    under different policy versions, identifying ontology drift, semantic
    instability, and replay invalidation risks.
    """
    
    def __init__(self, counterfactual_engine: CounterfactualReplayEngine):
        """
        Initialize semantic drift analyzer.
        
        Args:
            counterfactual_engine: Engine for replaying with policy substitution
        """
        self._counterfactual_engine = counterfactual_engine
    
    def analyze_semantic_drift(
        self,
        user_id: str,
        events: List[ReplayEvent],
        policies: List[CounterfactualPolicy],
        initial_cognition: Optional[ReplayCognitionState] = None
    ) -> SemanticDriftReport:
        """
        Analyze semantic drift across multiple policy versions.
        
        Replays the same event stream under each policy and compares
        the semantic interpretations to detect drift.
        
        Args:
            user_id: User ID to analyze
            events: Original event stream
            policies: Policies to compare
            initial_cognition: Optional initial cognition state
            
        Returns:
            SemanticDriftReport with comprehensive drift analysis
        """
        logger.info(f"🔄 Analyzing semantic drift for user {user_id} across {len(policies)} policies")
        
        # Get counterfactual replay results
        comparison = self._counterfactual_engine.compare_counterfactual_policies(
            user_id=user_id,
            events=events,
            policies=policies,
            initial_cognition=initial_cognition
        )
        
        # Build drift report
        report = SemanticDriftReport(
            user_id=user_id,
            analysis_timestamp=datetime.utcnow(),
            policies_compared=[p.value for p in policies]
        )
        
        # Detect semantic differences
        for policy_a, policy_b in self._generate_policy_pairs(policies):
            differences = self._detect_differences_between_policies(
                comparison.policy_replays[policy_a.value],
                comparison.policy_replays[policy_b.value],
                policy_a.value,
                policy_b.value
            )
            report.semantic_differences.extend(differences)
        
        # Summarize drift by type
        for diff in report.semantic_differences:
            report.drift_summary[diff.drift_type] = report.drift_summary.get(diff.drift_type, 0) + 1
        
        # Compute overall drift score
        report.overall_drift_score = self._compute_drift_score(report.semantic_differences)
        report.drift_severity = self._assess_drift_severity(report.overall_drift_score)
        
        # Assess replay validity
        report.replay_valid, report.replay_invalidation_reason = self._assess_replay_validity(report)
        
        # Compute pedagogical consistency
        report.pedagogical_consistency_score = self._compute_consistency_score(report.semantic_differences)
        
        logger.info(f"✅ Semantic drift analysis completed for user {user_id}: {report.drift_severity} drift")
        
        return report
    
    def _generate_policy_pairs(self, policies: List[CounterfactualPolicy]) -> List[Tuple[CounterfactualPolicy, CounterfactualPolicy]]:
        """Generate all unique policy pairs for comparison."""
        pairs = []
        for i in range(len(policies)):
            for j in range(i + 1, len(policies)):
                pairs.append((policies[i], policies[j]))
        return pairs
    
    def _detect_differences_between_policies(
        self,
        replay_a: ReplayResult,
        replay_b: ReplayResult,
        policy_a: str,
        policy_b: str
    ) -> List[SemanticDifference]:
        """
        Detect semantic differences between two policy replays.
        
        Compares adaptation events to detect differences in pedagogical
        interpretations of the same cognitive state.
        
        Args:
            replay_a: Replay result for policy A
            replay_b: Replay result for policy B
            policy_a: Policy A version
            policy_b: Policy B version
            
        Returns:
            List of semantic differences
        """
        differences = []
        
        # Get adaptation events from both replays
        adaptations_a = [e for e in replay_a.events_processed 
                        if e.event_type == ReplayEventType.ADAPTATION_GENERATED]
        adaptations_b = [e for e in replay_b.events_processed 
                        if e.event_type == ReplayEventType.ADAPTATION_GENERATED]
        
        # Compare adaptation events
        min_adaptations = min(len(adaptations_a), len(adaptations_b))
        for i in range(min_adaptations):
            diff = self._compare_adaptation_events(
                adaptations_a[i],
                adaptations_b[i],
                policy_a,
                policy_b
            )
            if diff:
                differences.append(diff)
        
        # Compare final projections
        projection_diff = self._compare_projections(
            replay_a.final_projection,
            replay_b.final_projection,
            policy_a,
            policy_b
        )
        if projection_diff:
            differences.append(projection_diff)
        
        return differences
    
    def _compare_adaptation_events(
        self,
        adaptation_a: ReplayEvent,
        adaptation_b: ReplayEvent,
        policy_a: str,
        policy_b: str
    ) -> Optional[SemanticDifference]:
        """
        Compare two adaptation events for semantic differences.
        
        Args:
            adaptation_a: Adaptation event from policy A
            adaptation_b: Adaptation event from policy B
            policy_a: Policy A version
            policy_b: Policy B version
            
        Returns:
            SemanticDifference if drift detected, None otherwise
        """
        payload_a = adaptation_a.payload or {}
        payload_b = adaptation_b.payload or {}
        
        # Check adaptation type difference
        if payload_a.get("adaptation_type") != payload_b.get("adaptation_type"):
            return SemanticDifference(
                drift_type=SemanticDriftType.ADAPTATION_TYPE,
                policy_a=policy_a,
                policy_b=policy_b,
                trigger_cognition=ReplayCognitionState(
                    mastery=0.5,
                    uncertainty=0.3,
                    zpd_score=0.4,
                    bayesian_alpha=5.0,
                    bayesian_beta=5.0,
                    kalman_mastery=0.5,
                    kalman_covariance=0.1,
                    lyapunov_mastery=0.5
                ),
                interpretation_a=payload_a.get("adaptation_type"),
                interpretation_b=payload_b.get("adaptation_type"),
                difference_magnitude=0.8,
                impact_level="high",
                event_timestamp=adaptation_a.timestamp,
                concept_id=payload_a.get("concept_id")
            )
        
        # Check recommendation difference
        if payload_a.get("recommendation") != payload_b.get("recommendation"):
            return SemanticDifference(
                drift_type=SemanticDriftType.RECOMMENDATION_SEMANTICS,
                policy_a=policy_a,
                policy_b=policy_b,
                trigger_cognition=ReplayCognitionState(
                    mastery=0.5,
                    uncertainty=0.3,
                    zpd_score=0.4,
                    bayesian_alpha=5.0,
                    bayesian_beta=5.0,
                    kalman_mastery=0.5,
                    kalman_covariance=0.1,
                    lyapunov_mastery=0.5
                ),
                interpretation_a=payload_a.get("recommendation"),
                interpretation_b=payload_b.get("recommendation"),
                difference_magnitude=0.5,
                impact_level="medium",
                event_timestamp=adaptation_a.timestamp,
                concept_id=payload_a.get("concept_id")
            )
        
        return None
    
    def _compare_projections(
        self,
        projection_a: ReplayProjectionState,
        projection_b: ReplayProjectionState,
        policy_a: str,
        policy_b: str
    ) -> Optional[SemanticDifference]:
        """
        Compare two projection states for semantic differences.
        
        Args:
            projection_a: Projection from policy A
            projection_b: Projection from policy B
            policy_a: Policy A version
            policy_b: Policy B version
            
        Returns:
            SemanticDifference if drift detected, None otherwise
        """
        # Compare UX semantics if available
        if hasattr(projection_a, 'ux_semantics') and hasattr(projection_b, 'ux_semantics'):
            ux_a = projection_a.ux_semantics or {}
            ux_b = projection_b.ux_semantics or {}
            
            # Check pedagogical state difference
            if ux_a.get("pedagogical_state") != ux_b.get("pedagogical_state"):
                return SemanticDifference(
                drift_type=SemanticDriftType.PEDAGOGICAL_NARRATIVE,
                policy_a=policy_a,
                policy_b=policy_b,
                trigger_cognition=ReplayCognitionState(
                    mastery=0.5,
                    uncertainty=0.3,
                    zpd_score=0.4,
                    bayesian_alpha=5.0,
                    bayesian_beta=5.0,
                    kalman_mastery=0.5,
                    kalman_covariance=0.1,
                    lyapunov_mastery=0.5
                ),
                interpretation_a=ux_a.get("pedagogical_state"),
                interpretation_b=ux_b.get("pedagogical_state"),
                difference_magnitude=0.6,
                impact_level="medium",
                event_timestamp=datetime.utcnow()
            )
        
        return None
    
    def _compute_drift_score(self, differences: List[SemanticDifference]) -> float:
        """
        Compute overall drift score from semantic differences.
        
        Args:
            differences: List of semantic differences
            
        Returns:
            Drift score (0-1, higher = more drift)
        """
        if not differences:
            return 0.0
        
        # Weighted sum of difference magnitudes
        total_magnitude = sum(diff.difference_magnitude for diff in differences)
        max_possible = len(differences)  # Each diff max magnitude is 1
        
        return min(total_magnitude / max_possible, 1.0)
    
    def _assess_drift_severity(self, drift_score: float) -> str:
        """
        Assess drift severity from drift score.
        
        Args:
            drift_score: Drift score (0-1)
            
        Returns:
            Severity level (none, low, medium, high, critical)
        """
        if drift_score == 0.0:
            return "none"
        elif drift_score < 0.2:
            return "low"
        elif drift_score < 0.5:
            return "medium"
        elif drift_score < 0.8:
            return "high"
        else:
            return "critical"
    
    def _assess_replay_validity(self, report: SemanticDriftReport) -> Tuple[bool, Optional[str]]:
        """
        Assess whether replay is still valid given the detected drift.
        
        Args:
            report: Semantic drift report
            
        Returns:
            Tuple of (replay_valid, invalidation_reason)
        """
        # Critical drift invalidates replay
        if report.drift_severity == "critical":
            return False, "Critical semantic drift detected - replay may produce invalid results"
        
        # High drift with many adaptation type changes invalidates replay
        adaptation_type_drifts = report.drift_summary.get(SemanticDriftType.ADAPTATION_TYPE, 0)
        if report.drift_severity == "high" and adaptation_type_drifts > 5:
            return False, "High drift with frequent adaptation type changes - pedagogical consistency compromised"
        
        # Otherwise replay is valid
        return True, None
    
    def _compute_consistency_score(self, differences: List[SemanticDifference]) -> float:
        """
        Compute pedagogical consistency score.
        
        Args:
            differences: List of semantic differences
            
        Returns:
            Consistency score (0-1, higher = more consistent)
        """
        if not differences:
            return 1.0
        
        # Inverse of drift score
        drift_score = self._compute_drift_score(differences)
        return 1.0 - drift_score
