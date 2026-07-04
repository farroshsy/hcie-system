"""
Experiment Registry Tests

Validates replay-deterministic cohort assignment and experiment lifecycle.
Critical for ensuring pedagogical experiments are reproducible and replay-safe.
"""

import pytest
from datetime import datetime, timedelta
from app.services.experiment.experiment_registry import (
    ExperimentRegistry,
    Experiment,
    ExperimentStatus,
    ExperimentType,
    get_experiment_registry
)


def test_experiment_registration():
    """Test basic experiment registration"""
    registry = ExperimentRegistry()
    
    experiment = Experiment(
        experiment_id="test_exp_001",
        name="Test Policy Comparison",
        description="Compare v1.0.0 vs v1.1.0 adaptation policies",
        hypothesis="v1.1.0 will improve mastery gain by 10%",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0", "v1.1.0"],
        cohort_criteria={"grade_level": ["K-8"]},
        rollout_percentage=0.5,
        start_date=datetime.utcnow()
    )
    
    assert registry.register_experiment(experiment) == True
    assert registry.get_experiment("test_exp_001") is not None
    assert registry.get_experiment("test_exp_001").name == "Test Policy Comparison"


def test_experiment_duplicate_registration():
    """Test that duplicate experiment IDs are rejected"""
    registry = ExperimentRegistry()
    
    experiment = Experiment(
        experiment_id="test_exp_001",
        name="Test Experiment",
        description="Test description",
        hypothesis="Test hypothesis",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0"],
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow()
    )
    
    assert registry.register_experiment(experiment) == True
    assert registry.register_experiment(experiment) == False  # Should fail


def test_replay_deterministic_assignment():
    """
    CRITICAL TEST: Validate replay-deterministic cohort assignment.
    
    Same user_id + same experiment_seed → same experiment assignment.
    This is required for replay compatibility and counterfactual analysis.
    """
    registry = ExperimentRegistry()
    
    # Create active experiment
    experiment = Experiment(
        experiment_id="replay_test_001",
        name="Replay Determinism Test",
        description="Test replay-deterministic assignment",
        hypothesis="Assignment should be deterministic",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0", "v1.1.0"],
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow() - timedelta(days=1),
        status=ExperimentStatus.ACTIVE
    )
    
    registry.register_experiment(experiment)
    
    # Test 1: Same user + same seed → same assignment (immediate)
    user_id = "user_12345"
    seed = "test_seed_001"
    
    assignment1 = registry.assign_user_to_experiment(user_id, seed)
    assignment2 = registry.assign_user_to_experiment(user_id, seed)
    
    assert assignment1 == assignment2
    assert assignment1 == "replay_test_001"
    
    # Test 2: Different user + same seed → potentially different assignment
    user_id_2 = "user_67890"
    assignment3 = registry.assign_user_to_experiment(user_id_2, seed)
    
    # Should still be assigned to the experiment (100% rollout)
    assert assignment3 == "replay_test_001"
    
    # Test 3: Same user + different seed → potentially different assignment
    seed_2 = "test_seed_002"
    assignment4 = registry.assign_user_to_experiment(user_id, seed_2)
    
    # Should still be assigned to the experiment (100% rollout)
    assert assignment4 == "replay_test_001"


def test_replay_deterministic_policy_assignment():
    """
    CRITICAL TEST: Validate replay-deterministic policy assignment.
    
    Same user_id + same experiment_id → same policy version.
    Required for multi-policy experiments to be replay-safe.
    """
    registry = ExperimentRegistry()
    
    # Create multi-policy experiment
    experiment = Experiment(
        experiment_id="policy_test_001",
        name="Policy Assignment Test",
        description="Test deterministic policy assignment",
        hypothesis="Policy assignment should be deterministic",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0", "v1.1.0", "v1.2.0"],  # Multiple policies
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow() - timedelta(days=1),
        status=ExperimentStatus.ACTIVE
    )
    
    registry.register_experiment(experiment)
    
    # Test deterministic policy assignment
    user_id = "user_98765"
    experiment_id = "policy_test_001"
    
    policy1 = registry.assign_policy_for_user(user_id, experiment_id)
    policy2 = registry.assign_policy_for_user(user_id, experiment_id)
    
    assert policy1 == policy2  # Same assignment on repeated calls
    assert policy1 in experiment.policy_versions  # Valid policy
    
    # Test different users get potentially different policies
    user_id_2 = "user_11111"
    policy3 = registry.assign_policy_for_user(user_id_2, experiment_id)
    
    # Should be one of the valid policies
    assert policy3 in experiment.policy_versions
    
    # Test 100 calls to ensure determinism
    for i in range(100):
        policy = registry.assign_policy_for_user(user_id, experiment_id)
        assert policy == policy1  # Always the same for same user


