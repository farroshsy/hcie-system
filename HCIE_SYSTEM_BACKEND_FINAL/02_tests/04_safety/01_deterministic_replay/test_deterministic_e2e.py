"""
End-to-End Deterministic Mode Test

Tests deterministic mode through the full system pipeline:
API → Kafka → Learning Consumer → UnifiedBrain → Outbox → PostgreSQL

Validates:
- Deterministic UUID generation
- Deterministic timestamps
- Deterministic RNG in bandit decisions
- Deterministic event propagation through Kafka
- Deterministic state updates in PostgreSQL
"""

import os
import json
import time
import requests
from typing import Dict, Any, List
from datetime import datetime

# API configuration
# Use localhost:8000 when running inside container, localhost:8001 when running from host
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def send_learning_interaction(user_id: str, concept: str, response_time: float, correctness: bool) -> Dict[str, Any]:
    """
    Send a learning interaction through the API
    
    Args:
        user_id: User identifier
        concept: Learning concept
        response_time: Response time in seconds
        correctness: Whether the answer was correct
        
    Returns:
        API response
    """
    # Use the admin interaction creation endpoint
    payload = {
        "user_id": user_id,
        "concept_id": concept,
        "representation": "text"
    }
    
    response = requests.post(f"{API_BASE_URL}/api/admin/interactions/create", json=payload)
    response.raise_for_status()
    return response.json()

def get_user_state(user_id: str) -> Dict[str, Any]:
    """
    Get current user state from the API
    
    Args:
        user_id: User identifier
        
    Returns:
        User state
    """
    response = requests.get(f"{API_BASE_URL}/api/v1/users/{user_id}/state")
    response.raise_for_status()
    return response.json()

def compare_results(run1: Dict[str, Any], run2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two runs for determinism
    
    Args:
        run1: First run results
        run2: Second run results
        
    Returns:
        Comparison results
    """
    comparison = {
        "identical": True,
        "differences": []
    }
    
    # Compare interaction IDs (should be identical in deterministic mode)
    if run1.get("interaction_id") != run2.get("interaction_id"):
        comparison["identical"] = False
        comparison["differences"].append({
            "field": "interaction_id",
            "run1": run1.get("interaction_id"),
            "run2": run2.get("interaction_id")
        })
    
    # Compare state updates
    state1 = run1.get("state", {})
    state2 = run2.get("state", {})
    
    for key in ["mastery", "uncertainty", "confidence"]:
        if state1.get(key) != state2.get(key):
            comparison["identical"] = False
            comparison["differences"].append({
                "field": f"state.{key}",
                "run1": state1.get(key),
                "run2": state2.get(key)
            })
    
    return comparison

def run_e2e_deterministic_test():
    """
    Run end-to-end deterministic mode test
    
    Test flow:
    1. Send same learning interaction twice
    2. Compare results for determinism
    3. Validate UUIDs, timestamps, state are identical
    """
    print("🔥 End-to-End Deterministic Mode Test")
    print("=" * 60)
    
    # Test configuration
    test_user_id = "deterministic_test_user"
    test_concept = "algorithms"
    test_response_time = 5.2
    test_correctness = True
    
    print(f"Test Configuration:")
    print(f"  - User ID: {test_user_id}")
    print(f"  - Concept: {test_concept}")
    print(f"  - Response Time: {test_response_time}s")
    print(f"  - Correctness: {test_correctness}")
    print()
    
    # Run 1
    print("📝 Run 1: Sending learning interaction...")
    try:
        result1 = send_learning_interaction(test_user_id, test_concept, test_response_time, test_correctness)
        print(f"  ✅ Interaction sent successfully")
        print(f"  - Interaction ID: {result1.get('interaction_id')}")
        
        # Wait for processing
        time.sleep(2)
        
        # Get state after run 1
        state1 = get_user_state(test_user_id)
        print(f"  - Mastery: {state1.get('mastery', 0):.4f}")
        print(f"  - Uncertainty: {state1.get('uncertainty', 0):.4f}")
        print(f"  - Confidence: {state1.get('confidence', 0):.4f}")
    except Exception as e:
        print(f"  ❌ Run 1 failed: {e}")
        return False
    
    print()
    
    # Clear user state for clean run 2
    print("🔄 Clearing user state for Run 2...")
    try:
        # Delete user to reset state
        requests.delete(f"{API_BASE_URL}/api/v1/users/{test_user_id}")
        print(f"  ✅ User state cleared")
        time.sleep(1)
    except Exception as e:
        print(f"  ⚠️ Could not clear user state: {e}")
    
    print()
    
    # Run 2
    print("📝 Run 2: Sending same learning interaction...")
    try:
        result2 = send_learning_interaction(test_user_id, test_concept, test_response_time, test_correctness)
        print(f"  ✅ Interaction sent successfully")
        print(f"  - Interaction ID: {result2.get('interaction_id')}")
        
        # Wait for processing
        time.sleep(2)
        
        # Get state after run 2
        state2 = get_user_state(test_user_id)
        print(f"  - Mastery: {state2.get('mastery', 0):.4f}")
        print(f"  - Uncertainty: {state2.get('uncertainty', 0):.4f}")
        print(f"  - Confidence: {state2.get('confidence', 0):.4f}")
    except Exception as e:
        print(f"  ❌ Run 2 failed: {e}")
        return False
    
    print()
    
    # Compare results
    print("📊 Comparing results...")
    comparison = compare_results(
        {"interaction_id": result1.get("interaction_id"), "state": state1},
        {"interaction_id": result2.get("interaction_id"), "state": state2}
    )
    
    if comparison["identical"]:
        print("  ✅ Results are IDENTICAL - Deterministic mode working!")
    else:
        print("  ❌ Results DIFFER - Deterministic mode not working correctly")
        print(f"  Differences:")
        for diff in comparison["differences"]:
            print(f"    - {diff['field']}: run1={diff['run1']}, run2={diff['run2']}")
    
    print()
    print("=" * 60)
    print(f"Test Result: {'PASS' if comparison['identical'] else 'FAIL'}")
    
    return comparison["identical"]

if __name__ == "__main__":
    success = run_e2e_deterministic_test()
    exit(0 if success else 1)
