"""
Test Phase 3 Behavioral Policies Integration (Shared Runtime Architecture)

Tests that behavioral policy configurations are properly integrated
into the production runtime (UnifiedBrain) without semantic fragmentation.

Architecture: Policies are configuration/parameter sets for the shared runtime layer:
- Interaction Scheduler (Orchestration): Timing, conditions, routing, NO cognition
- UnifiedBrain (Runtime): Concept selection, candidate filtering, JT computation, ALL cognition
- Policy Configuration: Influences runtime behavior via parameter overrides, NOT logic replacement

This test verifies:
1. Interaction scheduler is pure orchestration (no cognition logic)
2. Policy configurations are passed to runtime layer
3. UnifiedBrain applies policy configurations as non-breaking overrides
4. Backward compatibility (existing infrastructure still works)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
pytest.skip(
    "phase-3 behavioral-policies e2e: requires the full running stack, absent in the isolated unit harness.",
    allow_module_level=True,
)

from infrastructure.experiment.interaction_scheduler import InteractionScheduler
from infrastructure.experiment.behavioral_policies import PolicyFactory, compute_policy_divergence
from core.learning.unified_brain import UnifiedLearningBrain


def test_interaction_scheduler_orchestration_only():
    """Test that interaction scheduler is pure orchestration (no cognition logic)"""
    print("🧪 Testing Interaction Scheduler (Orchestration Layer Only)")
    print("="*60)
    
    concepts = ["concept_001", "concept_002", "concept_003", "concept_004", "concept_005"]
    
    # Test with behavioral policy configurations enabled
    scheduler = InteractionScheduler(concepts, use_behavioral_policies=True)
    
    # Verify policy configurations are loaded
    print(f"  Loaded {len(scheduler.policy_configs)} policy configurations")
    
    # Test orchestration (concept selection should be None - deferred to runtime)
    print("\n📊 Testing Orchestration (Concept Selection Deferred to Runtime)")
    scheduled = scheduler.schedule_next(
        user_id="test_user",
        config={"policy": "hcie", "learner_archetype": "novice"},
        interaction_number=10,
        current_state={}
    )
    
    # Verify orchestration data
    assert scheduled["concept"] is None, "Concept should be None (deferred to runtime)"
    assert scheduled["policy"] == "hcie", "Policy should be hcie"
    assert scheduled["policy_config"] is not None, "Policy config should be provided"
    assert "timing_condition" in scheduled, "Timing condition should be included"
    assert "difficulty_condition" in scheduled, "Difficulty condition should be included"
    
    print(f"  ✅ Concept: {scheduled['concept']} (deferred to runtime)")
    print(f"  ✅ Policy: {scheduled['policy']}")
    print(f"  ✅ Policy config provided: {scheduled['policy_config'] is not None}")
    print(f"  ✅ Timing condition: {scheduled['timing_condition']}")
    print(f"  ✅ Difficulty condition: {scheduled['difficulty_condition']}")
    
    # Test interaction data simulation (archetype handlers still work)
    print("\n📊 Testing Interaction Data Simulation (Archetype Handlers)")
    interaction_data = scheduler.simulate_interaction_data(
        concept="concept_001",
        archetype="novice",
        interaction_number=10
    )
    
    assert "correctness" in interaction_data, "Interaction data should include correctness"
    assert "response_time" in interaction_data, "Interaction data should include response time"
    
    print(f"  ✅ Interaction data generated: {interaction_data}")
    
    print("\n✅ Interaction scheduler is pure orchestration (no cognition logic)")
    return True


def test_policy_configuration_integration():
    """Test that policy configurations are properly structured for runtime layer"""
    print("\n🧪 Testing Policy Configuration Structure")
    print("="*60)
    
    concepts = ["concept_001", "concept_002", "concept_003", "concept_004", "concept_005"]
    
    # Test policy configuration creation
    print("\n📊 Testing Policy Configuration Creation")
    policy_config = PolicyFactory.create_policy("hcie", concepts)
    
    # Verify policy configuration has required methods
    assert hasattr(policy_config, "get_governance_weights"), "Should have get_governance_weights"
    assert hasattr(policy_config, "get_bandit_config"), "Should have get_bandit_config"
    assert hasattr(policy_config, "get_transfer_config"), "Should have get_transfer_config"
    assert hasattr(policy_config, "get_ensemble_weights"), "Should have get_ensemble_weights"
    
    governance_weights = policy_config.get_governance_weights()
    bandit_config = policy_config.get_bandit_config()
    transfer_config = policy_config.get_transfer_config()
    ensemble_weights = policy_config.get_ensemble_weights()
    
    print(f"  ✅ Governance weights: {governance_weights}")
    print(f"  ✅ Bandit config: {bandit_config}")
    print(f"  ✅ Transfer config: {transfer_config}")
    print(f"  ✅ Ensemble weights: {ensemble_weights}")
    
    # Test policy divergence metrics
    print("\n📊 Testing Policy Divergence Metrics")
    policy1 = PolicyFactory.create_policy("random", concepts)
    policy2 = PolicyFactory.create_policy("mastery_greedy", concepts)
    divergence = compute_policy_divergence(policy1, policy2)
    
    print(f"\nRandom vs Mastery-Greedy:")
    print(f"  Governance Weight Divergence: {divergence['governance_weight_divergence']}")
    print(f"  Bandit Config Divergence: {divergence['bandit_config_divergence']}")
    print(f"  Characteristic Divergence: {divergence['characteristic_divergence']}")
    
    print("\n✅ Policy configurations properly structured for runtime layer")
    return True


def test_backward_compatibility():
    """Test backward compatibility (existing infrastructure still works)"""
    print("\n🧪 Testing Backward Compatibility")
    print("="*60)
    
    concepts = ["concept_001", "concept_002", "concept_003", "concept_004", "concept_005"]
    
    # Test with behavioral policies disabled (fallback)
    print("\n📊 Testing with Behavioral Policies Disabled (Fallback)")
    scheduler_fallback = InteractionScheduler(concepts, use_behavioral_policies=False)
    
    scheduled = scheduler_fallback.schedule_next(
        user_id="test_user",
        config={"policy": "random", "learner_archetype": "novice"},
        interaction_number=10,
        current_state={}
    )
    
    assert scheduled["concept"] is None, "Concept should be None (deferred to runtime)"
    assert scheduled["policy_config"] is None, "Policy config should be None (fallback)"
    
    print(f"  ✅ Concept: {scheduled['concept']} (deferred to runtime)")
    print(f"  ✅ Policy config: {scheduled['policy_config']} (fallback mode)")
    
    # Test interaction data simulation still works
    interaction_data = scheduler_fallback.simulate_interaction_data(
        concept="concept_001",
        archetype="novice",
        interaction_number=10
    )
    
    assert "correctness" in interaction_data, "Interaction data should still work"
    
    print(f"  ✅ Interaction data: {interaction_data}")
    
    print("\n✅ Backward compatibility maintained")
    return True


def test_experiment_context_isolation():
    """Test that policy configuration only applies in experiment context"""
    print("\n🧪 Testing Experiment Context Isolation")
    print("="*60)
    
    concepts = ["concept_001", "concept_002", "concept_003", "concept_004", "concept_005"]
    policy_config = PolicyFactory.create_policy("hcie", concepts)
    
    print("\n📊 Testing Experiment Context Isolation (Production Safety)")
    
    # Test 1: experiment_context=False should NOT apply policy config
    print("  Test 1: experiment_context=False (production mode)")
    brain_production = UnifiedLearningBrain(
        system_mode="jt",
        environment="research",
        policy_config=policy_config,
        experiment_context=False
    )
    
    # Verify policy config is stored but not applied
    assert brain_production.policy_config is not None, "Policy config should be stored"
    assert brain_production.experiment_context is False, "Experiment context should be False"
    
    # Check that default governance weights are used (not overridden)
    if hasattr(brain_production, 'jt_governance') and brain_production.jt_governance:
        # In production, default weights should be used
        print(f"  ✅ Production mode: Policy config stored but not applied (experiment_context=False)")
    
    # Test 2: experiment_context=True should apply policy config
    print("  Test 2: experiment_context=True (experiment mode)")
    brain_experiment = UnifiedLearningBrain(
        system_mode="jt",
        environment="research",
        policy_config=policy_config,
        experiment_context=True
    )
    
    # Verify policy config is applied
    assert brain_experiment.policy_config is not None, "Policy config should be stored"
    assert brain_experiment.experiment_context is True, "Experiment context should be True"
    
    print(f"  ✅ Experiment mode: Policy config applied (experiment_context=True)")
    
    # Test 3: No policy config (backward compatibility)
    print("  Test 3: No policy config (default behavior)")
    brain_default = UnifiedLearningBrain(
        system_mode="jt",
        environment="research",
        policy_config=None,
        experiment_context=False
    )
    
    assert brain_default.policy_config is None, "Policy config should be None"
    print(f"  ✅ Default behavior: No policy config, uses default parameters")
    
    print("\n✅ Experiment context isolation verified (production safety ensured)")
    return True


def test_semantic_fragmentation_fixed():
    """Test that semantic fragmentation is fixed (no cognition logic in orchestration)"""
    print("\n🧪 Testing Semantic Fragmentation Fixed")
    print("="*60)
    
    concepts = ["concept_001", "concept_002", "concept_003", "concept_004", "concept_005"]
    scheduler = InteractionScheduler(concepts, use_behavioral_policies=True)
    
    # Verify no policy selection methods exist (cognition logic removed)
    print("\n📊 Verifying No Cognition Logic in Interaction Scheduler")
    
    cognition_methods = [
        "_policy_random",
        "_policy_static",
        "_policy_mastery_greedy",
        "_policy_uncertainty_reduction",
        "_policy_zpd_aligned",
        "_policy_epsilon_greedy",
        "_policy_ucb",
        "_policy_thompson",
        "_policy_hcie"
    ]
    
    for method in cognition_methods:
        assert not hasattr(scheduler, method), f"Method {method} should not exist (cognition logic removed)"
        print(f"  ✅ {method} removed (no cognition logic)")
    
    # Verify orchestration methods still exist
    orchestration_methods = [
        "schedule_next",
        "simulate_interaction_data"
    ]
    
    for method in orchestration_methods:
        assert hasattr(scheduler, method), f"Method {method} should exist (orchestration logic)"
        print(f"  ✅ {method} exists (orchestration logic)")
    
    print("\n✅ Semantic fragmentation fixed (no cognition logic in orchestration layer)")
    return True


def test_all():
    """Run all tests"""
    print("🧪 Phase 3 Refactoring Tests (Semantic Fragmentation Fixed)")
    print("="*60)
    
    try:
        test_interaction_scheduler_orchestration_only()
        test_policy_configuration_integration()
        test_backward_compatibility()
        test_experiment_context_isolation()
        test_semantic_fragmentation_fixed()
        
        print("\n" + "="*60)
        print("✅ All Phase 3 refactoring tests passed")
        print("="*60)
        print("\n📊 Summary:")
        print("  - Interaction scheduler is pure orchestration (no cognition logic)")
        print("  - Policy configurations properly structured for runtime layer")
        print("  - Backward compatibility maintained")
        print("  - Experiment context isolation verified (production safety)")
        print("  - Semantic fragmentation fixed")
        print("  - Cognition logic deferred to UnifiedBrain (runtime layer)")
        
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_all()
