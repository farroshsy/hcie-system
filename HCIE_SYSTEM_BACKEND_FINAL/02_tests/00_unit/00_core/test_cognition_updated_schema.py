"""
Test CognitionUpdated event schema with Phase 1 fields

This test verifies that the CognitionUpdated event contains all required fields
for Phase 1 trajectory recording.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from messaging.schema.canonical_events import CognitionUpdated


def test_cognition_updated_schema_with_phase1_fields():
    """Test that CognitionUpdated event accepts all Phase 1 required fields"""
    print("🧪 Testing CognitionUpdated schema with Phase 1 fields...")
    
    # Create a sample CognitionUpdated event with all Phase 1 fields
    event_data = {
        "schema_version": "1.0",
        "event_type": "CognitionUpdated",
        "source_service": "learning_consumer",
        "event_timestamp": datetime.utcnow(),
        "emitted_at": datetime.utcnow(),
        "event_id": "cognition_001",
        "interaction_id": "attempt_001",
        "user_id": "user_001",
        "concept_id": "concept_001",
        "interaction_number": 1,
        "state_before": {
            "mastery": 0.3,
            "uncertainty": 0.2,
            "ensemble_mastery": 0.3
        },
        "state_after": {
            "mastery": 0.5,
            "uncertainty": 0.15,
            "ensemble_mastery": 0.5,
            "lyapunov_mastery": 0.48,
            "bayesian_mastery": 0.52,
            "kalman_mastery": 0.50
        },
        "governance_snapshot": {
            "jt_value": 0.25,
            "jt_weights": {"w1": 0.4, "w2": 0.2, "w3": 0.1, "w4": 0.1, "w5": 0.2},
            "jt_components": {"delta_m": 0.2, "transfer": 0.1, "cost": 0.05, "uncertainty": 0.03, "zpd": 0.15},
            "jt_volatility": 0.1,
            "exploration_pressure": 0.5,
            "stability_index": 0.8,
            "ensemble_weights": {"lyapunov": 0.33, "bayesian": 0.33, "kalman": 0.34},
            "learner_contributions": {"lyapunov": 0.16, "bayesian": 0.17, "kalman": 0.17}
        },
        "experiment_run_id": "exp_run_001",
        "transfer_sources": ["concept_000"],
        "transfer_amounts": {"concept_000": 0.1},
        "transfer_efficiency": 0.8,
        "action_selected": "concept_001",
        "action_distribution": {"concept_001": 0.7, "concept_002": 0.3},
        "lyapunov_mastery": 0.48,
        "bayesian_mastery": 0.52,
        "kalman_mastery": 0.50,
        "ensemble_mastery": 0.5,
        "ensemble_uncertainty": 0.15,
        "bandit_alpha": 5.0,
        "bandit_beta": 2.0,
        "bandit_selected": True,
        "zpd_lower": 0.3,
        "zpd_upper": 0.7,
        "trace_id": "trace_001",
        "span_id": "span_001",
        "parent_span_id": None,
        "causation_id": "attempt_001_processed",
        "correlation_id": "trace_001",
        "experiment_id": "exp_001",
        "policy_version": "v1.0.0",
        "cohort_id": "cohort_001",
        "assignment_hash": "hash_001",
        "idempotency_key": "user_001_concept_001_001"
    }
    
    event = CognitionUpdated(**event_data)
    assert event.event_id == "cognition_001"
    assert event.interaction_id == "attempt_001"
    assert event.user_id == "user_001"
    assert event.concept_id == "concept_001"
    assert event.interaction_number == 1
    assert event.experiment_run_id == "exp_run_001"
    assert event.state_before == {"mastery": 0.3, "uncertainty": 0.2, "ensemble_mastery": 0.3}
    assert event.state_after["mastery"] == 0.5
    assert "jt_value" in event.governance_snapshot
    assert event.transfer_sources == ["concept_000"]
    assert event.action_selected == "concept_001"


def test_required_fields_present():
    """Test that all required Phase 1 fields are present in schema"""
    print("\n🧪 Testing required Phase 1 fields...")
    
    required_fields = [
        "event_id",
        "interaction_id",
        "event_timestamp",
        "emitted_at",
        "state_before",
        "state_after",
        "governance_snapshot",
        "experiment_run_id"
    ]
    
    # Get the schema fields
    schema_fields = CognitionUpdated.__fields__.keys()
    
    missing_fields = []
    for field in required_fields:
        if field not in schema_fields:
            missing_fields.append(field)
    
    assert not missing_fields, f"Missing required Phase 1 fields: {missing_fields}"


def test_optional_fields_present():
    """Test that optional Phase 1 fields are present in schema"""
    print("\n🧪 Testing optional Phase 1 fields...")
    
    optional_fields = [
        "interaction_number",
        "transfer_sources",
        "transfer_amounts",
        "transfer_efficiency",
        "action_selected",
        "action_distribution"
    ]
    
    # Get the schema fields
    schema_fields = CognitionUpdated.__fields__.keys()
    
    missing_fields = []
    for field in optional_fields:
        if field not in schema_fields:
            missing_fields.append(field)
    
    assert not missing_fields, f"Missing optional Phase 1 fields: {missing_fields}"


if __name__ == "__main__":
    print("="*60)
    print("CognitionUpdated Phase 1 Schema Validation")
    print("="*60)
    
    # Run tests
    test1 = test_required_fields_present()
    test2 = test_optional_fields_present()
    test3 = test_cognition_updated_schema_with_phase1_fields()
    
    print("\n" + "="*60)
    if test1 and test2 and test3:
        print("✅ All tests passed - CognitionUpdated schema ready for Phase 1")
    else:
        print("❌ Some tests failed - schema needs fixes")
    print("="*60)
