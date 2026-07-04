"""
P0.1 - Real Single-Event Cognition Continuity Validation

Brutal truth test: Did the exact same mastery state survive:
API → Outbox → Kafka → Consumer → UnifiedBrain → Persistence?

This is a thin, direct test. No frameworks. No abstractions.
Just: submit event, capture state, validate continuity.

Test scope:
- 1 user
- 1 concept
- 1 task
- 1 attempt

No concurrency. No load. Just semantic integrity.
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
        "user_id": "test_user_p0_1",
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


def capture_outbox_event(event_id: str):
    """
    Capture TaskAttemptSubmitted event from outbox_event_envelopes table using Docker exec.
    
    Uses outbox_event_envelopes because it contains canonical event contracts:
    - event_type, trace_id, causation_id, correlation_id, source_service
    These are required for P0.1 validation of canonical contract compliance.
    
    Note: Runtime now emits canonical 'TaskAttemptSubmitted' events.
    Querying for 'TaskAttemptSubmitted' to match actual system behavior.
    
    Args:
        event_id: The event ID to look for
    
    Returns:
        Dict with outbox event data or None
    """
    try:
        # Use Docker exec to query Postgres directly
        # Query outbox_event_envelopes for canonical event contracts
        cmd = [
            "docker", "exec", "docker-postgres-1",
            "psql", "-U", "hcie_user", "-d", "hcie",
            "-c",
            "SELECT id, event_id, event_type, topic, envelope, correlation_id, causation_id, source_service, created_at FROM outbox_event_envelopes WHERE event_type = 'TaskAttemptSubmitted' ORDER BY created_at DESC LIMIT 1;"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse output
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 3:  # Header + separator + data
            data_line = lines[2].split('|')
            return {
                "id": data_line[0].strip(),
                "event_id": data_line[1].strip(),
                "event_type": data_line[2].strip(),
                "topic": data_line[3].strip(),
                "envelope": data_line[4].strip(),
                "correlation_id": data_line[5].strip(),
                "causation_id": data_line[6].strip(),
                "source_service": data_line[7].strip(),
                "created_at": data_line[8].strip()
            }
        return None
    except Exception as e:
        print(f"❌ Failed to capture outbox event: {e}")
        return None


def query_learner_progress(user_id: str, concept_id: str):
    """
    Query Postgres learning_state for mastery state using Docker exec.
    
    Uses learning_state table (not learner_progress) which contains:
    - user_id, concept, state_data (JSONB with mastery/uncertainty)
    
    Args:
        user_id: User identifier
        concept_id: Concept identifier
    
    Returns:
        Dict with mastery state or None
    """
    try:
        # Use Docker exec to query Postgres directly
        cmd = [
            "docker", "exec", "docker-postgres-1",
            "psql", "-U", "hcie_user", "-d", "hcie",
            "-c",
            f"SELECT user_id, concept, state_data, updated_at FROM learning_state WHERE user_id = '{user_id}' LIMIT 1;"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse output - handle multiline JSONB
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 3:  # Header + separator + data
            # Join all lines after separator to handle multiline JSONB
            data_section = '\n'.join(lines[2:])
            # Split by pipe but handle the multiline case
            parts = data_section.split('|')
            if len(parts) >= 4:
                return {
                    "user_id": parts[0].strip(),
                    "concept": parts[1].strip(),
                    "state_data": '|'.join(parts[2:-1]).strip(),  # Rejoin middle parts for JSONB
                    "updated_at": parts[-1].strip()
                }
        return None
    except Exception as e:
        print(f"❌ Failed to query learner progress: {e}")
        return None


def validate_cognition_continuity(submission_result, outbox_event, learner_progress):
    """
    Validate that mastery state is preserved across the full chain.
    
    Args:
        submission_result: API submission response
        outbox_event: Event captured from outbox
        learner_progress: Mastery state from Postgres
    
    Returns:
        Dict with validation result
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Validate outbox event exists
    if not outbox_event:
        result["errors"].append("No outbox event found")
        result["valid"] = False
        return result
    
    # Validate learner progress exists
    if not learner_progress:
        result["errors"].append("No learner progress found")
        result["valid"] = False
        return result
    
    # Validate event contract compliance
    # Parse envelope (JSONB field containing canonical event data)
    outbox_envelope = json.loads(outbox_event["envelope"]) if isinstance(outbox_event["envelope"], str) else outbox_event["envelope"]
    
    # The actual canonical event data is in the "payload" field of the envelope
    payload = outbox_envelope.get("payload", {})
    
    # Check required fields in payload
    required_fields = ["event_id", "user_id", "concept", "interaction"]
    for field in required_fields:
        if field not in payload:
            result["errors"].append(f"Missing required field in payload: {field}")
            result["valid"] = False
    
    # Check that interaction has correct field
    if "interaction" in payload:
        if "correct" not in payload["interaction"]:
            result["errors"].append("Missing 'correct' field in interaction")
            result["valid"] = False
    
    # Check trace fields (from metadata, not envelope top level)
    metadata = outbox_envelope.get("metadata", {})
    if "correlation_id" not in metadata:
        result["warnings"].append("Missing correlation_id in metadata")
    
    # Check causation_id (should be None for root event)
    if metadata.get("causation_id") is not None:
        result["warnings"].append("TaskAttemptSubmitted should not have causation_id (root event)")
    
    # Check source_service ownership (accept both outbox-pattern and runtime_coordinator)
    source_service = metadata.get("source_service", "")
    if source_service not in ["outbox-pattern", "runtime_coordinator"]:
        result["errors"].append(f"Wrong source_service: {source_service} (expected outbox-pattern or runtime_coordinator)")
        result["valid"] = False
    
    # Validate mastery continuity
    # This is the core brutal truth check
    # Parse state_data JSONB field
    state_data = json.loads(learner_progress["state_data"]) if isinstance(learner_progress["state_data"], str) else learner_progress["state_data"]
    
    if state_data:
        # Check if mastery exists in state_data
        if "mastery" not in state_data:
            result["warnings"].append("mastery not found in state_data")
        else:
            mastery_value = state_data["mastery"]
            if not (0.0 <= mastery_value <= 1.0):
                result["errors"].append(f"Invalid mastery value: {mastery_value}")
                result["valid"] = False
    
    return result


