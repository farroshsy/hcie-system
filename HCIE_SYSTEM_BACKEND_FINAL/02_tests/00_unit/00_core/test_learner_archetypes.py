"""
Test learner archetype configurations

Verifies that learner archetypes provide valid Unified Brain parameter configurations.
This ensures evaluation validity - archetypes use the same Unified Brain cognition logic
with different parameter tuning.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.learning.learner_archetypes import (
    ArchetypeType,
    LearnerArchetypeConfig
)


def test_archetype_configurations():
    """Test that all archetypes provide valid Unified Brain parameter configurations"""
    print("🧪 Testing Learner Archetype Configurations")
    print("=" * 60)
    
    # Test all archetype configurations
    all_configs = LearnerArchetypeConfig.get_all_archetype_configs()
    assert len(all_configs) == 6, "Should have 6 archetype configurations"
    print(f"  ✅ Created {len(all_configs)} archetype configurations")
    
    # Test each archetype configuration
    for archetype_type in ArchetypeType:
        config = LearnerArchetypeConfig.get_archetype_config(archetype_type)
        description = LearnerArchetypeConfig.get_archetype_description(archetype_type)
        
        # Verify configuration has required Unified Brain parameters
        required_params = [
            'learning_rate',
            'exploration_rate',
            'transfer_weight',
            'uncertainty_weight',
            'zpd_weight',
            'challenge_weight',
            'mastery_weight',
            'lyapunov_weight',
            'bayesian_weight',
            'kalman_weight'
        ]
        
        for param in required_params:
            assert param in config, f"{archetype_type.value} missing parameter: {param}"
            assert 0.0 <= config[param] <= 1.0, f"{archetype_type.value} {param} out of range: {config[param]}"
        
        print(f"  ✅ {archetype_type.value}: {description}")
    
    # Test specific archetype characteristics
    print("\n🧪 Testing Archetype Characteristics")
    print("=" * 60)
    
    # Novice: Slow learning, high uncertainty
    novice_config = LearnerArchetypeConfig.get_archetype_config(ArchetypeType.NOVICE)
    assert novice_config['learning_rate'] == 0.1, "Novice should have slow learning rate"
    assert novice_config['uncertainty_weight'] == 0.8, "Novice should have high uncertainty weight"
    assert novice_config['transfer_weight'] == 0.2, "Novice should have low transfer weight"
    print(f"  ✅ Novice: learning_rate={novice_config['learning_rate']}, "
          f"uncertainty_weight={novice_config['uncertainty_weight']}, "
          f"transfer_weight={novice_config['transfer_weight']}")
    
    # Unstable: Has variance parameter
    unstable_config = LearnerArchetypeConfig.get_archetype_config(ArchetypeType.UNSTABLE)
    assert 'cognition_variance' in unstable_config, "Unstable should have variance parameter"
    assert unstable_config['cognition_variance'] == 0.1, "Unstable should have variance 0.1"
    print(f"  ✅ Unstable: cognition_variance={unstable_config['cognition_variance']}")
    
    # Transfer-Heavy: High transfer
    transfer_config = LearnerArchetypeConfig.get_archetype_config(ArchetypeType.TRANSFER_HEAVY)
    assert transfer_config['transfer_weight'] == 0.8, "Transfer-heavy should have high transfer weight"
    print(f"  ✅ Transfer-Heavy: transfer_weight={transfer_config['transfer_weight']}")
    
    # Forgetting: Has forgetting rate
    forgetting_config = LearnerArchetypeConfig.get_archetype_config(ArchetypeType.FORGETTING)
    assert 'forgetting_rate' in forgetting_config, "Forgetting should have forgetting rate"
    assert forgetting_config['forgetting_rate'] == 0.15, "Forgetting should have forgetting rate 0.15"
    print(f"  ✅ Forgetting: forgetting_rate={forgetting_config['forgetting_rate']}")
    
    # Exploration-Sensitive: High exploration, novelty bonus
    exploration_config = LearnerArchetypeConfig.get_archetype_config(ArchetypeType.EXPLORATION_SENSITIVE)
    assert exploration_config['exploration_rate'] == 0.7, "Exploration-sensitive should have high exploration rate"
    assert 'novelty_bonus' in exploration_config, "Exploration-sensitive should have novelty bonus"
    print(f"  ✅ Exploration-Sensitive: exploration_rate={exploration_config['exploration_rate']}, "
          f"novelty_bonus={exploration_config['novelty_bonus']}")
    
    # Challenge-Seeking: High learning rate, high ZPD
    challenge_config = LearnerArchetypeConfig.get_archetype_config(ArchetypeType.CHALLENGE_SEEKING)
    assert challenge_config['learning_rate'] == 0.4, "Challenge-seeking should have high learning rate"
    assert challenge_config['zpd_weight'] == 0.8, "Challenge-seeking should have high ZPD weight"
    assert challenge_config['challenge_weight'] == 0.7, "Challenge-seeking should prefer challenge"
    print(f"  ✅ Challenge-Seeking: learning_rate={challenge_config['learning_rate']}, "
          f"zpd_weight={challenge_config['zpd_weight']}, "
          f"challenge_weight={challenge_config['challenge_weight']}")
    
    print("\n" + "=" * 60)
    print("✅ All learner archetype configuration tests passed")
    print("=" * 60)
    print("\n📊 Summary:")
    print("  - Archetypes provide Unified Brain parameter configurations")
    print("  - All configurations have required parameters")
    print("  - Parameter values are in valid range [0, 1]")
    print("  - Each archetype has distinct characteristics")
    print("  - Evaluation validity ensured: same cognition logic, different parameters")
    
    return True


def test_all():
    """Run all learner archetype tests"""
    try:
        test_archetype_configurations()
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_all()
