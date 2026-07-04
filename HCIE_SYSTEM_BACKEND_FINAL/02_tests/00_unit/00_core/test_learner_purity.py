#!/usr/bin/env python3
"""
Test Learner Purity: Ensure learners don't commit independently
This is the final invariant for mathematical correctness

Phase 10b: marker-quarantined. This test directly drives the Postgres
transaction boundary and requires a live database. Opt in with
``HCIE_FINALS_RUN_PG=1``.
"""

import json

import pytest as _pt_skip
_pt_skip.skip(
    "core.learning.learning_loop_engine was retired; test targets removed code.",
    allow_module_level=True,
)

import uuid
import pytest

pytestmark = pytest.mark.requires_pg

from core.learning.learning_loop_engine import LearningLoopEngine
from storage.postgres_store import PostgresInteractionStore

def test_learner_no_independent_commits():
    """
    Test that LearningLoopEngine doesn't commit independently
    """
    print("🧪 TESTING LEARNER PURITY")
    print("=" * 50)
    
    # Setup
    db_store = PostgresInteractionStore()
    conn = db_store._get_connection()
    engine = LearningLoopEngine()
    
    # Create test event
    event_id = str(uuid.uuid4())
    test_event = {
        "event_id": event_id,
        "user_id": "test-user-purity",
        "event_type": "task_submitted",  # Use supported event type
        "concept": "test_concept",
        "reward": 0.1  # Add reward field
    }
    
    # Test 1: Learner should not affect DB without explicit commit
    print("📋 Test 1: Learner computation without commit")
    
    cursor = conn.cursor()
    
    # Get initial state
    cursor.execute("SELECT COUNT(*) FROM user_state WHERE user_id = %s", (test_event["user_id"],))
    initial_count = cursor.fetchone()[0]
    print(f"   Initial user_state count: {initial_count}")
    
    # Apply learner update (should NOT commit)
    result = engine.apply_event(test_event, cursor)
    
    # Check if learner affected DB without explicit commit
    cursor.execute("SELECT COUNT(*) FROM user_state WHERE user_id = %s", (test_event["user_id"],))
    after_learner_count = cursor.fetchone()[0]
    print(f"   After learner (no commit): {after_learner_count}")
    
    learner_pure = (after_learner_count == initial_count)
    print(f"   Learner purity: {'PASS' if learner_pure else 'FAIL'}")
    
    # Test 2: Consumer commits atomically
    print(f"\n📋 Test 2: Consumer atomic commit")
    
    # Simulate consumer atomic transaction
    cursor.execute("BEGIN")
    
    # Persist learner result
    if result.get("type") == "learning_computed":
        state_json = result.get("state_json")
        cursor.execute("""
            INSERT INTO user_state (user_id, mastery)
            VALUES (%s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET 
                mastery = %s,
                updated_at = CURRENT_TIMESTAMP
        """, (test_event["user_id"], state_json, state_json))
    
    # Mark as processed
    import uuid as uuid_lib
    event_uuid = uuid_lib.UUID(event_id) if isinstance(event_id, str) else event_id
    cursor.execute("""
        INSERT INTO processed_events (event_id, user_id) 
        VALUES (%s, %s)
    """, (str(event_uuid), test_event["user_id"]))
    
    # Check before commit (should be 0 since we're in same transaction)
    cursor.execute("SELECT COUNT(*) FROM user_state WHERE user_id = %s", (test_event["user_id"],))
    before_commit_count = cursor.fetchone()[0]
    print(f"   Before commit: {before_commit_count}")
    
    # Commit atomically
    cursor.execute("COMMIT")
    print(f"   ✅ Transaction committed")
    
    # Check after commit (should be 1)
    cursor.execute("SELECT COUNT(*) FROM user_state WHERE user_id = %s", (test_event["user_id"],))
    after_commit_count = cursor.fetchone()[0]
    print(f"   After commit: {after_commit_count}")
    print(f"   Expected: 1")
    
    atomic_commit = (after_commit_count == 1)
    print(f"   Atomic commit: {'PASS' if atomic_commit else 'FAIL'}")
    
    # Debug: Check what was actually inserted
    cursor.execute("SELECT mastery FROM user_state WHERE user_id = %s", (test_event["user_id"],))
    mastery_row = cursor.fetchone()
    print(f"   Inserted mastery: {mastery_row[0] if mastery_row else 'None'}")
    
    # Test 3: Verify idempotency
    print(f"\n📋 Test 3: Idempotency verification")
    
    # Try to process same event again
    cursor.execute("BEGIN")
    
    # Check processed_events
    cursor.execute("""
        SELECT 1 FROM processed_events 
        WHERE event_id = %s 
        FOR UPDATE
    """, (event_id,))
    
    already_processed = cursor.fetchone() is not None
    print(f"   Event already processed: {'YES' if already_processed else 'NO'}")
    
    cursor.execute("ROLLBACK")
    
    idempotency_holds = already_processed
    print(f"   Idempotency: {'PASS' if idempotency_holds else 'FAIL'}")
    
    # Cleanup
    cursor = conn.cursor()
    cursor.execute("DELETE FROM processed_events WHERE event_id = %s", (event_id,))
    cursor.execute("DELETE FROM user_state WHERE user_id = %s", (test_event["user_id"],))
    cursor.execute("COMMIT")
    cursor.close()
    
    # Overall result
    all_tests_pass = learner_pure and atomic_commit and idempotency_holds
    
    print(f"\n🎯 LEARNER PURITY RESULTS")
    print("=" * 50)
    print(f"✅ Learner purity: {'PASS' if learner_pure else 'FAIL'}")
    print(f"✅ Atomic commit: {'PASS' if atomic_commit else 'FAIL'}")
    print(f"✅ Idempotency: {'PASS' if idempotency_holds else 'FAIL'}")
    print(f"\n🏆 OVERALL: {'ALL TESTS PASS' if all_tests_pass else 'SOME TESTS FAIL'}")
    
    return all_tests_pass

