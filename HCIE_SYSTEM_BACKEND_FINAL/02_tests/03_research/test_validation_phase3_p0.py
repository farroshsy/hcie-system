"""
Phase 3 End-to-End Event Validation - P0: TaskAttemptSubmitted → CognitionUpdated Continuity

This script validates:
1. TaskAttemptSubmitted event is emitted with canonical contract
2. CognitionUpdated event is emitted by learning-consumer
3. Causal lineage is preserved (causation_id links events)
4. Trace propagation works (trace_id, span_id, parent_span_id)
5. Semantic continuity (cognitive state matches between events)

This validates the foundational runtime invariant: cognition continuity.
"""

import sys
import os
import json
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging.schema.canonical_events import (
    TaskAttemptSubmitted,
    LearningProcessed,
    CognitionUpdated,
    validate_event_contract,
    get_event_contract
)


def validate_canonical_contract_compliance(event_data: dict, expected_event_type: str) -> dict:
    """
    Validate that event data conforms to canonical contract.
    
    Returns:
        Dict with validation result and details
    """
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "contract": get_event_contract(expected_event_type)
    }
    
    # Check event type
    if event_data.get("event_type") != expected_event_type:
        result["errors"].append(f"Event type mismatch: expected {expected_event_type}, got {event_data.get('event_type')}")
    
    # Check schema version
    schema_version = event_data.get("schema_version")
    if not schema_version:
        result["errors"].append("Missing schema_version")
    else:
        result["warnings"].append(f"Schema version: {schema_version}")
    
    # Check required trace fields
    required_trace_fields = result["contract"].get("required_trace_fields", [])
    for field in required_trace_fields:
        if field not in event_data or event_data[field] is None:
            result["errors"].append(f"Missing required trace field: {field}")
    
    # Check ownership
    ownership = event_data.get("source_service")
    expected_ownership = result["contract"].get("owner")
    if ownership != expected_ownership:
        result["errors"].append(f"Ownership mismatch: expected {expected_ownership}, got {ownership}")
    
    # Check idempotency key
    idempotency_key = event_data.get("idempotency_key")
    if not idempotency_key:
        result["warnings"].append("Missing idempotency_key (replay safety compromised)")
    
    # Check causal lineage
    causation_id = event_data.get("causation_id")
    correlation_id = event_data.get("correlation_id")
    if expected_event_type == "TaskAttemptSubmitted":
        if causation_id is not None:
            result["warnings"].append("TaskAttemptSubmitted should not have causation_id (root event)")
    else:
        if causation_id is None:
            result["errors"].append(f"{expected_event_type} missing causation_id (causal lineage broken)")
    
    # Check trace propagation
    trace_id = event_data.get("trace_id")
    span_id = event_data.get("span_id")
    parent_span_id = event_data.get("parent_span_id")
    
    if not trace_id:
        result["errors"].append("Missing trace_id (OTel continuity broken)")
    if not span_id:
        result["errors"].append("Missing span_id (OTel continuity broken)")
    
    result["valid"] = len(result["errors"]) == 0
    return result


def validate_causal_lineage(
    task_attempt_event: dict,
    cognition_updated_event: dict
) -> dict:
    """
    Validate causal lineage between TaskAttemptSubmitted and CognitionUpdated.
    
    Returns:
        Dict with validation result and details
    """
    result = {
        "valid": False,
        "errors": [],
        "warnings": []
    }
    
    # Check trace_id continuity
    task_trace_id = task_attempt_event.get("trace_id")
    cognition_trace_id = cognition_updated_event.get("trace_id")
    
    if task_trace_id != cognition_trace_id:
        result["errors"].append(f"Trace ID discontinuity: {task_trace_id} != {cognition_trace_id}")
    
    # Check causation_id linkage
    task_event_id = task_attempt_event.get("event_id")
    cognition_causation_id = cognition_updated_event.get("causation_id")
    
    if cognition_causation_id != task_event_id:
        result["errors"].append(f"Causation ID mismatch: expected {task_event_id}, got {cognition_causation_id}")
    
    # Check correlation_id continuity
    task_correlation_id = task_attempt_event.get("correlation_id")
    cognition_correlation_id = cognition_updated_event.get("correlation_id")
    
    if task_correlation_id != cognition_correlation_id:
        result["warnings"].append(f"Correlation ID mismatch: {task_correlation_id} != {cognition_correlation_id}")
    
    # Check span hierarchy
    task_span_id = task_attempt_event.get("span_id")
    cognition_parent_span_id = cognition_updated_event.get("parent_span_id")
    
    if cognition_parent_span_id != task_span_id:
        result["warnings"].append(f"Span hierarchy broken: expected parent {task_span_id}, got {cognition_parent_span_id}")
    
    result["valid"] = len(result["errors"]) == 0
    return result