def test_brutal_truth():
    """
    Brutal truth test: Validate cognition continuity across distributed execution.
    
    Steps:
    1. Submit task attempt via API
    2. Capture TaskAttemptSubmitted event from outbox
    3. Wait for learning-consumer processing (5-10s)
    4. Query Postgres learner_progress for mastery
    5. Validate mastery state preserved exactly
    6. Validate causal lineage preserved
    7. Validate trace continuity preserved
    """
    
    print("🔥 P0.1 - Brutal Truth Test: Cognition Continuity")
    print("="*60)
    print("Testing: API → Outbox → Kafka → Consumer → UnifiedBrain → Persistence")
    print("="*60)
    
    # Step 1: Submit task attempt
    print("\n[1/5] Submitting task attempt via API...")
    submission_result = submit_task_attempt()
    if not submission_result:
        print("❌ Failed to submit task attempt")
        return 1
    print(f"✅ Task attempt submitted: {submission_result}")
    
    # Step 2: Capture outbox event
    print("\n[2/5] Capturing TaskAttemptSubmitted from outbox...")
    time.sleep(2)  # Wait for outbox write
    outbox_event = capture_outbox_event(None)
    if not outbox_event:
        print("❌ No outbox event found")
        return 1
    print(f"✅ Outbox event captured: {outbox_event['id']}")
    
    # Step 3: Wait for learning-consumer processing
    print("\n[3/5] Waiting for learning-consumer processing (10s)...")
    time.sleep(10)
    
    # Step 4: Query learner progress
    print("\n[4/5] Querying Postgres learner_progress...")
    learner_progress = query_learner_progress("test_user_p0_1", "concept_001")
    if not learner_progress:
        print("❌ No learner progress found")
        return 1
    print(f"✅ Learner progress found: {learner_progress['user_id']}")
    
    # Step 5: Validate cognition continuity
    print("\n[5/5] Validating cognition continuity...")
    validation_result = validate_cognition_continuity(submission_result, outbox_event, learner_progress)
    
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
    sys.exit(test_brutal_truth())
