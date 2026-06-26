"""
Runtime Experiment Injection Tests

Validates that experiment assignment is correctly injected into adaptation runtime.
Critical for multi-policy pedagogical runtime and replay-safe experiments.
"""

import pytest
from datetime import datetime, timedelta
from app.services.experiment.runtime_experiment_injection import (
    RuntimeExperimentInjector,
    ExperimentContext,
    get_runtime_experiment_injector
)
from app.services.experiment.experiment_registry import (
    ExperimentRegistry,
    Experiment,
    ExperimentStatus,
    ExperimentType
)


def test_experiment_context_creation():
    """Test basic experiment context creation"""
    context = ExperimentContext(
        user_id="user_001",
        experiment_id="exp_001",
        policy_version="v1.0.0",
        cohort_id="exp_001:v1.0.0",
        assignment_hash="abc123",
        experiment_seed="seed_001"
    )
    
    assert context.user_id == "user_001"
    assert context.experiment_id == "exp_001"
    assert context.policy_version == "v1.0.0"
    assert context.cohort_id == "exp_001:v1.0.0"
    assert context.assignment_hash == "abc123"
    assert context.experiment_seed == "seed_001"
    assert context.is_active() == True


def test_experiment_context_no_assignment():
    """Test experiment context with no active assignment"""
    context = ExperimentContext(user_id="user_002")
    
    assert context.user_id == "user_002"
    assert context.experiment_id is None
    assert context.policy_version is None
    assert context.is_active() == False


def test_experiment_context_to_dict():
    """Test experiment context serialization"""
    context = ExperimentContext(
        user_id="user_001",
        experiment_id="exp_001",
        policy_version="v1.0.0",
        cohort_id="exp_001:v1.0.0",
        assignment_hash="abc123",
        experiment_seed="seed_001"
    )
    
    context_dict = context.to_dict()
    
    assert context_dict["experiment_id"] == "exp_001"
    assert context_dict["policy_version"] == "v1.0.0"
    assert context_dict["cohort_id"] == "exp_001:v1.0.0"
    assert context_dict["assignment_hash"] == "abc123"
    assert context_dict["experiment_seed"] == "seed_001"
    assert "timestamp" in context_dict


def test_runtime_injector_initialization():
    """Test RuntimeExperimentInjector initialization"""
    registry = ExperimentRegistry()
    injector = RuntimeExperimentInjector(registry)
    
    assert injector._experiment_registry is registry
    assert injector._context_cache == {}


def test_runtime_injector_no_active_experiment():
    """Test injector with no active experiments"""
    registry = ExperimentRegistry()
    injector = RuntimeExperimentInjector(registry)
    
    context = injector.get_experiment_context("user_001")
    
    assert context.user_id == "user_001"
    assert context.is_active() == False
    assert context.experiment_id is None
    assert context.policy_version is None


def test_runtime_injector_with_active_experiment():
    """Test injector with active experiment assignment"""
    registry = ExperimentRegistry()
    injector = RuntimeExperimentInjector(registry)
    
    # Create active experiment
    experiment = Experiment(
        experiment_id="injection_test_001",
        name="Injection Test",
        description="Test runtime injection",
        hypothesis="Injection works correctly",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0", "v1.1.0"],
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow() - timedelta(days=1),
        status=ExperimentStatus.ACTIVE
    )
    
    registry.register_experiment(experiment)
    
    # Get experiment context
    context = injector.get_experiment_context("user_injection_001")
    
    assert context.user_id == "user_injection_001"
    assert context.is_active() == True
    assert context.experiment_id == "injection_test_001"
    assert context.policy_version in ["v1.0.0", "v1.1.0"]
    assert context.cohort_id == f"injection_test_001:{context.policy_version}"
    assert context.assignment_hash is not None
    assert len(context.assignment_hash) == 16  # SHA256 truncated to 16 chars


def test_runtime_injector_deterministic_assignment():
    """
    CRITICAL TEST: Validate deterministic experiment assignment.
    
    Same user_id → same experiment context (deterministic).
    Required for replay-safe experiments.
    """
    registry = ExperimentRegistry()
    injector = RuntimeExperimentInjector(registry)
    
    # Create active experiment
    experiment = Experiment(
        experiment_id="deterministic_test_001",
        name="Deterministic Assignment Test",
        description="Test deterministic assignment",
        hypothesis="Assignment is deterministic",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0", "v1.1.0"],
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow() - timedelta(days=1),
        status=ExperimentStatus.ACTIVE
    )
    
    registry.register_experiment(experiment)
    
    # Test 1: Same user → same assignment (immediate)
    context1 = injector.get_experiment_context("user_det_001")
    context2 = injector.get_experiment_context("user_det_001")
    
    assert context1.experiment_id == context2.experiment_id
    assert context1.policy_version == context2.policy_version
    assert context1.assignment_hash == context2.assignment_hash
    
    # Test 2: Cache consistency
    assert "user_det_001:default" in injector._context_cache
    
    # Test 3: Different users → potentially different assignments
    context3 = injector.get_experiment_context("user_det_002")
    
    # Should still be assigned to the experiment (100% rollout)
    assert context3.experiment_id == "deterministic_test_001"
    # Policy version may differ based on deterministic hash