def validate_semantic_continuity(
    task_attempt_event: dict,
    cognition_updated_event: dict
) -> dict:
    """
    Validate semantic continuity between TaskAttemptSubmitted and CognitionUpdated.
    
    This checks that the cognitive state in CognitionUpdated is consistent
    with the attempt in TaskAttemptSubmitted.
    
    Returns:
        Dict with validation result and details
    """
    result = {
        "valid": False,
        "errors": [],
        "warnings": []
    }
    
    # Check user_id continuity
    task_user_id = task_attempt_event.get("user_id")
    cognition_user_id = cognition_updated_event.get("user_id")
    
    if task_user_id != cognition_user_id:
        result["errors"].append(f"User ID discontinuity: {task_user_id} != {cognition_user_id}")
    
    # Check concept_id continuity
    task_concept_id = task_attempt_event.get("concept_id")
    cognition_concept_id = cognition_updated_event.get("concept_id")
    
    if task_concept_id != cognition_concept_id:
        result["errors"].append(f"Concept ID discontinuity: {task_concept_id} != {cognition_concept_id}")
    
    # Check that CognitionUpdated has ensemble mastery (cognitive state)
    ensemble_mastery = cognition_updated_event.get("ensemble_mastery")
    if ensemble_mastery is None:
        result["errors"].append("Missing ensemble_mastery in CognitionUpdated")
    elif not (0.0 <= ensemble_mastery <= 1.0):
        result["errors"].append(f"Invalid ensemble_mastery: {ensemble_mastery} (must be 0-1)")
    
    # Check that CognitionUpdated has ensemble uncertainty
    ensemble_uncertainty = cognition_updated_event.get("ensemble_uncertainty")
    if ensemble_uncertainty is None:
        result["errors"].append("Missing ensemble_uncertainty in CognitionUpdated")
    elif ensemble_uncertainty < 0:
        result["errors"].append(f"Invalid ensemble_uncertainty: {ensemble_uncertainty} (must be >= 0)")
    
    # Check that CognitionUpdated has learner state (lyapunov, bayesian, kalman)
    lyapunov_mastery = cognition_updated_event.get("lyapunov_mastery")
    bayesian_mastery = cognition_updated_event.get("bayesian_mastery")
    kalman_mastery = cognition_updated_event.get("kalman_mastery")
    
    if lyapunov_mastery is None and bayesian_mastery is None and kalman_mastery is None:
        result["errors"].append("Missing all learner mastery values in CognitionUpdated")
    
    result["valid"] = len(result["errors"]) == 0
    return result