def test_learner_determinism():
    """
    Test that learner produces same result for same input
    """
    print(f"\n🧪 TESTING LEARNER DETERMINISM")
    print("=" * 50)
    
    # Setup
    db_store = PostgresInteractionStore()
    conn = db_store._get_connection()
    engine = LearningLoopEngine()
    
    # Create test event
    test_event = {
        "event_id": str(uuid.uuid4()),
        "user_id": "test-user-determinism",
        "event_type": "task_submitted",  # Use supported event type
        "concept": "test_concept",
        "reward": 0.1
    }
    
    # Apply learner multiple times
    results = []
    for i in range(3):
        cursor = conn.cursor()
        result = engine.apply_event(test_event, cursor)
        results.append(result)
        cursor.close()
        
        print(f"   Run {i+1}: {result.get('type', 'unknown')}")
    
    # Check determinism
    all_same = all(
        r.get("state_json") == results[0].get("state_json") 
        for r in results
    )
    
    print(f"   Deterministic results: {'YES' if all_same else 'NO'}")
    
    return all_same

def main():
    """
    Test learner purity and determinism
    """
    print("🔒 LEARNER PURITY & DETERMINISM TESTS")
    print("=" * 60)
    
    try:
        # Test 1: Learner purity
        test1 = test_learner_no_independent_commits()
        
        # Test 2: Learner determinism
        test2 = test_learner_determinism()
        
        print(f"\n🎯 FINAL PURITY RESULTS")
        print("=" * 50)
        print(f"✅ Learner Purity: {'PASS' if test1 else 'FAIL'}")
        print(f"✅ Learner Determinism: {'PASS' if test2 else 'FAIL'}")
        
        if test1 and test2:
            print(f"\n🏆 LEARNER INVARIANTS ESTABLISHED")
            print(f"✅ Learners are pure functions")
            print(f"✅ No independent commits")
            print(f"✅ Deterministic behavior")
            print(f"✅ Ready for mathematical learning guarantees")
        else:
            print(f"\n❌ LEARNER INVARIANTS VIOLATED")
            print(f"❌ Not ready for learning integration")
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
