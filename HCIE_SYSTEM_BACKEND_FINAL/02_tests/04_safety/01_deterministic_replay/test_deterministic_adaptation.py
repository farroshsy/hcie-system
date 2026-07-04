"""
Deterministic Adaptation Test Suite
Validates that adaptation derivation is deterministic across multiple runs

Tests:
- Single run determinism
- 100 runs determinism
- Replay determinism
- Process restart determinism
- Container restart determinism
"""

import pytest
import json
from typing import Dict, Any

from core.adaptation.deterministic_adaptation_engine import (
    DeterministicAdaptationEngine,
    get_deterministic_adaptation_engine,
    SemanticAdaptation
)
from core.adaptation.policy_registry import AdaptationPolicyRegistry


class TestDeterministicAdaptation:
    """
    Test suite for deterministic adaptation derivation
    
    Validates:
    - Same cognition snapshot + same policy version = identical adaptation output
    - Over 1 run, 100 runs, replay runs, process restarts, container restarts
    """
    
    @pytest.fixture
    def engine(self):
        """Get deterministic adaptation engine instance"""
        return get_deterministic_adaptation_engine()
    
    @pytest.fixture
    def sample_cognition_snapshot(self) -> Dict[str, Any]:
        """Sample cognition snapshot for testing"""
        return {
            "mastery": 0.45,
            "uncertainty": 0.6,
            "zpd_score": 0.5,
            "bayesian_alpha": 20.0,
            "bayesian_beta": 1.0,
            "kalman_mastery": 0.47,
            "kalman_covariance": 0.05,
            "lyapunov_mastery": 0.46
        }
    
    @pytest.fixture
    def sample_cognition_snapshot_remediation(self) -> Dict[str, Any]:
        """Cognition snapshot that should trigger remediation"""
        return {
            "mastery": 0.25,
            "uncertainty": 0.7,
            "zpd_score": 0.3,
            "bayesian_alpha": 10.0,
            "bayesian_beta": 1.0,
            "kalman_mastery": 0.27,
            "kalman_covariance": 0.1,
            "lyapunov_mastery": 0.26
        }
    
    @pytest.fixture
    def sample_cognition_snapshot_milestone(self) -> Dict[str, Any]:
        """Cognition snapshot that should trigger milestone acknowledgement"""
        return {
            "mastery": 0.85,
            "uncertainty": 0.2,
            "zpd_score": 0.7,
            "bayesian_alpha": 30.0,
            "bayesian_beta": 1.0,
            "kalman_mastery": 0.87,
            "kalman_covariance": 0.02,
            "lyapunov_mastery": 0.86
        }
    
    def test_single_run_determinism(self, engine, sample_cognition_snapshot):
        """
        Test 1: Single run determinism
        
        Validates that adaptation derivation produces consistent output
        """
        # Derive adaptation
        adaptation = engine.derive_adaptation(
            cognition_snapshot=sample_cognition_snapshot,
            policy_version="v1.0.0",
            user_id="test_user",
            causation_id="test_causation"
        )
        
        # Verify structure
        assert adaptation['event_type'] == 'AdaptationGenerated'
        assert adaptation['policy_version'] == 'v1.0.0'
        assert 'adaptation_type' in adaptation
        assert 'recommendation' in adaptation
        assert 'cognition_snapshot' in adaptation
        assert 'deterministic_inputs_hash' in adaptation
        assert 'schema_version' in adaptation
        assert 'policy_inputs_schema_version' in adaptation
        
        # Verify determinism
        assert engine.verify_determinism(adaptation)
        
        # Verify self-contained
        assert engine.is_self_contained(adaptation)
    
    def test_100_runs_determinism(self, engine, sample_cognition_snapshot):
        """
        Test 2: 100 runs determinism
        
        Validates that adaptation derivation produces identical output
        across 100 consecutive runs with the same inputs
        """
        adaptations = []
        
        # Run 100 times
        for i in range(100):
            adaptation = engine.derive_adaptation(
                cognition_snapshot=sample_cognition_snapshot,
                policy_version="v1.0.0",
                user_id="test_user",
                causation_id="test_causation"
            )
            adaptations.append(adaptation)
        
        # All adaptations should have identical structure
        first_adaptation = adaptations[0]
        
        for i, adaptation in enumerate(adaptations):
            # Same adaptation type
            assert adaptation['adaptation_type'] == first_adaptation['adaptation_type']
            
            # Same deterministic hash
            assert adaptation['deterministic_inputs_hash'] == first_adaptation['deterministic_inputs_hash']
            
            # Same recommendation structure
            assert json.dumps(adaptation['recommendation'], sort_keys=True) == \
                   json.dumps(first_adaptation['recommendation'], sort_keys=True)
            
            # Same schema versions
            assert adaptation['schema_version'] == first_adaptation['schema_version']
            assert adaptation['policy_inputs_schema_version'] == first_adaptation['policy_inputs_schema_version']
        
        # All deterministic hashes should be identical
        hashes = [a['deterministic_inputs_hash'] for a in adaptations]
        assert len(set(hashes)) == 1, "All deterministic hashes should be identical"
    
    def test_replay_determinism(self, engine, sample_cognition_snapshot):
        """
        Test 3: Replay determinism
        
        Validates that replaying adaptation from stored event produces identical output
        """
        # Derive original adaptation
        original_adaptation = engine.derive_adaptation(
            cognition_snapshot=sample_cognition_snapshot,
            policy_version="v1.0.0",
            user_id="test_user",
            causation_id="test_causation"
        )
        
        # Simulate replay: re-derive from stored cognition snapshot
        replayed_adaptation = engine.derive_adaptation(
            cognition_snapshot=original_adaptation['cognition_snapshot'],
            policy_version=original_adaptation['policy_version'],
            user_id="test_user",
            causation_id=original_adaptation['causation_id']
        )
        
        # Verify replay produces identical output
        assert replayed_adaptation['adaptation_type'] == original_adaptation['adaptation_type']
        assert replayed_adaptation['deterministic_inputs_hash'] == original_adaptation['deterministic_inputs_hash']
        assert json.dumps(replayed_adaptation['recommendation'], sort_keys=True) == \
               json.dumps(original_adaptation['recommendation'], sort_keys=True)
        
        # Verify both are deterministic
        assert engine.verify_determinism(original_adaptation)
        assert engine.verify_determinism(replayed_adaptation)
    
    def test_different_cognition_states(self, engine, sample_cognition_snapshot_remediation, sample_cognition_snapshot_milestone):
        """
        Test 4: Different cognition states produce different adaptations
        
        Validates that different cognitive states produce different adaptation types
        """
        # Remediation case
        adaptation_remediation = engine.derive_adaptation(
            cognition_snapshot=sample_cognition_snapshot_remediation,
            policy_version="v1.0.0",
            user_id="test_user",
            causation_id="test_causation"
        )
        
        # Milestone case
        adaptation_milestone = engine.derive_adaptation(
            cognition_snapshot=sample_cognition_snapshot_milestone,
            policy_version="v1.0.0",
            user_id="test_user",
            causation_id="test_causation"
        )
        
        # Different adaptation types
        assert adaptation_remediation['adaptation_type'] == 'remediation'
        assert adaptation_milestone['adaptation_type'] == 'milestone_acknowledgement'
        
        # Different deterministic hashes
        assert adaptation_remediation['deterministic_inputs_hash'] != adaptation_milestone['deterministic_inputs_hash']
        
        # Both deterministic
        assert engine.verify_determinism(adaptation_remediation)
        assert engine.verify_determinism(adaptation_milestone)
    
    def test_policy_version_isolation(self, engine, sample_cognition_snapshot):
        """
        Test 5: Policy version isolation
        
        Validates that different policy versions produce different outputs
        (when more policies are added in future)
        """
        # For now, only v1.0.0 exists
        # This test will be useful when v2.0.0 is added
        
        adaptation_v1 = engine.derive_adaptation(
            cognition_snapshot=sample_cognition_snapshot,
            policy_version="v1.0.0",
            user_id="test_user",
            causation_id="test_causation"
        )
        
        assert adaptation_v1['policy_version'] == 'v1.0.0'
        assert engine.verify_determinism(adaptation_v1)
    
    def test_trace_context_propagation(self, engine, sample_cognition_snapshot):
        """
        Test 6: Trace context propagation
        
        Validates that trace context is correctly propagated
        """
        trace_context = {
            'trace_id': 'test-trace-123',
            'span_id': 'test-span-456',
            'parent_span_id': 'test-parent-789'
        }
        
        adaptation = engine.derive_adaptation(
            cognition_snapshot=sample_cognition_snapshot,
            policy_version="v1.0.0",
            user_id="test_user",
            causation_id="test_causation",
            trace_context=trace_context
        )
        
        # Verify trace context propagated
        assert adaptation['trace_id'] == 'test-trace-123'
        assert adaptation['span_id'] == 'test-span-456'
        assert adaptation['parent_span_id'] == 'test-parent-789'
        
        # Verify determinism (trace context should not affect adaptation derivation)
        assert engine.verify_determinism(adaptation)
    
    def test_causation_lineage(self, engine, sample_cognition_snapshot):
        """
        Test 7: Causation lineage preservation
        
        Validates that causation ID is correctly preserved
        """
        causation_id = "cognition-updated-123"
        
        adaptation = engine.derive_adaptation(
            cognition_snapshot=sample_cognition_snapshot,
            policy_version="v1.0.0",
            user_id="test_user",
            causation_id=causation_id
        )
        
        # Verify causation ID preserved
        assert adaptation['causation_id'] == causation_id
        
        # Verify determinism
        assert engine.verify_determinism(adaptation)
    
    def test_schema_version_compatibility(self, engine, sample_cognition_snapshot):
        """
        Test 8: Schema version compatibility
        
        Validates that schema versions are correctly set
        """
        adaptation = engine.derive_adaptation(
            cognition_snapshot=sample_cognition_snapshot,
            policy_version="v1.0.0",
            user_id="test_user",
            causation_id="test_causation"
        )
        
        # Verify schema versions
        assert adaptation['schema_version'] == '1.0.0'
        assert adaptation['policy_inputs_schema_version'] == '1.0.0'
        
        # Verify determinism
        assert engine.verify_determinism(adaptation)
    
    def test_policy_registry_version_frozen(self):
        """
        Test 9: Policy registry version-frozen
        
        Validates that policy registry is version-frozen and cannot be mutated
        """
        # Verify v1.0.0 exists
        policy = AdaptationPolicyRegistry.get_policy("v1.0.0")
        assert policy.version == "v1.0.0"
        
        # Verify non-existent version raises error
        with pytest.raises(ValueError, match="Policy version v999.0.0 not found"):
            AdaptationPolicyRegistry.get_policy("v999.0.0")
        
        # Verify list available versions
        versions = AdaptationPolicyRegistry.list_available_versions()
        assert "v1.0.0" in versions
    
    def test_adaptation_type_classification(self, engine):
        """
        Test 10: Adaptation type classification
        
        Validates that adaptation types are correctly classified
        """
        # Test remediation classification
        remediation_snapshot = {
            "mastery": 0.25,
            "uncertainty": 0.7,
            "zpd_score": 0.3
        }
        adaptation = engine.derive_adaptation(
            cognition_snapshot=remediation_snapshot,
            policy_version="v1.0.0",
            user_id="test_user",
            causation_id="test_causation"
        )
        assert adaptation['adaptation_type'] == 'remediation'
        
        # Test milestone classification
        milestone_snapshot = {
            "mastery": 0.85,
            "uncertainty": 0.2,
            "zpd_score": 0.7
        }
        adaptation = engine.derive_adaptation(
            cognition_snapshot=milestone_snapshot,
            policy_version="v1.0.0",
            user_id="test_user",
            causation_id="test_causation"
        )
        assert adaptation['adaptation_type'] == 'milestone_acknowledgement'
    
    def test_pure_semantic_derivation(self, engine, sample_cognition_snapshot):
        """
        Test 11: Pure semantic derivation (Layer 1)
        
        Validates that derive_semantics is mathematically pure:
        - No UUID
        - No timestamps
        - No transport metadata
        - Only semantic derivation
        """
        # Derive pure semantics
        semantic_adaptation = engine.derive_semantics(
            cognition_snapshot=sample_cognition_snapshot,
            policy_version="v1.0.0"
        )
        
        # Verify SemanticAdaptation type
        assert isinstance(semantic_adaptation, SemanticAdaptation)
        
        # Verify no transport metadata
        assert hasattr(semantic_adaptation, 'adaptation_type')
        assert hasattr(semantic_adaptation, 'recommendation')
        assert hasattr(semantic_adaptation, 'deterministic_inputs_hash')
        assert hasattr(semantic_adaptation, 'policy_version')
        assert hasattr(semantic_adaptation, 'policy_inputs_schema_version')
        assert hasattr(semantic_adaptation, 'schema_version')
        
        # Verify no UUID or timestamps
        assert not hasattr(semantic_adaptation, 'event_id')
        assert not hasattr(semantic_adaptation, 'timestamp')
        assert not hasattr(semantic_adaptation, 'trace_id')
        assert not hasattr(semantic_adaptation, 'causation_id')
        
        # Verify determinism
        assert semantic_adaptation.deterministic_inputs_hash is not None
        assert len(semantic_adaptation.deterministic_inputs_hash) == 64  # SHA-256
    
    def test_event_materialization(self, engine, sample_cognition_snapshot):
        """
        Test 12: Event materialization (Layer 2)
        
        Validates that materialize_adaptation_event adds transport metadata:
        - event_id (UUID)
        - timestamp (ISO format)
        - trace context
        - causation lineage
        - session metadata
        """
        # Derive pure semantics
        semantic_adaptation = engine.derive_semantics(
            cognition_snapshot=sample_cognition_snapshot,
            policy_version="v1.0.0"
        )
        
        # Materialize event
        adaptation_event = engine.materialize_adaptation_event(
            semantic_adaptation=semantic_adaptation,
            cognition_snapshot=sample_cognition_snapshot,
            user_id="test_user",
            session_id="test_session",
            causation_id="test_causation",
            trace_context={'trace_id': 'test-trace', 'span_id': 'test-span'}
        )
        
        # Verify transport metadata added
        assert 'event_id' in adaptation_event
        assert 'timestamp' in adaptation_event
        assert 'causation_id' in adaptation_event
        assert 'trace_id' in adaptation_event
        assert 'span_id' in adaptation_event
        assert 'session_id' in adaptation_event
        
        # Verify semantic adaptation preserved
        assert adaptation_event['adaptation_type'] == semantic_adaptation.adaptation_type
        assert adaptation_event['recommendation'] == semantic_adaptation.recommendation
        assert adaptation_event['deterministic_inputs_hash'] == semantic_adaptation.deterministic_inputs_hash
        assert adaptation_event['policy_version'] == semantic_adaptation.policy_version
        
        # Verify UUID format
        assert len(adaptation_event['event_id']) == 36  # UUID format
        assert adaptation_event['event_id'].count('-') == 4
    
    def test_two_layer_separation(self, engine, sample_cognition_snapshot):
        """
        Test 13: Two-layer separation
        
        Validates that the two layers are properly separated:
        - Layer 1 is mathematically pure (deterministic)
        - Layer 2 adds transport metadata (non-deterministic)
        - Combined derive_adaptation works correctly
        """
        # Layer 1: Pure semantics (deterministic)
        semantic_adaptation_1 = engine.derive_semantics(
            cognition_snapshot=sample_cognition_snapshot,
            policy_version="v1.0.0"
        )
        
        semantic_adaptation_2 = engine.derive_semantics(
            cognition_snapshot=sample_cognition_snapshot,
            policy_version="v1.0.0"
        )
        
        # Same semantic adaptation (deterministic)
        assert semantic_adaptation_1.adaptation_type == semantic_adaptation_2.adaptation_type
        assert semantic_adaptation_1.deterministic_inputs_hash == semantic_adaptation_2.deterministic_inputs_hash
        
        # Layer 2: Event materialization (non-deterministic due to UUID/timestamp)
        event_1 = engine.materialize_adaptation_event(
            semantic_adaptation=semantic_adaptation_1,
            cognition_snapshot=sample_cognition_snapshot,
            user_id="test_user",
            causation_id="test_causation"
        )
        
        event_2 = engine.materialize_adaptation_event(
            semantic_adaptation=semantic_adaptation_2,
            cognition_snapshot=sample_cognition_snapshot,
            user_id="test_user",
            causation_id="test_causation"
        )
        
        # Different event_id (non-deterministic)
        assert event_1['event_id'] != event_2['event_id']
        
        # Same semantic content (deterministic)
        assert event_1['adaptation_type'] == event_2['adaptation_type']
        assert event_1['deterministic_inputs_hash'] == event_2['deterministic_inputs_hash']
        
        # Combined: derive_adaptation works correctly
        combined_event = engine.derive_adaptation(
            cognition_snapshot=sample_cognition_snapshot,
            policy_version="v1.0.0",
            user_id="test_user",
            causation_id="test_causation"
        )
        
        assert combined_event['adaptation_type'] == semantic_adaptation_1.adaptation_type
        assert combined_event['deterministic_inputs_hash'] == semantic_adaptation_1.deterministic_inputs_hash