def print_validation_result(result: dict, title: str):
    """Print validation result in a formatted way."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {'✅ VALID' if result['valid'] else '❌ INVALID'}")
    
    if result.get("contract"):
        print(f"Contract: {result['contract']}")
    
    if result["errors"]:
        print(f"\nErrors ({len(result['errors'])}):")
        for error in result["errors"]:
            print(f"  ❌ {error}")
    
    if result["warnings"]:
        print(f"\nWarnings ({len(result['warnings'])}):")
        for warning in result["warnings"]:
            print(f"  ⚠️  {warning}")
    
    print(f"{'='*60}\n")


def main():
    """
    Main validation function.
    
    This would typically:
    1. Submit a real task attempt via RuntimeCoordinator
    2. Capture TaskAttemptSubmitted event from outbox
    3. Wait for learning-consumer to process
    4. Capture CognitionUpdated event from learning_analytics topic
    5. Validate both events and their relationship
    """
    print("🔥 Phase 3 End-to-End Event Validation - P0")
    print("TaskAttemptSubmitted → CognitionUpdated Continuity")
    print("="*60)
    
    # TODO: This is a placeholder for the actual validation
    # The real implementation would:
    # 1. Set up test environment with Kafka, PostgreSQL, learning-consumer
    # 2. Submit a task attempt via RuntimeCoordinator
    # 3. Capture events from outbox and Kafka
    # 4. Validate events against canonical contracts
    # 5. Validate causal lineage
    # 6. Validate semantic continuity
    
    print("\n⏳ Validation setup required:")
    print("  - Running Kafka cluster")
    print("  - Running PostgreSQL with outbox pattern")
    print("  - Running learning-consumer")
    print("  - RuntimeCoordinator with outbox integration")
    print("\n📝 This is a validation framework. Actual validation requires:")
    print("  1. Test environment setup")
    print("  2. Event capture from outbox/Kafka")
    print("  3. Full end-to-end flow execution")
    
    # Example validation with mock data (for demonstration)
    print("\n" + "="*60)
    print("MOCK VALIDATION (for demonstration)")
    print("="*60)
    
    # Mock TaskAttemptSubmitted event
    mock_task_attempt = {
        "event_type": "TaskAttemptSubmitted",
        "schema_version": "1.0",
        "event_id": "task-attempt-001",
        "trace_id": "trace-123",
        "span_id": "span-001",
        "parent_span_id": None,
        "causation_id": None,
        "correlation_id": "corr-123",
        "source_service": "runtime_coordinator",
        "event_timestamp": datetime.utcnow(),
        "emitted_at": datetime.utcnow(),
        "idempotency_key": "user-001-session-001-task-001",
        "user_id": "user-001",
        "session_id": "session-001",
        "task_id": "task-001",
        "attempt_id": "attempt-001",
        "concept_id": "concept-001",
        "user_answer": "answer",
        "correct_answer": "correct",
        "is_correct": True,
        "response_time_ms": 5000.0,
        "task_difficulty": 0.5,
        "task_metadata": {},
        "session_context": {}
    }
    
    # Mock CognitionUpdated event
    mock_cognition_updated = {
        "event_type": "CognitionUpdated",
        "schema_version": "1.0",
        "event_id": "cognition-001",
        "trace_id": "trace-123",
        "span_id": "span-002",
        "parent_span_id": "span-001",
        "causation_id": "task-attempt-001",
        "correlation_id": "corr-123",
        "source_service": "learning_consumer",
        "event_timestamp": datetime.utcnow(),
        "emitted_at": datetime.utcnow(),
        "idempotency_key": "user-001-concept-001-timestamp",
        "user_id": "user-001",
        "concept_id": "concept-001",
        "lyapunov_mastery": 0.7,
        "bayesian_mastery": 0.6,
        "kalman_mastery": 0.8,
        "ensemble_mastery": 0.7,
        "ensemble_uncertainty": 0.1,
        "bandit_alpha": 10.0,
        "bandit_beta": 5.0,
        "bandit_selected": True,
        "zpd_lower": 0.4,
        "zpd_upper": 0.9
    }
    
    # Validate TaskAttemptSubmitted
    task_validation = validate_canonical_contract_compliance(mock_task_attempt, "TaskAttemptSubmitted")
    print_validation_result(task_validation, "TaskAttemptSubmitted Validation")
    
    # Validate CognitionUpdated
    cognition_validation = validate_canonical_contract_compliance(mock_cognition_updated, "CognitionUpdated")
    print_validation_result(cognition_validation, "CognitionUpdated Validation")
    
    # Validate causal lineage
    lineage_validation = validate_causal_lineage(mock_task_attempt, mock_cognition_updated)
    print_validation_result(lineage_validation, "Causal Lineage Validation")
    
    # Validate semantic continuity
    semantic_validation = validate_semantic_continuity(mock_task_attempt, mock_cognition_updated)
    print_validation_result(semantic_validation, "Semantic Continuity Validation")
    
    # Overall result
    all_valid = all([
        task_validation["valid"],
        cognition_validation["valid"],
        lineage_validation["valid"],
        semantic_validation["valid"]
    ])
    
    print("="*60)
    print(f"OVERALL RESULT: {'✅ ALL VALIDATIONS PASSED' if all_valid else '❌ VALIDATIONS FAILED'}")
    print("="*60)
    
    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