def test_runtime_injector_inject_into_adaptation():
    """Test injecting experiment context into adaptation inputs"""
    registry = ExperimentRegistry()
    injector = RuntimeExperimentInjector(registry)
    
    # Create active experiment
    experiment = Experiment(
        experiment_id="adaptation_injection_001",
        name="Adaptation Injection Test",
        description="Test adaptation injection",
        hypothesis="Injection into adaptation works",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0", "v1.1.0"],
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow() - timedelta(days=1),
        status=ExperimentStatus.ACTIVE
    )
    
    registry.register_experiment(experiment)
    
    # Original adaptation inputs
    adaptation_inputs = {
        "mastery": 0.5,
        "uncertainty": 0.3,
        "zpd_score": 0.7
    }
    
    # Inject experiment context
    enriched_inputs = injector.inject_into_adaptation(
        user_id="user_adapt_001",
        adaptation_inputs=adaptation_inputs
    )
    
    # Verify enrichment
    assert "mastery" in enriched_inputs  # Original fields preserved
    assert "uncertainty" in enriched_inputs
    assert "experiment_context" in enriched_inputs
    assert "policy_version" in enriched_inputs
    
    assert enriched_inputs["experiment_context"]["experiment_id"] == "adaptation_injection_001"
    assert enriched_inputs["policy_version"] in ["v1.0.0", "v1.1.0"]


def test_runtime_injector_attach_to_event():
    """Test attaching experiment lineage to event payload"""
    registry = ExperimentRegistry()
    injector = RuntimeExperimentInjector(registry)
    
    # Create active experiment
    experiment = Experiment(
        experiment_id="event_lineage_001",
        name="Event Lineage Test",
        description="Test event lineage attachment",
        hypothesis="Event lineage attachment works",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0", "v1.1.0"],
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow() - timedelta(days=1),
        status=ExperimentStatus.ACTIVE
    )
    
    registry.register_experiment(experiment)
    
    # Original event payload
    event_payload = {
        "event_id": "evt_001",
        "event_type": "CognitionUpdated",
        "user_id": "user_event_001"
    }
    
    # Attach experiment lineage
    enriched_payload = injector.attach_to_event(
        user_id="user_event_001",
        event_payload=event_payload
    )
    
    # Verify lineage attachment
    assert "event_id" in enriched_payload  # Original fields preserved
    assert "experiment_lineage" in enriched_payload
    
    assert enriched_payload["experiment_lineage"]["experiment_id"] == "event_lineage_001"
    assert enriched_payload["experiment_lineage"]["policy_version"] in ["v1.0.0", "v1.1.0"]
    assert enriched_payload["experiment_lineage"]["assignment_hash"] is not None


def test_runtime_injector_get_policy_version():
    """Test getting policy version for user"""
    registry = ExperimentRegistry()
    injector = RuntimeExperimentInjector(registry)
    
    # Create active experiment
    experiment = Experiment(
        experiment_id="policy_version_001",
        name="Policy Version Test",
        description="Test policy version retrieval",
        hypothesis="Policy version retrieval works",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0", "v1.1.0"],
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow() - timedelta(days=1),
        status=ExperimentStatus.ACTIVE
    )
    
    registry.register_experiment(experiment)
    
    # Get policy version
    policy_version = injector.get_policy_version_for_user("user_policy_001")
    
    assert policy_version is not None
    assert policy_version in ["v1.0.0", "v1.1.0"]
    
    # Test with no active experiment
    policy_version_none = injector.get_policy_version_for_user("user_no_exp")
    # This should still return a policy version since the experiment has 100% rollout
    # If we wanted to test no assignment, we'd need a user outside the rollout percentage


def test_runtime_injector_clear_context():
    """Test clearing cached experiment context"""
    registry = ExperimentRegistry()
    injector = RuntimeExperimentInjector(registry)
    
    # Create active experiment
    experiment = Experiment(
        experiment_id="clear_context_001",
        name="Clear Context Test",
        description="Test context clearing",
        hypothesis="Context clearing works",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0"],
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow() - timedelta(days=1),
        status=ExperimentStatus.ACTIVE
    )
    
    registry.register_experiment(experiment)
    
    # Get context (caches it)
    context1 = injector.get_experiment_context("user_clear_001")
    cache_key = "user_clear_001:default"
    assert cache_key in injector._context_cache
    
    # Clear context
    injector.clear_context("user_clear_001")
    assert cache_key not in injector._context_cache
    
    # Get context again (should recompute)
    context2 = injector.get_experiment_context("user_clear_001")
    assert cache_key in injector._context_cache
    
    # Should still be deterministic
    assert context1.experiment_id == context2.experiment_id
    assert context1.policy_version == context2.policy_version


def test_global_injector_singleton():
    """Test global injector singleton pattern"""
    injector1 = get_runtime_experiment_injector()
    injector2 = get_runtime_experiment_injector()
    
    # Should be the same instance
    assert injector1 is injector2


def test_injection_with_rollout_percentage():
    """Test injection with partial rollout percentage"""
    registry = ExperimentRegistry()
    injector = RuntimeExperimentInjector(registry)
    
    # Create experiment with 50% rollout
    experiment = Experiment(
        experiment_id="rollout_test_001",
        name="Rollout Test",
        description="Test partial rollout",
        hypothesis="Partial rollout works correctly",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0"],
        cohort_criteria={},
        rollout_percentage=0.5,  # 50% rollout
        start_date=datetime.utcnow() - timedelta(days=1),
        status=ExperimentStatus.ACTIVE
    )
    
    registry.register_experiment(experiment)
    
    # Get context for multiple users
    assigned_count = 0
    unassigned_count = 0
    
    for i in range(100):
        user_id = f"user_rollout_{i}"
        context = injector.get_experiment_context(user_id)
        
        if context.is_active():
            assigned_count += 1
        else:
            unassigned_count += 1
    
    # Should be approximately 50% assigned (with some tolerance for hash distribution)
    # In a real test, we'd use statistical significance, but for now just check it's not 0 or 100
    assert assigned_count > 0
    assert unassigned_count > 0
    assert 40 <= assigned_count <= 60  # Allow some tolerance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
