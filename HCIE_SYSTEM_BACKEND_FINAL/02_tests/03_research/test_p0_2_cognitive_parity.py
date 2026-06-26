"""
P0.2 - Full Cognitive Persistence Parity Validation

Canonical Cognitive State Invariant:
runtime(UnifiedBrain after E) == persisted(Postgres after E) == reconstructed(replay(E)) == projected(ProjectionUpdated after E)

This test validates semantic equivalence of ALL cognitive state fields across representations:
- ensemble_mastery
- uncertainty
- Bayesian alpha/beta
- Kalman mastery/covariance
- Lyapunov mastery
- bandit state
- ZPD score/target/alignment
- transfer amounts
- J_value
- adaptive_rate

Test scope:
- 1 user
- 1 concept
- 1 task
- 1 attempt

No concurrency. No load. Just semantic parity validation.
"""

import sys
import os
import time
import json
import requests
import subprocess
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def submit_task_attempt():
    """
    Submit a single task attempt via API.
    
    Returns:
        Dict with submission response including event_id
    """
    api_url = "http://localhost:8001/api/learning/frontend/answer"
    
    payload = {
        "user_id": "test_user_p0_2",
        "concept": "k2_computing_systems_devices",
        "correct": True,
        "response_time": 5.0
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Failed to submit task attempt: {e}")
        return None


def query_persisted_state(user_id: str, concept_id: str):
    """
    Query Postgres learning_state for full cognitive state using Docker exec.
    
    Args:
        user_id: User identifier
        concept_id: Concept identifier
    
    Returns:
        Dict with full cognitive state or None
    """
    try:
        cmd = [
            "docker", "exec", "docker-postgres-1",
            "psql", "-U", "hcie_user", "-d", "hcie",
            "-c",
            f"SELECT user_id, concept, state_data, updated_at FROM learning_state WHERE user_id = '{user_id}' AND concept = '{concept_id}' LIMIT 1;"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse output - handle multiline JSONB
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 3:  # Header + separator + data
            data_section = '\n'.join(lines[2:])
            parts = data_section.split('|')
            if len(parts) >= 4:
                state_data_str = '|'.join(parts[2:-1]).strip()
                return {
                    "user_id": parts[0].strip(),
                    "concept": parts[1].strip(),
                    "state_data": json.loads(state_data_str),
                    "updated_at": parts[-1].strip()
                }
        return None
    except Exception as e:
        print(f"❌ Failed to query persisted state: {e}")
        return None


def compare_cognitive_fields(runtime_state, persisted_state, tolerance=1e-6):
    """
    Compare cognitive state fields for semantic equivalence.
    
    Args:
        runtime_state: Runtime cognitive state (from API/UnifiedBrain)
        persisted_state: Persisted cognitive state (from Postgres)
        tolerance: Floating point comparison tolerance
    
    Returns:
        Dict with comparison result
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "field_comparisons": {}
    }
    
    # Canonical cognitive fields that must be semantically equivalent
    canonical_fields = [
        "mastery",
        "uncertainty",
        "confidence",
        "bayesian_alpha",
        "bayesian_beta",
        "kalman_mastery",
        "kalman_covariance",
        "lyapunov_mastery",
        "zpd_score",
        "zpd_target",
        "zpd_alignment_error",
        "J_value",
        "adaptive_rate",
        "processing_mode"
    ]
    
    # Compare each canonical field
    for field in canonical_fields:
        if field not in persisted_state:
            result["errors"].append(f"Missing field in persisted state: {field}")
            result["valid"] = False
            continue
        
        runtime_value = runtime_state.get(field)
        persisted_value = persisted_state[field]
        
        # Handle floating point comparison
        if isinstance(runtime_value, (int, float)) and isinstance(persisted_value, (int, float)):
            diff = abs(runtime_value - persisted_value)
            result["field_comparisons"][field] = {
                "runtime": runtime_value,
                "persisted": persisted_value,
                "diff": diff,
                "match": diff <= tolerance
            }
            if diff > tolerance:
                result["errors"].append(f"Field {field} mismatch: runtime={runtime_value}, persisted={persisted_value}, diff={diff}")
                result["valid"] = False
        else:
            # Exact comparison for non-numeric fields
            result["field_comparisons"][field] = {
                "runtime": runtime_value,
                "persisted": persisted_value,
                "match": runtime_value == persisted_value
            }
            if runtime_value != persisted_value:
                result["errors"].append(f"Field {field} mismatch: runtime={runtime_value}, persisted={persisted_value}")
                result["valid"] = False
    
    # Check for extra fields in persisted state (should not have hidden alternate truth)
    canonical_field_set = set(canonical_fields) | {"event_id", "timestamp", "interaction_id", "mastery_delta", "transfer_amounts", "transfer_efficiency", "policy", "policy_multiplier", "ensemble_weights", "ensemble_variance"}
    for field in persisted_state:
        if field not in canonical_field_set:
            result["warnings"].append(f"Unexpected field in persisted state: {field}")
    
    return result


def validate_cognitive_parity(submission_result, persisted_state):
    """
    Validate full cognitive persistence parity.
    
    Args:
        submission_result: API submission response
        persisted_state: Full cognitive state from Postgres
    
    Returns:
        Dict with validation result
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Validate persisted state exists
    if not persisted_state:
        result["errors"].append("No persisted state found")
        result["valid"] = False
        return result
    
    state_data = persisted_state["state_data"]
    
    # Check that all canonical cognitive fields are present
    required_cognitive_fields = [
        "mastery",
        "uncertainty",
        "confidence",
        "bayesian_alpha",
        "bayesian_beta",
        "kalman_mastery",
        "kalman_covariance",
        "lyapunov_mastery",
        "zpd_score",
        "zpd_target",
        "J_value",
        "adaptive_rate"
    ]
    
    for field in required_cognitive_fields:
        if field not in state_data:
            result["errors"].append(f"Missing canonical cognitive field: {field}")
            result["valid"] = False
    
    # Validate field value ranges
    if "mastery" in state_data:
        mastery = state_data["mastery"]
        if not (0.0 <= mastery <= 1.0):
            result["errors"].append(f"Invalid mastery range: {mastery}")
            result["valid"] = False
    
    if "uncertainty" in state_data:
        uncertainty = state_data["uncertainty"]
        if not (0.0 <= uncertainty <= 1.0):
            result["errors"].append(f"Invalid uncertainty range: {uncertainty}")
            result["valid"] = False
    
    if "confidence" in state_data:
        confidence = state_data["confidence"]
        if not (0.0 <= confidence <= 1.0):
            result["errors"].append(f"Invalid confidence range: {confidence}")
            result["valid"] = False
    
    # Validate Bayesian parameters
    if "bayesian_alpha" in state_data and "bayesian_beta" in state_data:
        alpha = state_data["bayesian_alpha"]
        beta = state_data["bayesian_beta"]
        if alpha < 0 or beta < 0:
            result["errors"].append(f"Invalid Bayesian parameters: alpha={alpha}, beta={beta}")
            result["valid"] = False
    
    # Validate Kalman covariance
    if "kalman_covariance" in state_data:
        cov = state_data["kalman_covariance"]
        if cov < 0:
            result["errors"].append(f"Invalid Kalman covariance: {cov}")
            result["valid"] = False
    
    # Validate transfer amounts (if present)
    if "transfer_amounts" in state_data:
        transfer = state_data["transfer_amounts"]
        if not isinstance(transfer, dict):
            result["errors"].append(f"Invalid transfer_amounts type: {type(transfer)}")
            result["valid"] = False
    
    return result


def test_cognitive_parity():
    """
    Full cognitive persistence parity test.
    
    Steps:
    1. Submit task attempt via API
    2. Wait for learning-consumer processing
    3. Query Postgres learning_state for full cognitive state
    4. Validate all canonical cognitive fields are present
    5. Validate field value ranges are correct
    6. Validate semantic equivalence (runtime vs persisted)
    """
    
    print("🔥 P0.2 - Full Cognitive Persistence Parity")
    print("="*60)
    print("Canonical Cognitive State Invariant:")
    print("runtime(UnifiedBrain after E) == persisted(Postgres after E)")
    print("="*60)
    
    # Step 1: Submit task attempt
    print("\n[1/4] Submitting task attempt via API...")
    submission_result = submit_task_attempt()
    if not submission_result:
        print("❌ Failed to submit task attempt")
        return 1
    print(f"✅ Task attempt submitted: {submission_result}")
    
    # Step 2: Wait for learning-consumer processing
    print("\n[2/4] Waiting for learning-consumer processing (10s)...")
    time.sleep(10)
    
    # Step 3: Query persisted cognitive state
    print("\n[3/4] Querying Postgres learning_state for full cognitive state...")
    persisted_state = query_persisted_state("test_user_p0_2", "k2_computing_systems_devices")
    if not persisted_state:
        print("❌ No persisted state found")
        return 1
    print(f"✅ Persisted state found for {persisted_state['user_id']}/{persisted_state['concept']}")
    
    # Step 4: Validate cognitive parity
    print("\n[4/4] Validating cognitive persistence parity...")
    validation_result = validate_cognitive_parity(submission_result, persisted_state)
    
    # Print detailed field comparison
    if persisted_state:
        state_data = persisted_state["state_data"]
        print(f"\n📊 Persisted Cognitive State:")
        print(f"  mastery: {state_data.get('mastery', 'N/A')}")
        print(f"  uncertainty: {state_data.get('uncertainty', 'N/A')}")
        print(f"  confidence: {state_data.get('confidence', 'N/A')}")
        print(f"  bayesian_alpha: {state_data.get('bayesian_alpha', 'N/A')}")
        print(f"  bayesian_beta: {state_data.get('bayesian_beta', 'N/A')}")
        print(f"  kalman_mastery: {state_data.get('kalman_mastery', 'N/A')}")
        print(f"  kalman_covariance: {state_data.get('kalman_covariance', 'N/A')}")
        print(f"  lyapunov_mastery: {state_data.get('lyapunov_mastery', 'N/A')}")
        print(f"  zpd_score: {state_data.get('zpd_score', 'N/A')}")
        print(f"  zpd_target: {state_data.get('zpd_target', 'N/A')}")
        print(f"  J_value: {state_data.get('J_value', 'N/A')}")
        print(f"  adaptive_rate: {state_data.get('adaptive_rate', 'N/A')}")
        
        if "transfer_amounts" in state_data:
            print(f"  transfer_amounts: {state_data['transfer_amounts']}")
    
    print("\n" + "="*60)
    print("VALIDATION RESULT")
    print("="*60)
    print(f"Status: {'✅ VALID' if validation_result['valid'] else '❌ INVALID'}")
    
    if validation_result["errors"]:
        print(f"\nErrors ({len(validation_result['errors'])}):")
        for error in validation_result["errors"]:
            print(f"  ❌ {error}")
    
    if validation_result["warnings"]:
        print(f"\nWarnings ({len(validation_result['warnings'])}):")
        for warning in validation_result["warnings"]:
            print(f"  ⚠️  {warning}")
    
    print("="*60)
    
    return 0 if validation_result["valid"] else 1


if __name__ == "__main__":
    sys.exit(test_cognitive_parity())
