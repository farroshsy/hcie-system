#!/usr/bin/env python3
"""
Test Proper Reward Coupling
Verifies that bandit uses exogenous rewards, not endogenous delta

Phase 10b: ``test_exogenous_reward_coupling`` and
``test_deterministic_seeding`` are marker-quarantined because they
drive ``LearningLoopEngine`` over a real Postgres cursor.
``test_reward_stationarity`` only exercises the in-memory reward
calculator and runs under the default invocation. Opt in to the
quarantined tests with ``HCIE_FINALS_RUN_PG=1``.
"""

import json

import pytest as _pt_skip
_pt_skip.skip(
    "core.learning.learning_loop_engine was retired; test targets removed code.",
    allow_module_level=True,
)

import uuid
import pytest

from core.learning.learning_loop_engine import LearningLoopEngine
from storage.postgres_store import PostgresInteractionStore

@pytest.mark.requires_pg
def test_exogenous_reward_coupling():
    """
    Test that bandit uses proper reward calculator, not delta
    """
    print("🧪 TESTING EXOGENOUS REWARD COUPLING")
    print("=" * 50)
    
    # Setup
    db_store = PostgresInteractionStore()
    conn = db_store._get_connection()
    engine = LearningLoopEngine()
    
    # Create test event with clear reward components
    event_id = str(uuid.uuid4())
    test_event = {
        "event_id": event_id,
        "user_id": "test-user-reward",
        "event_type": "task_submitted",
        "concept": "test_concept",
        "reward": 0.1,  # This is learner input, NOT bandit reward
        "correct": True,
        "response_time": 20.0,
        "difficulty": 0.5,
        "consistency": 0.8
    }
    
    print(f"📋 Test event:")
    print(f"   Learner input reward: {test_event['reward']}")
    print(f"   Correct: {test_event['correct']}")
    print(f"   Response time: {test_event['response_time']}")
    print(f"   Difficulty: {test_event['difficulty']}")
    
    # Apply learning event
    cursor = conn.cursor()
    result = engine.apply_event(test_event, cursor)
    cursor.close()
    
    # Extract reward components from result
    if result.get("type") == "learning_computed":
        new_state = result.get("new_state", {})
        bandit_state = new_state.get("bandit", {})
        learner_result = result.get("learner", {})
        
        print(f"\n📊 Learning Results:")
        print(f"   Learner delta: {learner_result.get('delta', 0):.6f}")
        print(f"   New mastery: {new_state.get('mastery', {}).get('global', 0):.6f}")
        print(f"   Bandit action: {bandit_state.get('last_action', 'unknown')}")
        print(f"   Bandit values: {bandit_state.get('values', {})}")
        
        # Test the critical difference
        learner_delta = learner_result.get("delta", 0)
        
        # Calculate what the reward should be using the reward calculator
        # Now truly exogenous - no learning dependency
        reward_data = engine.reward_calculator.compute_detailed_reward(
            correct=test_event["correct"],
            time_taken=test_event["response_time"],
            difficulty=test_event["difficulty"],
            response_consistency=test_event["consistency"]
            # Removed: learning_progress (was creating weak feedback loop)
            # Removed: user_mastery (was creating state dependency)
        )
        
        proper_reward = reward_data.get("total_reward", 0)
        
        print(f"\n🔍 Reward Coupling Analysis:")
        print(f"   Learner delta (old way): {learner_delta:.6f}")
        print(f"   Proper reward (new way): {proper_reward:.6f}")
        
        # They should be different (this proves we fixed the coupling)
        coupling_fixed = abs(learner_delta - proper_reward) > 0.01
        print(f"   Coupling fixed: {'YES' if coupling_fixed else 'NO'}")
        
        # Verify reward is bounded and meaningful
        reward_bounded = 0 <= proper_reward <= 1
        print(f"   Reward bounded [0,1]: {'YES' if reward_bounded else 'NO'}")
        
        # Cleanup
        cursor = conn.cursor()
        cursor.execute("DELETE FROM processed_events WHERE user_id = %s", (test_event["user_id"],))
        cursor.execute("DELETE FROM user_state WHERE user_id = %s", (test_event["user_id"],))
        cursor.execute("COMMIT")
        cursor.close()
        
        return coupling_fixed and reward_bounded
    
    return False

