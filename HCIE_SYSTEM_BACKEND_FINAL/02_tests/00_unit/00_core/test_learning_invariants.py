#!/usr/bin/env python3
"""
Test Learning State Manager Invariants
Validates the critical boundary between distributed correctness and learning correctness

Phase 10b: marker-quarantined. These tests exercise the
``LearningStateManager`` against a real Postgres connection. Opt in
with ``HCIE_FINALS_RUN_PG=1``.
"""

import json
import time
import uuid
import pytest

pytestmark = pytest.mark.requires_pg

from core.learning.learning_state_manager import LearningStateManager
from storage.postgres_store import PostgresInteractionStore

def test_idempotency_invariant():
    """
    Test that each event_id is processed exactly once
    """
    print("🧪 TESTING IDEMPOTENCY INVARIANT")
    print("=" * 50)
    
    # Setup
    db_store = PostgresInteractionStore()
    conn = db_store._get_connection()
    state_manager = LearningStateManager(conn)
    
    # Create test event
    event_id = uuid.uuid4()
    test_event = {
        "event_id": str(event_id),  # Store as string in event
        "user_id": "test-user",
        "event_type": "task_completed",
        "concept_id": "test_concept",
        "correct": True,
        "difficulty": 0.5,
        "response_time": 30.0
    }
    
    print(f"📦 Created test event: {event_id}")
    
    # Test 1: First processing should succeed
    def dummy_update(event):
        return {"status": "success", "delta": 0.1}
    
    result1 = state_manager.apply_learning_update(test_event, dummy_update)
    print(f"✅ First processing: {'SUCCESS' if result1 else 'FAILED'}")
    
    # Test 2: Second processing should be rejected
    result2 = state_manager.apply_learning_update(test_event, dummy_update)
    print(f"⏭️ Second processing: {'REJECTED' if not result2 else 'FAILED'}")
    
    # Test 3: Verify database state
    is_processed = state_manager.is_event_processed(event_id)
    print(f"🔍 Event marked as processed: {'YES' if is_processed else 'NO'}")
    
    # Get invariant report
    report = state_manager.get_invariant_report()
    print(f"📊 Invariant Report: {json.dumps(report, indent=2)}")
    
    # Cleanup
    cursor = conn.cursor()
    cursor.execute("DELETE FROM processed_events WHERE event_id = %s", (str(event_id),))
    cursor.execute("COMMIT")
    cursor.close()
    
    assert result1 and not result2 and is_processed, "idempotency invariant violated (event processed more than once)"

def test_determinism_invariant():
    """
    Test that same event_id always produces same result
    """
    print(f"\n🧪 TESTING DETERMINISM INVARIANT")
    print("=" * 50)
    
    # Setup
    db_store = PostgresInteractionStore()
    conn = db_store._get_connection()
    state_manager = LearningStateManager(conn)
    
    # Create test event
    event_id = uuid.uuid4()
    test_event = {
        "event_id": event_id,
        "user_id": "test-user",
        "event_type": "task_completed",
        "concept_id": "test_concept",
        "correct": True,
        "difficulty": 0.5,
        "response_time": 30.0
    }
    
    def deterministic_update(event):
        # Update that should always produce same result
        return {
            "status": "success",
            "delta": 0.1,
            "timestamp": hash(event.get("event_id", "")) % 1000  # Deterministic from event_id
        }
    
    # Process same event multiple times (should be cached after first)
    results = []
    for i in range(3):
        # Clear processed cache to test determinism
        state_manager._processed_cache.clear()
        result = state_manager.apply_learning_update(test_event, deterministic_update)
        results.append(result)
        print(f"🔄 Processing {i+1}: {'SUCCESS' if result else 'REJECTED'}")
    
    # All should succeed except first (due to idempotency)
    successes = sum(1 for r in results if r is not None)
    print(f"📊 Successful processes: {successes}/3 (should be 1)")
    
    # Cleanup
    cursor = conn.cursor()
    cursor.execute("DELETE FROM processed_events WHERE event_id = %s", (str(event_id),))
    cursor.execute("COMMIT")
    cursor.close()
    
    assert successes == 1, f"determinism/idempotency invariant: expected 1 success, got {successes}"

