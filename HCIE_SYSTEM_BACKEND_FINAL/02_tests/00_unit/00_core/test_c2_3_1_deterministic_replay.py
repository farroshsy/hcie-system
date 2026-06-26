"""
C2.3.1 - Deterministic Canonical Replay Engine Tests

Tests for deterministic pedagogical replay, semantic reconstruction, and counterfactual simulation.

Focus on pedagogical replay (NOT debugging replay, log replay, or infrastructure replay).
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.replay.deterministic_replay_engine import (
    ReplayEventType,
    ReplayEvent,
    ReplayCognitionState,
    ReplayProjectionState,
    ReplayAdaptationState,
    ReplayContext,
    ReplayResult,
    DeterministicReplayEngine
)


class TestReplayEventType:
    """Test ReplayEventType enum."""
    
    def test_event_type_values(self):
        """Test that event type enum has expected values."""
        assert ReplayEventType.TASK_ATTEMPT_SUBMITTED.value == "TaskAttemptSubmitted"
        assert ReplayEventType.COGNITION_UPDATED.value == "CognitionUpdated"
        assert ReplayEventType.ADAPTATION_GENERATED.value == "AdaptationGenerated"
        assert ReplayEventType.PROJECTION_UPDATED.value == "ProjectionUpdated"


class TestReplayEvent:
    """Test ReplayEvent dataclass."""
    
    def test_replay_event_creation(self):
        """Test creating a replay event."""
        event = ReplayEvent(
            event_id="event_001",
            event_type=ReplayEventType.COGNITION_UPDATED,
            user_id="user_001",
            timestamp=datetime.now(),
            causation_id="causation_001",
            trace_id="trace_001",
            payload={"mastery": 0.5, "uncertainty": 0.3},
            experiment_id="experiment_001",
            policy_version="v1.0.0",
            cohort_id="cohort_001",
            assignment_hash="hash_001",
            policy_snapshot_id="snapshot_001",
            schema_version="1.0.0"
        )
        
        assert event.event_id == "event_001"
        assert event.event_type == ReplayEventType.COGNITION_UPDATED
        assert event.user_id == "user_001"
        assert event.policy_version == "v1.0.0"


class TestReplayCognitionState:
    """Test ReplayCognitionState dataclass."""
    
    def test_cognition_state_creation(self):
        """Test creating cognition state."""
        state = ReplayCognitionState(
            mastery=0.5,
            uncertainty=0.3,
            zpd_score=0.4,
            bayesian_alpha=5.0,
            bayesian_beta=5.0,
            kalman_mastery=0.5,
            kalman_covariance=0.1,
            lyapunov_mastery=0.5
        )
        
        assert state.mastery == 0.5
        assert state.uncertainty == 0.3
        assert state.zpd_score == 0.4
    
    def test_cognition_state_hash(self):
        """Test cognition state hash computation."""
        state = ReplayCognitionState(
            mastery=0.5,
            uncertainty=0.3,
            zpd_score=0.4,
            bayesian_alpha=5.0,
            bayesian_beta=5.0,
            kalman_mastery=0.5,
            kalman_covariance=0.1,
            lyapunov_mastery=0.5
        )
        
        hash1 = state.compute_hash()
        hash2 = state.compute_hash()
        
        # Hash should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 16  # SHA256 truncated to 16 chars
    
    def test_cognition_state_hash_with_concepts(self):
        """Test hash computation with concept mastery."""
        state = ReplayCognitionState(
            mastery=0.5,
            uncertainty=0.3,
            zpd_score=0.4,
            bayesian_alpha=5.0,
            bayesian_beta=5.0,
            kalman_mastery=0.5,
            kalman_covariance=0.1,
            lyapunov_mastery=0.5,
            concept_mastery={"binary_search": 0.7, "sorting": 0.3}
        )
        
        hash1 = state.compute_hash()
        
        # Hash should include concept mastery
        assert hash1 is not None
        assert len(hash1) == 16


class TestReplayProjectionState:
    """Test ReplayProjectionState dataclass."""
    
    def test_projection_state_creation(self):
        """Test creating projection state."""
        state = ReplayProjectionState(
            readiness=0.7,
            confidence_stability=0.8,
            challenge_suitability=0.6,
            pacing_responsiveness=0.5,
            cognitive_stability=0.7,
            transfer_readiness=0.4,
            learning_momentum=0.6,
            uncertainty_band=0.3
        )
        
        assert state.readiness == 0.7
        assert state.confidence_stability == 0.8
    
    def test_projection_state_hash(self):
        """Test projection state hash computation."""
        state = ReplayProjectionState(
            readiness=0.7,
            confidence_stability=0.8,
            challenge_suitability=0.6,
            pacing_responsiveness=0.5,
            cognitive_stability=0.7,
            transfer_readiness=0.4,
            learning_momentum=0.6,
            uncertainty_band=0.3
        )
        
        hash1 = state.compute_hash()
        hash2 = state.compute_hash()
        
        # Hash should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 16
    
    def test_projection_state_hash_with_adaptation(self):
        """Test hash computation with adaptation enrichment."""
        state = ReplayProjectionState(
            readiness=0.7,
            confidence_stability=0.8,
            challenge_suitability=0.6,
            pacing_responsiveness=0.5,
            cognitive_stability=0.7,
            transfer_readiness=0.4,
            learning_momentum=0.6,
            uncertainty_band=0.3,
            adaptation_type="remediation",
            adaptation_recommendation="Review binary search basics"
        )
        
        hash1 = state.compute_hash()
        
        # Hash should include adaptation
        assert hash1 is not None
        assert len(hash1) == 16


class TestReplayAdaptationState:
    """Test ReplayAdaptationState dataclass."""
    
    def test_adaptation_state_creation(self):
        """Test creating adaptation state."""
        state = ReplayAdaptationState(
            adaptation_type="remediation",
            recommendation="Review binary search basics",
            policy_version="v1.0.0",
            target_concept_id="binary_search",
            timing_category="middle",
            deterministic_inputs_hash="hash_001"
        )
        
        assert state.adaptation_type == "remediation"
        assert state.policy_version == "v1.0.0"
    
    def test_adaptation_state_hash(self):
        """Test adaptation state hash computation."""
        state = ReplayAdaptationState(
            adaptation_type="remediation",
            recommendation="Review binary search basics",
            policy_version="v1.0.0",
            target_concept_id="binary_search",
            timing_category="middle",
            deterministic_inputs_hash="hash_001"
        )
        
        hash1 = state.compute_hash()
        hash2 = state.compute_hash()
        
        # Hash should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 16


class TestDeterministicReplayEngine:
    """Test DeterministicReplayEngine class."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = DeterministicReplayEngine()
        
        assert engine is not None
        assert engine._policy_snapshot_repository is None
    
    def test_replay_empty_events(self):
        """Test replay with no events."""
        engine = DeterministicReplayEngine()
        
        result = engine.replay_learner_trajectory(
            user_id="user_001",
            events=[]
        )
        
        assert result.user_id == "user_001"
        assert result.total_events_processed == 0
        assert result.determinism_valid is True
    
    def test_replay_single_cognition_event(self):
        """Test replay with single cognition update event."""
        engine = DeterministicReplayEngine()
        
        events = [
            ReplayEvent(
                event_id="event_001",
                event_type=ReplayEventType.COGNITION_UPDATED,
                user_id="user_001",
                timestamp=datetime.now(),
                causation_id="causation_001",
                trace_id="trace_001",
                payload={
                    "mastery": 0.5,
                    "uncertainty": 0.3,
                    "zpd_score": 0.4,
                    "bayesian_alpha": 5.0,
                    "bayesian_beta": 5.0,
                    "kalman_mastery": 0.5,
                    "kalman_covariance": 0.1,
                    "lyapunov_mastery": 0.5
                },
                experiment_id=None,
                policy_version=None,
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            )
        ]
        
        result = engine.replay_learner_trajectory(
            user_id="user_001",
            events=events
        )
        
        assert result.total_events_processed == 1
        assert result.final_cognition.mastery == 0.5
        assert result.final_cognition.uncertainty == 0.3
        assert result.final_cognition.zpd_score == 0.4
    
    def test_replay_multiple_cognition_events(self):
        """Test replay with multiple cognition updates."""
        engine = DeterministicReplayEngine()
        
        events = [
            ReplayEvent(
                event_id=f"event_{i}",
                event_type=ReplayEventType.COGNITION_UPDATED,
                user_id="user_001",
                timestamp=datetime.now() + timedelta(seconds=i),
                causation_id=f"causation_{i}",
                trace_id="trace_001",
                payload={
                    "mastery": 0.1 + (i * 0.1),
                    "uncertainty": 0.9 - (i * 0.1),
                    "zpd_score": 0.1 + (i * 0.1),
                    "bayesian_alpha": 1.0 + (i * 1.0),
                    "bayesian_beta": 1.0 + (i * 1.0),
                    "kalman_mastery": 0.1 + (i * 0.1),
                    "kalman_covariance": 1.0 - (i * 0.1),
                    "lyapunov_mastery": 0.1 + (i * 0.1)
                },
                experiment_id=None,
                policy_version=None,
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            )
            for i in range(5)
        ]
        
        result = engine.replay_learner_trajectory(
            user_id="user_001",
            events=events
        )
        
        assert result.total_events_processed == 5
        # Final state should be from last event
        assert abs(result.final_cognition.mastery - 0.5) < 0.001
        assert abs(result.final_cognition.uncertainty - 0.5) < 0.001
    
    def test_replay_with_projection_event(self):
        """Test replay with projection update event."""
        engine = DeterministicReplayEngine()
        
        events = [
            ReplayEvent(
                event_id="event_001",
                event_type=ReplayEventType.COGNITION_UPDATED,
                user_id="user_001",
                timestamp=datetime.now(),
                causation_id="causation_001",
                trace_id="trace_001",
                payload={
                    "mastery": 0.5,
                    "uncertainty": 0.3,
                    "zpd_score": 0.4,
                    "bayesian_alpha": 5.0,
                    "bayesian_beta": 5.0,
                    "kalman_mastery": 0.5,
                    "kalman_covariance": 0.1,
                    "lyapunov_mastery": 0.5
                },
                experiment_id=None,
                policy_version=None,
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            ),
            ReplayEvent(
                event_id="event_002",
                event_type=ReplayEventType.PROJECTION_UPDATED,
                user_id="user_001",
                timestamp=datetime.now() + timedelta(seconds=1),
                causation_id="event_001",
                trace_id="trace_001",
                payload={
                    "ux_semantics": {
                        "readiness": 0.7,
                        "confidence_stability": 0.8,
                        "challenge_suitability": 0.6,
                        "pacing_responsiveness": 0.5,
                        "cognitive_stability": 0.7,
                        "transfer_readiness": 0.4,
                        "learning_momentum": 0.6,
                        "uncertainty_band": 0.3
                    },
                    "adaptation": {
                        "adaptation_type": "remediation",
                        "recommendation": "Review basics"
                    }
                },
                experiment_id=None,
                policy_version=None,
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            )
        ]
        
        result = engine.replay_learner_trajectory(
            user_id="user_001",
            events=events
        )
        
        assert result.total_events_processed == 2
        assert result.final_projection.readiness == 0.7
        assert result.final_projection.adaptation_type == "remediation"
    
    def test_replay_with_adaptation_event(self):
        """Test replay with adaptation generation event."""
        engine = DeterministicReplayEngine()
        
        events = [
            ReplayEvent(
                event_id="event_001",
                event_type=ReplayEventType.ADAPTATION_GENERATED,
                user_id="user_001",
                timestamp=datetime.now(),
                causation_id="cognition_001",
                trace_id="trace_001",
                payload={
                    "adaptation_type": "remediation",
                    "recommendation": "Review binary search basics",
                    "policy_version": "v1.0.0",
                    "concept_id": "binary_search",
                    "timing_category": "middle",
                    "deterministic_inputs_hash": "hash_001"
                },
                experiment_id="experiment_001",
                policy_version="v1.0.0",
                cohort_id="cohort_001",
                assignment_hash="hash_001",
                policy_snapshot_id="snapshot_001",
                schema_version="1.0.0"
            )
        ]
        
        result = engine.replay_learner_trajectory(
            user_id="user_001",
            events=events
        )
        
        assert result.total_events_processed == 1
        assert result.final_adaptation is not None
        assert result.final_adaptation.adaptation_type == "remediation"
        assert result.final_adaptation.policy_version == "v1.0.0"
    
    def test_replay_with_full_event_sequence(self):
        """Test replay with complete event sequence."""
        engine = DeterministicReplayEngine()
        
        events = [
            ReplayEvent(
                event_id="event_001",
                event_type=ReplayEventType.TASK_ATTEMPT_SUBMITTED,
                user_id="user_001",
                timestamp=datetime.now(),
                causation_id=None,
                trace_id="trace_001",
                payload={"concept_id": "binary_search", "is_correct": True},
                experiment_id="experiment_001",
                policy_version="v1.0.0",
                cohort_id="cohort_001",
                assignment_hash="hash_001",
                policy_snapshot_id=None,
                schema_version="1.0.0"
            ),
            ReplayEvent(
                event_id="event_002",
                event_type=ReplayEventType.COGNITION_UPDATED,
                user_id="user_001",
                timestamp=datetime.now() + timedelta(seconds=1),
                causation_id="event_001",
                trace_id="trace_001",
                payload={
                    "mastery": 0.5,
                    "uncertainty": 0.3,
                    "zpd_score": 0.4,
                    "bayesian_alpha": 5.0,
                    "bayesian_beta": 5.0,
                    "kalman_mastery": 0.5,
                    "kalman_covariance": 0.1,
                    "lyapunov_mastery": 0.5
                },
                experiment_id="experiment_001",
                policy_version="v1.0.0",
                cohort_id="cohort_001",
                assignment_hash="hash_001",
                policy_snapshot_id=None,
                schema_version="1.0.0"
            ),
            ReplayEvent(
                event_id="event_003",
                event_type=ReplayEventType.ADAPTATION_GENERATED,
                user_id="user_001",
                timestamp=datetime.now() + timedelta(seconds=2),
                causation_id="event_002",
                trace_id="trace_001",
                payload={
                    "adaptation_type": "remediation",
                    "recommendation": "Review basics",
                    "policy_version": "v1.0.0",
                    "concept_id": "binary_search",
                    "timing_category": "middle",
                    "deterministic_inputs_hash": "hash_002"
                },
                experiment_id="experiment_001",
                policy_version="v1.0.0",
                cohort_id="cohort_001",
                assignment_hash="hash_001",
                policy_snapshot_id="snapshot_001",
                schema_version="1.0.0"
            ),
            ReplayEvent(
                event_id="event_004",
                event_type=ReplayEventType.PROJECTION_UPDATED,
                user_id="user_001",
                timestamp=datetime.now() + timedelta(seconds=3),
                causation_id="event_003",
                trace_id="trace_001",
                payload={
                    "ux_semantics": {
                        "readiness": 0.7,
                        "confidence_stability": 0.8,
                        "challenge_suitability": 0.6,
                        "pacing_responsiveness": 0.5,
                        "cognitive_stability": 0.7,
                        "transfer_readiness": 0.4,
                        "learning_momentum": 0.6,
                        "uncertainty_band": 0.3
                    },
                    "adaptation": {
                        "adaptation_type": "remediation",
                        "recommendation": "Review basics"
                    }
                },
                experiment_id="experiment_001",
                policy_version="v1.0.0",
                cohort_id="cohort_001",
                assignment_hash="hash_001",
                policy_snapshot_id=None,
                schema_version="1.0.0"
            )
        ]
        
        result = engine.replay_learner_trajectory(
            user_id="user_001",
            events=events
        )
        
        assert result.total_events_processed == 4
        assert result.final_cognition.mastery == 0.5
        assert result.final_adaptation.adaptation_type == "remediation"
        assert result.final_projection.readiness == 0.7
    
    def test_replay_with_initial_cognition(self):
        """Test replay with custom initial cognition state."""
        engine = DeterministicReplayEngine()
        
        initial_cognition = ReplayCognitionState(
            mastery=0.3,
            uncertainty=0.4,
            zpd_score=0.2,
            bayesian_alpha=3.0,
            bayesian_beta=7.0,
            kalman_mastery=0.3,
            kalman_covariance=0.2,
            lyapunov_mastery=0.3
        )
        
        events = [
            ReplayEvent(
                event_id="event_001",
                event_type=ReplayEventType.COGNITION_UPDATED,
                user_id="user_001",
                timestamp=datetime.now(),
                causation_id="causation_001",
                trace_id="trace_001",
                payload={
                    "mastery": 0.5,
                    "uncertainty": 0.3,
                    "zpd_score": 0.4,
                    "bayesian_alpha": 5.0,
                    "bayesian_beta": 5.0,
                    "kalman_mastery": 0.5,
                    "kalman_covariance": 0.1,
                    "lyapunov_mastery": 0.5
                },
                experiment_id=None,
                policy_version=None,
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            )
        ]
        
        result = engine.replay_learner_trajectory(
            user_id="user_001",
            events=events,
            initial_cognition=initial_cognition
        )
        
        # Final state should be from event, not initial
        assert result.final_cognition.mastery == 0.5
        assert result.final_cognition.mastery != initial_cognition.mastery
    
    def test_replay_determinism_validation(self):
        """Test replay determinism validation against original state."""
        engine = DeterministicReplayEngine()
        
        events = [
            ReplayEvent(
                event_id="event_001",
                event_type=ReplayEventType.COGNITION_UPDATED,
                user_id="user_001",
                timestamp=datetime.now(),
                causation_id="causation_001",
                trace_id="trace_001",
                payload={
                    "mastery": 0.5,
                    "uncertainty": 0.3,
                    "zpd_score": 0.4,
                    "bayesian_alpha": 5.0,
                    "bayesian_beta": 5.0,
                    "kalman_mastery": 0.5,
                    "kalman_covariance": 0.1,
                    "lyapunov_mastery": 0.5
                },
                experiment_id=None,
                policy_version=None,
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            ),
            ReplayEvent(
                event_id="event_002",
                event_type=ReplayEventType.PROJECTION_UPDATED,
                user_id="user_001",
                timestamp=datetime.now() + timedelta(seconds=1),
                causation_id="event_001",
                trace_id="trace_001",
                payload={
                    "ux_semantics": {
                        "readiness": 0.7,
                        "confidence_stability": 0.8,
                        "challenge_suitability": 0.6,
                        "pacing_responsiveness": 0.5,
                        "cognitive_stability": 0.7,
                        "transfer_readiness": 0.4,
                        "learning_momentum": 0.6,
                        "uncertainty_band": 0.3
                    },
                    "adaptation": {
                        "adaptation_type": None,
                        "recommendation": None
                    }
                },
                experiment_id=None,
                policy_version=None,
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            )
        ]
        
        result = engine.replay_learner_trajectory(
            user_id="user_001",
            events=events
        )
        
        # Create original state matching replay
        original_cognition = ReplayCognitionState(
            mastery=0.5,
            uncertainty=0.3,
            zpd_score=0.4,
            bayesian_alpha=5.0,
            bayesian_beta=5.0,
            kalman_mastery=0.5,
            kalman_covariance=0.1,
            lyapunov_mastery=0.5
        )
        original_cognition.compute_hash()
        
        original_projection = ReplayProjectionState(
            readiness=0.7,
            confidence_stability=0.8,
            challenge_suitability=0.6,
            pacing_responsiveness=0.5,
            cognitive_stability=0.7,
            transfer_readiness=0.4,
            learning_momentum=0.6,
            uncertainty_band=0.3
        )
        original_projection.compute_hash()
        
        is_valid = engine.validate_replay_determinism(
            replay_result=result,
            original_cognition=original_cognition,
            original_projection=original_projection
        )
        
        assert is_valid is True
        assert result.determinism_valid is True
    
    def test_replay_determinism_validation_failure(self):
        """Test replay determinism validation with mismatched state."""
        engine = DeterministicReplayEngine()
        
        events = [
            ReplayEvent(
                event_id="event_001",
                event_type=ReplayEventType.COGNITION_UPDATED,
                user_id="user_001",
                timestamp=datetime.now(),
                causation_id="causation_001",
                trace_id="trace_001",
                payload={
                    "mastery": 0.5,
                    "uncertainty": 0.3,
                    "zpd_score": 0.4,
                    "bayesian_alpha": 5.0,
                    "bayesian_beta": 5.0,
                    "kalman_mastery": 0.5,
                    "kalman_covariance": 0.1,
                    "lyapunov_mastery": 0.5
                },
                experiment_id=None,
                policy_version=None,
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            )
        ]
        
        result = engine.replay_learner_trajectory(
            user_id="user_001",
            events=events
        )
        
        # Create original state NOT matching replay
        original_cognition = ReplayCognitionState(
            mastery=0.6,  # Different from replay
            uncertainty=0.3,
            zpd_score=0.4,
            bayesian_alpha=5.0,
            bayesian_beta=5.0,
            kalman_mastery=0.5,
            kalman_covariance=0.1,
            lyapunov_mastery=0.5
        )
        original_cognition.compute_hash()
        
        original_projection = ReplayProjectionState(
            readiness=0.5,
            confidence_stability=0.5,
            challenge_suitability=0.5,
            pacing_responsiveness=0.5,
            cognitive_stability=0.5,
            transfer_readiness=0.5,
            learning_momentum=0.5,
            uncertainty_band=0.5
        )
        original_projection.compute_hash()
        
        is_valid = engine.validate_replay_determinism(
            replay_result=result,
            original_cognition=original_cognition,
            original_projection=original_projection
        )
        
        assert is_valid is False
        assert result.determinism_valid is False
        assert len(result.validation_errors) > 0
    
    def test_replay_with_concept_mastery(self):
        """Test replay with per-concept mastery updates."""
        engine = DeterministicReplayEngine()
        
        events = [
            ReplayEvent(
                event_id="event_001",
                event_type=ReplayEventType.COGNITION_UPDATED,
                user_id="user_001",
                timestamp=datetime.now(),
                causation_id="causation_001",
                trace_id="trace_001",
                payload={
                    "mastery": 0.5,
                    "uncertainty": 0.3,
                    "zpd_score": 0.4,
                    "bayesian_alpha": 5.0,
                    "bayesian_beta": 5.0,
                    "kalman_mastery": 0.5,
                    "kalman_covariance": 0.1,
                    "lyapunov_mastery": 0.5,
                    "concept_mastery": {
                        "binary_search": 0.7,
                        "sorting": 0.3,
                        "linked_list": 0.5
                    }
                },
                experiment_id=None,
                policy_version=None,
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            )
        ]
        
        result = engine.replay_learner_trajectory(
            user_id="user_001",
            events=events
        )
        
        assert result.total_events_processed == 1
        assert "binary_search" in result.final_cognition.concept_mastery
        assert result.final_cognition.concept_mastery["binary_search"] == 0.7
        assert result.final_cognition.concept_mastery["sorting"] == 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