def test_experiment_lifecycle():
    """Test experiment status transitions"""
    registry = ExperimentRegistry()
    
    experiment = Experiment(
        experiment_id="lifecycle_test_001",
        name="Lifecycle Test",
        description="Test experiment lifecycle",
        hypothesis="Lifecycle transitions work correctly",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0"],
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow(),
        status=ExperimentStatus.DRAFT
    )
    
    registry.register_experiment(experiment)
    
    # Test status transitions
    assert registry.update_experiment_status("lifecycle_test_001", ExperimentStatus.ACTIVE) == True
    assert registry.get_experiment("lifecycle_test_001").status == ExperimentStatus.ACTIVE
    
    assert registry.update_experiment_status("lifecycle_test_001", ExperimentStatus.PAUSED) == True
    assert registry.get_experiment("lifecycle_test_001").status == ExperimentStatus.PAUSED
    
    assert registry.update_experiment_status("lifecycle_test_001", ExperimentStatus.COMPLETED) == True
    assert registry.get_experiment("lifecycle_test_001").status == ExperimentStatus.COMPLETED


def test_experiment_filtering():
    """Test experiment listing with filters"""
    registry = ExperimentRegistry()
    
    # Create experiments with different types and statuses
    exp1 = Experiment(
        experiment_id="filter_test_001",
        name="Active Policy Comparison",
        description="Test",
        hypothesis="Test",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0"],
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow(),
        status=ExperimentStatus.ACTIVE
    )
    
    exp2 = Experiment(
        experiment_id="filter_test_002",
        name="Draft Cohort Segmentation",
        description="Test",
        hypothesis="Test",
        experiment_type=ExperimentType.COHORT_SEGMENTATION,
        policy_versions=["v1.0.0"],
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow(),
        status=ExperimentStatus.DRAFT
    )
    
    exp3 = Experiment(
        experiment_id="filter_test_003",
        name="Active Cohort Segmentation",
        description="Test",
        hypothesis="Test",
        experiment_type=ExperimentType.COHORT_SEGMENTATION,
        policy_versions=["v1.0.0"],
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow(),
        status=ExperimentStatus.ACTIVE
    )
    
    registry.register_experiment(exp1)
    registry.register_experiment(exp2)
    registry.register_experiment(exp3)
    
    # Test status filter
    active_experiments = registry.list_experiments(status=ExperimentStatus.ACTIVE)
    assert len(active_experiments) == 2
    
    # Test type filter
    cohort_experiments = registry.list_experiments(experiment_type=ExperimentType.COHORT_SEGMENTATION)
    assert len(cohort_experiments) == 2
    
    # Test combined filter
    active_cohort = registry.list_experiments(
        status=ExperimentStatus.ACTIVE,
        experiment_type=ExperimentType.COHORT_SEGMENTATION
    )
    assert len(active_cohort) == 1
    assert active_cohort[0].experiment_id == "filter_test_003"


def test_user_assignment_integration():
    """Test full user assignment flow"""
    registry = ExperimentRegistry()
    
    # Create active experiment
    experiment = Experiment(
        experiment_id="assignment_test_001",
        name="Assignment Integration Test",
        description="Test full assignment flow",
        hypothesis="Assignment flow works end-to-end",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0", "v1.1.0"],
        cohort_criteria={},
        rollout_percentage=0.5,  # 50% rollout
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=30),
        status=ExperimentStatus.ACTIVE
    )
    
    registry.register_experiment(experiment)
    
    # Get user assignment
    user_id = "user_integration_001"
    assignment = registry.get_user_assignment(user_id)
    
    # Assignment should either be None (not in rollout) or have experiment_id and policy_version
    if assignment:
        assert "experiment_id" in assignment
        assert "policy_version" in assignment
        assert assignment["experiment_id"] == "assignment_test_001"
        assert assignment["policy_version"] in experiment.policy_versions
    else:
        # User not in 50% rollout
        assert assignment is None


def test_experiment_lineage():
    """Test experiment lineage tracking"""
    registry = ExperimentRegistry()
    
    experiment = Experiment(
        experiment_id="lineage_test_001",
        name="Lineage Test",
        description="Test experiment lineage",
        hypothesis="Lineage tracking works",
        experiment_type=ExperimentType.POLICY_COMPARISON,
        policy_versions=["v1.0.0", "v1.1.0"],
        cohort_criteria={},
        rollout_percentage=1.0,
        start_date=datetime.utcnow() - timedelta(days=1),
        status=ExperimentStatus.ACTIVE
    )
    
    registry.register_experiment(experiment)
    
    # Assign some users
    for i in range(10):
        user_id = f"user_lineage_{i}"
        registry.assign_user_to_experiment(user_id)
        registry.assign_policy_for_user(user_id, "lineage_test_001")
    
    # Get lineage
    lineage = registry.get_experiment_lineage("lineage_test_001")
    
    assert "experiment" in lineage
    assert "assignment_count" in lineage
    assert "policy_distribution" in lineage
    assert lineage["assignment_count"] == 10
    
    # Check policy distribution
    policy_dist = lineage["policy_distribution"]
    assert "v1.0.0" in policy_dist
    assert "v1.1.0" in policy_dist
    assert sum(policy_dist.values()) == 10


def test_global_registry_singleton():
    """Test global registry singleton pattern"""
    registry1 = get_experiment_registry()
    registry2 = get_experiment_registry()
    
    # Should be the same instance
    assert registry1 is registry2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