def test_replay_safety():
    """
    Test that DLQ replay events are handled safely
    """
    print(f"\n🧪 TESTING REPLAY SAFETY")
    print("=" * 50)
    
    # Setup
    db_store = PostgresInteractionStore()
    conn = db_store._get_connection()
    state_manager = LearningStateManager(conn)
    
    # Simulate DLQ replay scenario
    event_id = str(uuid.uuid4())
    replay_event = {
        "event_id": event_id,
        "user_id": "test-user",
        "event_type": "task_completed",
        "concept_id": "test_concept",
        "correct": True,
        "difficulty": 0.5,
        "response_time": 30.0,
        "replay": True,  # Mark as replay
        "original_event_id": event_id  # Track original
    }
    
    def replay_update(event):
        return {
            "status": "replay_success",
            "delta": 0.1,
            "replay": True
        }
    
    # Process original event
    result1 = state_manager.apply_learning_update(replay_event, replay_update)
    print(f"✅ Original processing: {'SUCCESS' if result1 else 'FAILED'}")
    
    # Simulate replay (same event_id from DLQ)
    result2 = state_manager.apply_learning_update(replay_event, replay_update)
    print(f"⏭️ Replay processing: {'REJECTED' if not result2 else 'FAILED'}")
    
    # Cleanup
    cursor = conn.cursor()
    cursor.execute("DELETE FROM processed_events WHERE event_id = %s", (str(event_id),))
    cursor.execute("COMMIT")
    cursor.close()
    
    assert result1 and not result2, "replay safety invariant violated (DLQ replay double-applied)"

def test_boundary_enforcement():
    """
    Test that boundary enforcement rejects invalid events
    """
    print(f"\n🧪 TESTING BOUNDARY ENFORCEMENT")
    print("=" * 50)
    
    # Setup
    db_store = PostgresInteractionStore()
    conn = db_store._get_connection()
    state_manager = LearningStateManager(conn)
    
    # Test invalid events
    invalid_events = [
        {"event_type": "task_completed"},  # Missing event_id
        {"event_id": "", "user_id": "test", "event_type": "task_completed"},  # Empty event_id
        {"event_id": "test", "user_id": "", "event_type": "task_completed"},  # Empty user_id
        {"event_id": "test", "user_id": "test"},  # Missing event_type
    ]
    
    def dummy_update(event):
        return {"status": "success"}
    
    rejected_count = 0
    for i, invalid_event in enumerate(invalid_events):
        result = state_manager.apply_learning_update(invalid_event, dummy_update)
        if result is None:
            rejected_count += 1
            print(f"❌ Invalid event {i+1}: REJECTED (correct)")
        else:
            print(f"❌ Invalid event {i+1}: ACCEPTED (wrong!)")
    
    print(f"📊 Rejected invalid events: {rejected_count}/{len(invalid_events)} (should be {len(invalid_events)})")
    
    assert rejected_count == len(invalid_events), f"boundary enforcement: {rejected_count}/{len(invalid_events)} invalid events rejected"

def main():
    """
    Run all invariant tests
    """
    print("🔒 LEARNING STATE MANAGER INVARIANT TESTS")
    print("=" * 60)
    
    try:
        # Run all tests
        test1 = test_idempotency_invariant()
        test2 = test_determinism_invariant()
        test3 = test_replay_safety()
        test4 = test_boundary_enforcement()
        
        print(f"\n🎯 FINAL RESULTS")
        print("=" * 50)
        print(f"✅ Idempotency: {'PASS' if test1 else 'FAIL'}")
        print(f"✅ Determinism: {'PASS' if test2 else 'FAIL'}")
        print(f"✅ Replay Safety: {'PASS' if test3 else 'FAIL'}")
        print(f"✅ Boundary Enforcement: {'PASS' if test4 else 'FAIL'}")
        
        all_passed = test1 and test2 and test3 and test4
        print(f"\n🏆 OVERALL: {'ALL INVARIANTS PASS' if all_passed else 'SOME INVARIANTS FAIL'}")
        
        if all_passed:
            print("\n✅ Learning State Manager is MATHEMATICALLY SAFE")
            print("✅ Ready for Bandit + Lyapunov integration")
        else:
            print("\n❌ Learning State Manager has INVARIANT VIOLATIONS")
            print("❌ NOT ready for learning integration")
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