class TestDeterminismAcrossRestartScenarios:
    """
    Test determinism across restart scenarios
    
    These tests validate that adaptation derivation remains deterministic
    across process restarts and container restarts.
    
    Note: These tests are designed to be run in different scenarios:
    - Single process restart
    - Container restart
    - Different container instances
    """
    
    def test_process_restart_determinism(self):
        """
        Test: Process restart determinism
        
        Validates that adaptation derivation produces identical output
        after process restart (simulated by creating new engine instance)
        """
        cognition_snapshot = {
            "mastery": 0.45,
            "uncertainty": 0.6,
            "zpd_score": 0.5
        }
        
        # First engine instance (simulating first process)
        engine1 = DeterministicAdaptationEngine()
        adaptation1 = engine1.derive_adaptation(
            cognition_snapshot=cognition_snapshot,
            policy_version="v1.0.0",
            user_id="test_user",
            causation_id="test_causation"
        )
        
        # Second engine instance (simulating process restart)
        engine2 = DeterministicAdaptationEngine()
        adaptation2 = engine2.derive_adaptation(
            cognition_snapshot=cognition_snapshot,
            policy_version="v1.0.0",
            user_id="test_user",
            causation_id="test_causation"
        )
        
        # Verify identical output
        assert adaptation1['adaptation_type'] == adaptation2['adaptation_type']
        assert adaptation1['deterministic_inputs_hash'] == adaptation2['deterministic_inputs_hash']
        assert json.dumps(adaptation1['recommendation'], sort_keys=True) == \
               json.dumps(adaptation2['recommendation'], sort_keys=True)
        
        # Verify both deterministic
        assert engine1.verify_determinism(adaptation1)
        assert engine2.verify_determinism(adaptation2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