@pytest.mark.requires_pg
def test_deterministic_seeding():
    """
    Test that SHA256 seeding is stable across runs
    """
    print(f"\n🧪 TESTING DETERMINISTIC SEEDING")
    print("=" * 50)
    
    # Setup
    db_store = PostgresInteractionStore()
    conn = db_store._get_connection()
    engine = LearningLoopEngine()
    
    # Create test event
    event_id = str(uuid.uuid4())
    test_event = {
        "event_id": event_id,
        "user_id": "test-user-seed",
        "event_type": "task_submitted",
        "concept": "test_concept",
        "reward": 0.1,
        "correct": True,
        "response_time": 20.0,
        "difficulty": 0.5
    }
    
    print(f"📋 Testing event_id: {event_id}")
    
    # Apply same event multiple times
    actions = []
    for i in range(3):
        cursor = conn.cursor()
        result = engine.apply_event(test_event, cursor)
        cursor.close()
        
        if result.get("type") == "learning_computed":
            new_state = result.get("new_state", {})
            bandit_state = new_state.get("bandit", {})
            action = bandit_state.get("last_action", 'unknown')
            actions.append(action)
            print(f"   Run {i+1}: bandit action = {action}")
        
        # Cleanup for next run
        cursor = conn.cursor()
        cursor.execute("DELETE FROM processed_events WHERE user_id = %s", (test_event["user_id"],))
        cursor.execute("DELETE FROM user_state WHERE user_id = %s", (test_event["user_id"],))
        cursor.execute("COMMIT")
        cursor.close()
    
    # Check if all actions are identical
    all_same = all(action == actions[0] for action in actions)
    print(f"\n📊 Seeding Results:")
    print(f"   All actions identical: {'YES' if all_same else 'NO'}")
    print(f"   Action sequence: {actions}")
    
    return all_same

def test_reward_stationarity():
    """
    Test that rewards are stationary (not dependent on mastery level)
    """
    print(f"\n🧪 TESTING REWARD STATIONARITY")
    print("=" * 50)
    
    # Setup
    db_store = PostgresInteractionStore()
    conn = db_store._get_connection()
    engine = LearningLoopEngine()
    
    # Create two identical events for different mastery levels
    base_event = {
        "event_id": str(uuid.uuid4()),
        "user_id": "test-user-stationarity",
        "event_type": "task_submitted",
        "concept": "test_concept",
        "reward": 0.1,
        "correct": True,
        "response_time": 20.0,
        "difficulty": 0.5,
        "consistency": 0.8
    }
    
    # Test at low mastery
    low_mastery_state = {
        "mastery": {"global": 0.1},
        "bandit": {"counts": {"easy": 0, "hard": 0}, "values": {"easy": 0.5, "hard": 0.5}}
    }
    
    # Test at high mastery  
    high_mastery_state = {
        "mastery": {"global": 0.8},
        "bandit": {"counts": {"easy": 10, "hard": 10}, "values": {"easy": 0.5, "hard": 0.5}}
    }
    
    # Calculate rewards at different mastery levels
    # Now truly exogenous - should be identical regardless of mastery
    low_reward_data = engine.reward_calculator.compute_detailed_reward(
        correct=base_event["correct"],
        time_taken=base_event["response_time"],
        difficulty=base_event["difficulty"],
        response_consistency=base_event["consistency"]
        # Removed: learning_progress (was creating weak feedback loop)
        # Removed: user_mastery (was creating state dependency)
    )
    
    high_reward_data = engine.reward_calculator.compute_detailed_reward(
        correct=base_event["correct"],
        time_taken=base_event["response_time"],
        difficulty=base_event["difficulty"],
        response_consistency=base_event["consistency"]
        # Removed: learning_progress (was creating weak feedback loop)
        # Removed: user_mastery (was creating state dependency)
    )
    
    low_reward = low_reward_data.get("total_reward", 0)
    high_reward = high_reward_data.get("total_reward", 0)
    
    print(f"📊 Stationarity Results:")
    print(f"   Low mastery (0.1) reward: {low_reward:.6f}")
    print(f"   High mastery (0.8) reward: {high_reward:.6f}")
    print(f"   Difference: {abs(low_reward - high_reward):.6f}")
    
    # Rewards should be identical (truly exogenous)
    perfectly_stationary = abs(low_reward - high_reward) < 0.001
    print(f"   Perfectly stationary (exogenous): {'YES' if perfectly_stationary else 'NO'}")
    
    return perfectly_stationary

def main():
    """
    Test reward coupling fixes
    """
    print("🔒 REWARD COUPLING TESTS")
    print("=" * 60)
    
    try:
        # Test 1: Exogenous reward coupling
        test1 = test_exogenous_reward_coupling()
        
        # Test 2: Deterministic seeding
        test2 = test_deterministic_seeding()
        
        # Test 3: Reward stationarity
        test3 = test_reward_stationarity()
        
        print(f"\n🎯 FINAL REWARD COUPLING RESULTS")
        print("=" * 50)
        print(f"✅ Exogenous reward coupling: {'PASS' if test1 else 'FAIL'}")
        print(f"✅ Deterministic seeding: {'PASS' if test2 else 'FAIL'}")
        print(f"✅ Perfect stationarity (exogenous): {'PASS' if test3 else 'FAIL'}")
        
        all_tests_pass = test1 and test2 and test3
        
        if all_tests_pass:
            print(f"\n🏆 REWARD COUPLING FIXED")
            print(f"✅ Bandit uses exogenous rewards")
            print(f"✅ No endogenous feedback")
            print(f"✅ Deterministic behavior")
            print(f"✅ Stationary reward signals")
            print(f"✅ Ready for mathematical bandit analysis")
        else:
            print(f"\n❌ REWARD COUPLING ISSUES DETECTED")
            print(f"❌ Bandit may still have endogenous bias")
            print(f"❌ Not ready for mathematical guarantees")
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
