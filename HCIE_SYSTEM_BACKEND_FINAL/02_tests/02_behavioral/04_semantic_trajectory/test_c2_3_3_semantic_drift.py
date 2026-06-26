"""
C2.3.3 - Semantic Drift Analysis Tests

Tests for detecting semantic drift across policy versions.

Focus on pedagogical semantic trajectories (learning), NOT infrastructure replay.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.replay.semantic_drift import (
    SemanticDriftType,
    SemanticDifference,
    SemanticDriftReport,
    SemanticDriftAnalyzer
)
from core.replay.counterfactual_replay import (
    CounterfactualPolicy,
    CounterfactualReplayEngine
)
from core.replay.deterministic_replay_engine import (
    ReplayEventType,
    ReplayEvent,
    ReplayCognitionState,
    ReplayProjectionState
)


class TestSemanticDriftType:
    """Test SemanticDriftType enum."""
    
    def test_drift_type_values(self):
        """Test that drift type enum has expected values."""
        assert SemanticDriftType.READINESS_SEMANTICS.value == "readiness_semantics"
        assert SemanticDriftType.INTERVENTION_TIMING.value == "intervention_timing"
        assert SemanticDriftType.PEDAGOGICAL_NARRATIVE.value == "pedagogical_narrative"
        assert SemanticDriftType.PACING_SEMANTICS.value == "pacing_semantics"
        assert SemanticDriftType.ADAPTATION_TYPE.value == "adaptation_type"
        assert SemanticDriftType.RECOMMENDATION_SEMANTICS.value == "recommendation_semantics"


class TestSemanticDifference:
    """Test SemanticDifference dataclass."""
    
    def test_semantic_difference_creation(self):
        """Test creating semantic difference."""
        policy_a = "v1.0.0"
        policy_b = "v1.1.0"
        adaptation_a = ReplayEvent(
            event_id="event_001",
            event_type=ReplayEventType.ADAPTATION_GENERATED,
            user_id="user_001",
            timestamp=datetime.now(),
            causation_id="cognition_001",
            trace_id="trace_001",
            payload={
                "adaptation_type": "remediation",
                "recommendation": "Review basics",
                "policy_version": "v1.0.0",
                "concept_id": "binary_search",
                "timing_category": "middle",
                "deterministic_inputs_hash": "hash_001"
            },
            experiment_id=None,
            policy_version="v1.0.0",
            cohort_id=None,
            assignment_hash=None,
            policy_snapshot_id=None,
            schema_version="1.0.0"
        )
        adaptation_b = ReplayEvent(
            event_id="event_002",
            event_type=ReplayEventType.ADAPTATION_GENERATED,
            user_id="user_001",
            timestamp=datetime.now(),
            causation_id="cognition_001",
            trace_id="trace_001",
            payload={
                "adaptation_type": "difficulty_shift",
                "recommendation": "Increase challenge",
                "policy_version": "v1.1.0",
                "concept_id": "binary_search",
                "timing_category": "middle",
                "deterministic_inputs_hash": "hash_002"
            },
            experiment_id=None,
            policy_version="v1.1.0",
            cohort_id=None,
            assignment_hash=None,
            policy_snapshot_id=None,
            schema_version="1.0.0"
        )
        payload_a = adaptation_a.payload
        payload_b = adaptation_b.payload
        
        diff = SemanticDifference(
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
            concept_id="binary_search"
        )
        
        assert diff.drift_type == SemanticDriftType.ADAPTATION_TYPE
        assert diff.policy_a == "v1.0.0"
        assert diff.policy_b == "v1.1.0"
        assert diff.interpretation_a == "remediation"
        assert diff.interpretation_b == "difficulty_shift"
        assert diff.difference_magnitude == 0.8
        assert diff.impact_level == "high"


class TestSemanticDriftReport:
    """Test SemanticDriftReport dataclass."""
    
    def test_report_creation(self):
        """Test creating semantic drift report."""
        report = SemanticDriftReport(
            user_id="user_001",
            analysis_timestamp=datetime.now(),
            policies_compared=["v1.0.0", "v1.1.0"]
        )
        
        assert report.user_id == "user_001"
        assert len(report.policies_compared) == 2
        assert report.overall_drift_score == 0.0
        assert report.drift_severity == "none"
        assert report.replay_valid is True
        assert report.pedagogical_consistency_score == 1.0


class TestSemanticDriftAnalyzer:
    """Test SemanticDriftAnalyzer class."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        assert analyzer is not None
        assert analyzer._counterfactual_engine is not None
    
    def test_generate_policy_pairs(self):
        """Test generating policy pairs for comparison."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        policies = [
            CounterfactualPolicy.V1_0_0,
            CounterfactualPolicy.V1_1_0,
            CounterfactualPolicy.CONSERVATIVE_PACING
        ]
        
        pairs = analyzer._generate_policy_pairs(policies)
        
        assert len(pairs) == 3  # 3 choose 2
        assert (CounterfactualPolicy.V1_0_0, CounterfactualPolicy.V1_1_0) in pairs
        assert (CounterfactualPolicy.V1_0_0, CounterfactualPolicy.CONSERVATIVE_PACING) in pairs
        assert (CounterfactualPolicy.V1_1_0, CounterfactualPolicy.CONSERVATIVE_PACING) in pairs
    
    def test_generate_policy_pairs_single(self):
        """Test generating policy pairs with single policy."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        policies = [CounterfactualPolicy.V1_0_0]
        
        pairs = analyzer._generate_policy_pairs(policies)
        
        assert len(pairs) == 0
    
    def test_compare_adaptation_events_different_type(self):
        """Test comparing adaptation events with different types."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        adaptation_a = ReplayEvent(
            event_id="event_001",
            event_type=ReplayEventType.ADAPTATION_GENERATED,
            user_id="user_001",
            timestamp=datetime.now(),
            causation_id="cognition_001",
            trace_id="trace_001",
            payload={
                "adaptation_type": "remediation",
                "recommendation": "Review basics",
                "policy_version": "v1.0.0",
                "concept_id": "binary_search",
                "timing_category": "middle",
                "deterministic_inputs_hash": "hash_001"
            },
            experiment_id=None,
            policy_version="v1.0.0",
            cohort_id=None,
            assignment_hash=None,
            policy_snapshot_id=None,
            schema_version="1.0.0"
        )
        
        adaptation_b = ReplayEvent(
            event_id="event_002",
            event_type=ReplayEventType.ADAPTATION_GENERATED,
            user_id="user_001",
            timestamp=datetime.now(),
            causation_id="cognition_001",
            trace_id="trace_001",
            payload={
                "adaptation_type": "difficulty_shift",
                "recommendation": "Increase challenge",
                "policy_version": "v1.1.0",
                "concept_id": "binary_search",
                "timing_category": "middle",
                "deterministic_inputs_hash": "hash_002"
            },
            experiment_id=None,
            policy_version="v1.1.0",
            cohort_id=None,
            assignment_hash=None,
            policy_snapshot_id=None,
            schema_version="1.0.0"
        )
        
        diff = analyzer._compare_adaptation_events(
            adaptation_a,
            adaptation_b,
            "v1.0.0",
            "v1.1.0"
        )
        
        assert diff is not None
        assert diff.drift_type == SemanticDriftType.ADAPTATION_TYPE
        assert diff.policy_a == "v1.0.0"
        assert diff.policy_b == "v1.1.0"
        assert diff.interpretation_a == "remediation"
        assert diff.interpretation_b == "difficulty_shift"
        assert diff.difference_magnitude == 0.8
        assert diff.impact_level == "high"
    
    def test_compare_adaptation_events_same_type(self):
        """Test comparing adaptation events with same type."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        adaptation_a = ReplayEvent(
            event_id="event_001",
            event_type=ReplayEventType.ADAPTATION_GENERATED,
            user_id="user_001",
            timestamp=datetime.now(),
            causation_id="cognition_001",
            trace_id="trace_001",
            payload={
                "adaptation_type": "remediation",
                "recommendation": "Review basics",
                "policy_version": "v1.0.0",
                "concept_id": "binary_search",
                "timing_category": "middle",
                "deterministic_inputs_hash": "hash_001"
            },
            experiment_id=None,
            policy_version="v1.0.0",
            cohort_id=None,
            assignment_hash=None,
            policy_snapshot_id=None,
            schema_version="1.0.0"
        )
        
        adaptation_b = ReplayEvent(
            event_id="event_002",
            event_type=ReplayEventType.ADAPTATION_GENERATED,
            user_id="user_001",
            timestamp=datetime.now(),
            causation_id="cognition_001",
            trace_id="trace_001",
            payload={
                "adaptation_type": "remediation",
                "recommendation": "Review basics",
                "policy_version": "v1.1.0",
                "concept_id": "binary_search",
                "timing_category": "middle",
                "deterministic_inputs_hash": "hash_002"
            },
            experiment_id=None,
            policy_version="v1.1.0",
            cohort_id=None,
            assignment_hash=None,
            policy_snapshot_id=None,
            schema_version="1.0.0"
        )
        
        diff = analyzer._compare_adaptation_events(
            adaptation_a,
            adaptation_b,
            "v1.0.0",
            "v1.1.0"
        )
        
        assert diff is None
    
    def test_compare_adaptation_events_different_recommendation(self):
        """Test comparing adaptation events with different recommendations."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        adaptation_a = ReplayEvent(
            event_id="event_001",
            event_type=ReplayEventType.ADAPTATION_GENERATED,
            user_id="user_001",
            timestamp=datetime.now(),
            causation_id="cognition_001",
            trace_id="trace_001",
            payload={
                "adaptation_type": "remediation",
                "recommendation": "Review basics",
                "policy_version": "v1.0.0",
                "concept_id": "binary_search",
                "timing_category": "middle",
                "deterministic_inputs_hash": "hash_001"
            },
            experiment_id=None,
            policy_version="v1.0.0",
            cohort_id=None,
            assignment_hash=None,
            policy_snapshot_id=None,
            schema_version="1.0.0"
        )
        
        adaptation_b = ReplayEvent(
            event_id="event_002",
            event_type=ReplayEventType.ADAPTATION_GENERATED,
            user_id="user_001",
            timestamp=datetime.now(),
            causation_id="cognition_001",
            trace_id="trace_001",
            payload={
                "adaptation_type": "remediation",
                "recommendation": "Review advanced",
                "policy_version": "v1.1.0",
                "concept_id": "binary_search",
                "timing_category": "middle",
                "deterministic_inputs_hash": "hash_002"
            },
            experiment_id=None,
            policy_version="v1.1.0",
            cohort_id=None,
            assignment_hash=None,
            policy_snapshot_id=None,
            schema_version="1.0.0"
        )
        
        diff = analyzer._compare_adaptation_events(
            adaptation_a,
            adaptation_b,
            "v1.0.0",
            "v1.1.0"
        )
        
        assert diff is not None
        assert diff.drift_type == SemanticDriftType.RECOMMENDATION_SEMANTICS
        assert diff.interpretation_a == "Review basics"
        assert diff.interpretation_b == "Review advanced"
        assert diff.difference_magnitude == 0.5
        assert diff.impact_level == "medium"
    
    def test_compute_drift_score_no_differences(self):
        """Test computing drift score with no differences."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        score = analyzer._compute_drift_score([])
        
        assert score == 0.0
    
    def test_compute_drift_score_with_differences(self):
        """Test computing drift score with differences."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        adaptation_a = ReplayEvent(
            event_id="event_001",
            event_type=ReplayEventType.ADAPTATION_GENERATED,
            user_id="user_001",
            timestamp=datetime.now(),
            causation_id="cognition_001",
            trace_id="trace_001",
            payload={
                "adaptation_type": "remediation",
                "recommendation": "Review basics",
                "policy_version": "v1.0.0",
                "concept_id": "binary_search",
                "timing_category": "middle",
                "deterministic_inputs_hash": "hash_001"
            },
            experiment_id=None,
            policy_version="v1.0.0",
            cohort_id=None,
            assignment_hash=None,
            policy_snapshot_id=None,
            schema_version="1.0.0"
        )
        
        differences = [
            SemanticDifference(
                drift_type=SemanticDriftType.ADAPTATION_TYPE,
                policy_a="v1.0.0",
                policy_b="v1.1.0",
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
                interpretation_a="remediation",
                interpretation_b="difficulty_shift",
                difference_magnitude=0.8,
                impact_level="high",
                event_timestamp=adaptation_a.timestamp,
                concept_id="binary_search"
            ),
            SemanticDifference(
                drift_type=SemanticDriftType.RECOMMENDATION_SEMANTICS,
                policy_a="v1.0.0",
                policy_b="v1.1.0",
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
                interpretation_a="Review basics",
                interpretation_b="Review advanced",
                difference_magnitude=0.5,
                impact_level="medium",
                event_timestamp=datetime.now()
            )
        ]
        
        score = analyzer._compute_drift_score(differences)
        
        # (0.8 + 0.5) / 2 = 0.65
        assert abs(score - 0.65) < 0.01
    
    def test_assess_drift_severity(self):
        """Test assessing drift severity."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        assert analyzer._assess_drift_severity(0.0) == "none"
        assert analyzer._assess_drift_severity(0.1) == "low"
        assert analyzer._assess_drift_severity(0.3) == "medium"
        assert analyzer._assess_drift_severity(0.7) == "high"
        assert analyzer._assess_drift_severity(0.9) == "critical"
    
    def test_assess_replay_validity_no_drift(self):
        """Test assessing replay validity with no drift."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        report = SemanticDriftReport(
            user_id="user_001",
            analysis_timestamp=datetime.now(),
            policies_compared=["v1.0.0", "v1.1.0"],
            overall_drift_score=0.0,
            drift_severity="none"
        )
        
        is_valid, reason = analyzer._assess_replay_validity(report)
        
        assert is_valid is True
        assert reason is None
    
    def test_assess_replay_validity_critical_drift(self):
        """Test assessing replay validity with critical drift."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        report = SemanticDriftReport(
            user_id="user_001",
            analysis_timestamp=datetime.now(),
            policies_compared=["v1.0.0", "v1.1.0"],
            overall_drift_score=0.9,
            drift_severity="critical"
        )
        
        is_valid, reason = analyzer._assess_replay_validity(report)
        
        assert is_valid is False
        assert reason is not None
        assert "Critical semantic drift" in reason
    
    def test_assess_replay_validity_high_drift_with_adaptation_changes(self):
        """Test assessing replay validity with high drift and many adaptation changes."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        report = SemanticDriftReport(
            user_id="user_001",
            analysis_timestamp=datetime.now(),
            policies_compared=["v1.0.0", "v1.1.0"],
            overall_drift_score=0.7,
            drift_severity="high",
            drift_summary={SemanticDriftType.ADAPTATION_TYPE: 10}
        )
        
        is_valid, reason = analyzer._assess_replay_validity(report)
        
        assert is_valid is False
        assert reason is not None
        assert "adaptation type changes" in reason
    
    def test_assess_replay_validity_high_drift_without_adaptation_changes(self):
        """Test assessing replay validity with high drift but few adaptation changes."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        report = SemanticDriftReport(
            user_id="user_001",
            analysis_timestamp=datetime.now(),
            policies_compared=["v1.0.0", "v1.1.0"],
            overall_drift_score=0.7,
            drift_severity="high",
            drift_summary={SemanticDriftType.RECOMMENDATION_SEMANTICS: 3}
        )
        
        is_valid, reason = analyzer._assess_replay_validity(report)
        
        assert is_valid is True
        assert reason is None
    
    def test_compute_consistency_score_no_differences(self):
        """Test computing consistency score with no differences."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        score = analyzer._compute_consistency_score([])
        
        assert score == 1.0
    
    def test_compute_consistency_score_with_differences(self):
        """Test computing consistency score with differences."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        differences = [
            SemanticDifference(
                drift_type=SemanticDriftType.ADAPTATION_TYPE,
                policy_a="v1.0.0",
                policy_b="v1.1.0",
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
                interpretation_a="remediation",
                interpretation_b="difficulty_shift",
                difference_magnitude=0.8,
                impact_level="high",
                event_timestamp=datetime.now()
            )
        ]
        
        score = analyzer._compute_consistency_score(differences)
        
        # 1.0 - 0.8 = 0.2
        assert abs(score - 0.2) < 0.01
    
    def test_analyze_semantic_drift_empty_events(self):
        """Test analyzing semantic drift with empty event stream."""
        engine = CounterfactualReplayEngine()
        analyzer = SemanticDriftAnalyzer(engine)
        
        policies = [CounterfactualPolicy.V1_0_0, CounterfactualPolicy.V1_1_0]
        
        report = analyzer.analyze_semantic_drift(
            user_id="user_001",
            events=[],
            policies=policies
        )
        
        assert report.user_id == "user_001"
        assert len(report.policies_compared) == 2
        assert report.overall_drift_score == 0.0
        assert report.drift_severity == "none"
        assert report.replay_valid is True
        assert report.pedagogical_consistency_score == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
