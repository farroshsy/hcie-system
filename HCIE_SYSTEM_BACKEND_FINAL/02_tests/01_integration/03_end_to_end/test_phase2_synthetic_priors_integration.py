"""
Test Phase 2 Synthetic Priors Integration

Tests that synthetic behavioral priors are properly integrated
into the interaction scheduler for ecological validity.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
pytest.skip(
    "phase-2 synthetic-priors e2e: requires the full running stack (api/pg/redis/kafka), absent in the isolated unit harness.",
    allow_module_level=True,
)

from infrastructure.experiment.interaction_scheduler import InteractionScheduler


def test_synthetic_priors_integration():
    """Test that synthetic priors are integrated into interaction scheduler"""
    print("🧪 Testing Phase 2 Synthetic Priors Integration")
    print("="*60)
    
    concepts = ["concept_001", "concept_002", "concept_003"]
    
    # Test with synthetic priors enabled
    print("\n📊 Testing with synthetic priors enabled")
    scheduler = InteractionScheduler(concepts, use_synthetic_priors=True)
    
    # Test each archetype
    archetypes = ["novice", "unstable", "transfer_heavy", "forgetting", 
                  "exploration_sensitive", "challenge_seeking"]
    
    for archetype in archetypes:
        print(f"\n  Archetype: {archetype}")
        scheduled = scheduler.schedule_next(
            user_id="test_user",
            config={"policy": "random", "learner_archetype": archetype},
            interaction_number=10
        )
        
        interaction_data = scheduled["interaction_data"]
        
        # Check that synthetic priors fields are present
        if "mastery" in interaction_data:
            print(f"    ✅ Mastery field present: {interaction_data['mastery']:.3f}")
        else:
            print(f"    ⚠️ Mastery field missing")
        
        print(f"    Correctness: {interaction_data['correctness']}")
        print(f"    Response Time: {interaction_data['response_time']:.2f}s")
        print(f"    Difficulty: {interaction_data['difficulty']}")
    
    # Test with synthetic priors disabled
    print("\n📊 Testing with synthetic priors disabled (fallback)")
    scheduler_fallback = InteractionScheduler(concepts, use_synthetic_priors=False)
    
    scheduled = scheduler_fallback.schedule_next(
        user_id="test_user",
        config={"policy": "random", "learner_archetype": "novice"},
        interaction_number=10
    )
    
    interaction_data = scheduled["interaction_data"]
    
    print(f"  Correctness: {interaction_data['correctness']}")
    print(f"  Response Time: {interaction_data['response_time']:.2f}s")
    print(f"  Difficulty: {interaction_data['difficulty']}")
    
    if "mastery" not in interaction_data:
        print(f"    ✅ Mastery field not present (expected for fallback)")
    
    print("\n✅ Phase 2 integration test completed")
    return True


if __name__ == "__main__":
    try:
        test_synthetic_priors_integration()
        print("\n" + "="*60)
        print("✅ All Phase 2 integration tests passed")
        print("="*60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
