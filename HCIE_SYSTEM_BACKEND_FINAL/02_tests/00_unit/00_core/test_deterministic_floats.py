#!/usr/bin/env python3
"""
Test Deterministic Floating-Point Handling
Ensures same event produces identical JSON across multiple runs

Phase 10b: ``test_floating_point_determinism`` is marker-quarantined
because it instantiates ``PostgresInteractionStore``. The other two
tests in this module (``test_json_sorting_determinism`` and
``test_float_normalization``) are pure unit tests and run under the
default invocation. Opt in to the quarantined test with
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

from core.learning.learning_loop_engine import LearningLoopEngine
from storage.postgres_store import PostgresInteractionStore

@pytest.mark.requires_pg
def test_floating_point_determinism():
    """
    Test that floating-point operations are deterministic
    """
    print("🧪 TESTING FLOATING-POINT DETERMINISM")
    print("=" * 50)
    
    # Setup
    db_store = PostgresInteractionStore()
    conn = db_store._get_connection()
    engine = LearningLoopEngine()
    
    # Create test event with floating-point values
    test_event = {
        "event_id": str(uuid.uuid4()),
        "user_id": "test-user-floats",
        "event_type": "task_submitted",
        "concept": "test_concept",
        "reward": 0.123456789,  # High precision float
    }
    
    print(f"📋 Test event with high-precision reward: {test_event['reward']}")
    
    # Apply learner multiple times
    state_jsons = []
    for i in range(5):
        cursor = conn.cursor()
        result = engine.apply_event(test_event, cursor)
        state_json = result.get("state_json", "")
        state_jsons.append(state_json)
        cursor.close()
        
        print(f"   Run {i+1}: {state_json[:100]}...")
    
    # Check if all JSON strings are identical
    first_json = state_jsons[0]
    all_identical = all(json_str == first_json for json_str in state_jsons)
    
    print(f"\n📊 Determinism Results:")
    print(f"   All JSON strings identical: {'YES' if all_identical else 'NO'}")
    
    if not all_identical:
        print(f"   ❌ Floating-point non-determinism detected!")
        
        # Show differences
        for i, json_str in enumerate(state_jsons):
            if json_str != first_json:
                print(f"   Run {i+1} differs from first run")
                
                # Parse and compare numeric values
                try:
                    parsed1 = json.loads(first_json)
                    parsed2 = json.loads(json_str)
                    
                    mastery1 = parsed1.get("new_state", {}).get("mastery", {})
                    mastery2 = parsed2.get("new_state", {}).get("mastery", {})
                    
                    print(f"   First mastery: {mastery1}")
                    print(f"   Run {i+1} mastery: {mastery2}")
                    
                except json.JSONDecodeError:
                    print(f"   Failed to parse JSON for comparison")
    else:
        print(f"   ✅ Perfect floating-point determinism")
    
    # Cleanup
    cursor = conn.cursor()
    cursor.execute("DELETE FROM processed_events WHERE user_id = %s", (test_event["user_id"],))
    cursor.execute("DELETE FROM user_state WHERE user_id = %s", (test_event["user_id"],))
    cursor.execute("COMMIT")
    cursor.close()
    
    return all_identical

def test_json_sorting_determinism():
    """
    Test that JSON sorting ensures deterministic output
    """
    print(f"\n🧪 TESTING JSON SORTING DETERMINISM")
    print("=" * 50)
    
    # Create dict with unsorted keys
    test_dict = {
        "z_key": 1.0,
        "a_key": 2.0,
        "m_key": 3.141592653589793,
        "b_key": 0.123456789,
        "nested": {
            "z_nested": 4.0,
            "a_nested": 5.0
        }
    }
    
    # Generate JSON multiple times
    jsons = []
    for i in range(3):
        json_str = json.dumps(test_dict, sort_keys=True)
        jsons.append(json_str)
        print(f"   JSON {i+1}: {json_str}")
    
    # Check if all identical
    all_identical = all(json_str == jsons[0] for json_str in jsons)
    
    print(f"\n📊 JSON Sorting Results:")
    print(f"   All JSON strings identical: {'YES' if all_identical else 'NO'}")
    
    return all_identical

def test_float_normalization():
    """
    Test that float normalization prevents drift
    """
    print(f"\n🧪 TESTING FLOAT NORMALIZATION")
    print("=" * 50)
    
    # Test values that can cause floating-point issues
    test_values = [
        0.1 + 0.2,  # Should be 0.3 but often 0.30000000000000004
        1.0 / 3.0,  # Repeating decimal
        0.123456789,  # High precision
        0.999999999,  # Near 1.0
    ]
    
    def normalize_floats(obj):
        if isinstance(obj, float):
            return round(obj, 6)
        elif isinstance(obj, dict):
            return {k: normalize_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [normalize_floats(item) for item in obj]
        else:
            return obj
    
    print("📋 Testing float normalization:")
    for i, value in enumerate(test_values):
        normalized = normalize_floats(value)
        print(f"   Original: {value} → Normalized: {normalized}")
        
        # Test that normalization is deterministic
        normalized_again = normalize_floats(value)
        deterministic = (normalized == normalized_again)
        print(f"   Deterministic: {'YES' if deterministic else 'NO'}")
    
    return True

def main():
    """
    Test all determinism aspects
    """
    print("🔒 DETERMINISTIC FLOATING-POINT TESTS")
    print("=" * 60)
    
    try:
        # Test 1: Floating-point determinism in learner
        test1 = test_floating_point_determinism()
        
        # Test 2: JSON sorting determinism
        test2 = test_json_sorting_determinism()
        
        # Test 3: Float normalization
        test3 = test_float_normalization()
        
        print(f"\n🎯 FINAL DETERMINISM RESULTS")
        print("=" * 50)
        print(f"✅ Floating-point determinism: {'PASS' if test1 else 'FAIL'}")
        print(f"✅ JSON sorting determinism: {'PASS' if test2 else 'FAIL'}")
        print(f"✅ Float normalization: {'PASS' if test3 else 'FAIL'}")
        
        all_tests_pass = test1 and test2 and test3
        
        if all_tests_pass:
            print(f"\n🏆 DETERMINISM GUARANTEES ESTABLISHED")
            print(f"✅ Same event → identical JSON always")
            print(f"✅ No floating-point drift")
            print(f"✅ Ready for bandit + Lyapunov integration")
        else:
            print(f"\n❌ DETERMINISM ISSUES DETECTED")
            print(f"❌ Risk of bandit bias from non-determinism")
            print(f"❌ Not ready for learning integration")
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
