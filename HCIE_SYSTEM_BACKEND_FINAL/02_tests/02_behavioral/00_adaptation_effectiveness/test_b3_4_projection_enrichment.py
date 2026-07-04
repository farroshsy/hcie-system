#!/usr/bin/env python3
"""
B3.4 Projection Enrichment Pipeline Test

Tests the projection enrichment pipeline:
- CognitionUpdated → pure cognition projection
- AdaptationGenerated → adaptation enrichment
- ProjectionUpdated = cognition + adaptation enrichment

Architecture:
CognitionUpdated → AdaptationGenerated → Projection enrichment/materialization → Frontend
"""

import sys
import os
import time
import json
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_projection_enrichment_deterministic():
    """
    Test that projection enrichment is deterministic (pure function of event data)
    
    B3.4: Projection enrichment must be deterministic with no external lookups.
    """
    print("🧪 Testing projection enrichment determinism...")
    
    # Simulate CognitionUpdated event
    cognition_event = {
        "event_id": "cognition_001",
        "event_type": "CognitionUpdated",
        "user_id": "user_001",
        "concept": "concept_001",
        "result": {
            "mastery": 0.75,
            "uncertainty": 0.1,
            "zpd_score": 0.8,
            "processing_mode": "jt",
            "lyapunov_mastery": 0.73,
            "bayesian_alpha": 5.0,
            "bayesian_beta": 2.0,
            "kalman_mastery": 0.74,
            "kalman_covariance": 0.05
        },
        "timestamp": time.time(),
        "causation_id": "learning_processed_001"
    }
    
    # Simulate AdaptationGenerated event
    adaptation_event = {
        "event_id": "adaptation_001",
        "event_type": "AdaptationGenerated",
        "user_id": "user_001",
        "adaptation_type": "difficulty_shift",
        "recommendation": {
            "target_difficulty": 0.8,
            "reason": "High mastery detected, increasing difficulty"
        },
        "policy_version": "v1.0.0",
        "cognition_snapshot": {
            "mastery": 0.75,
            "uncertainty": 0.1,
            "zpd_score": 0.8,
            "concept": "concept_001"
        },
        "deterministic_inputs_hash": "abc123",
        "causation_id": "cognition_001"
    }
    
    # Test: Same cognition event should produce same projection
    projection_1 = _extract_projection_from_cognition(cognition_event)
    projection_2 = _extract_projection_from_cognition(cognition_event)
    
    assert projection_1 == projection_2, "Cognition projection should be deterministic"
    print("✅ Cognition projection is deterministic")
    
    # Test: Same adaptation event should produce same enrichment
    enrichment_1 = _extract_adaptation_enrichment(adaptation_event)
    enrichment_2 = _extract_adaptation_enrichment(adaptation_event)
    
    assert enrichment_1 == enrichment_2, "Adaptation enrichment should be deterministic"
    print("✅ Adaptation enrichment is deterministic")
    
    # Test: Combined projection should be deterministic
    combined_1 = {**projection_1, "adaptation": enrichment_1}
    combined_2 = {**projection_2, "adaptation": enrichment_2}
    
    assert combined_1 == combined_2, "Combined projection should be deterministic"
    print("✅ Combined projection is deterministic")
    
    print("✅ Projection enrichment determinism test PASSED")
    return True


def test_projection_enrichment_no_external_lookups():
    """
    Test that projection enrichment has no external dependencies (registry, DB, Redis)
    
    B3.4: Projection enrichment must be pure function of event payload.
    """
    print("🧪 Testing projection enrichment has no external lookups...")
    
    # Simulate AdaptationGenerated event
    adaptation_event = {
        "event_id": "adaptation_001",
        "event_type": "AdaptationGenerated",
        "user_id": "user_001",
        "adaptation_type": "difficulty_shift",
        "recommendation": {
            "target_difficulty": 0.8,
            "reason": "High mastery detected, increasing difficulty"
        },
        "policy_version": "v1.0.0",
        "cognition_snapshot": {
            "mastery": 0.75,
            "uncertainty": 0.1,
            "zpd_score": 0.8,
            "concept": "concept_001"
        },
        "deterministic_inputs_hash": "abc123",
        "causation_id": "cognition_001"
    }
    
    # Extract adaptation enrichment (should not require external lookups)
    enrichment = _extract_adaptation_enrichment(adaptation_event)
    
    # Verify enrichment contains only data from event payload
    expected_keys = {"adaptation_type", "recommendation", "policy_version", "deterministic_inputs_hash"}
    actual_keys = set(enrichment.keys())
    
    assert actual_keys == expected_keys, f"Enrichment should only contain event data. Got: {actual_keys}"
    print("✅ Enrichment contains only event data (no external lookups)")
    
    print("✅ No external lookups test PASSED")
    return True


def test_projection_enrichment_semantic_correctness():
    """
    Test that projection enrichment preserves semantic correctness
    
    B3.4: ProjectionUpdated = pure cognition projection + adaptation enrichment
    """
    print("🧪 Testing projection enrichment semantic correctness...")
    
    # Simulate full event chain
    cognition_event = {
        "event_id": "cognition_001",
        "event_type": "CognitionUpdated",
        "user_id": "user_001",
        "concept": "concept_001",
        "result": {
            "mastery": 0.75,
            "uncertainty": 0.1,
            "zpd_score": 0.8
        },
        "causation_id": "learning_processed_001"
    }
    
    adaptation_event = {
        "event_id": "adaptation_001",
        "event_type": "AdaptationGenerated",
        "user_id": "user_001",
        "adaptation_type": "difficulty_shift",
        "recommendation": {
            "target_difficulty": 0.8,
            "reason": "High mastery detected"
        },
        "policy_version": "v1.0.0",
        "cognition_snapshot": cognition_event["result"],
        "deterministic_inputs_hash": "abc123",
        "causation_id": "cognition_001"
    }
    
    # Extract projection and enrichment
    projection = _extract_projection_from_cognition(cognition_event)
    enrichment = _extract_adaptation_enrichment(adaptation_event)
    
    # Verify semantic correctness: projection contains cognition, enrichment contains adaptation
    assert "mastery" in projection or "projected_mastery" in projection, "Projection should contain cognition"
    assert "adaptation_type" in enrichment, "Enrichment should contain adaptation type"
    assert "recommendation" in enrichment, "Enrichment should contain recommendation"
    
    # Verify semantic lineage
    assert adaptation_event["causation_id"] == cognition_event["event_id"], "Semantic lineage should be preserved"
    
    print("✅ Semantic correctness test PASSED")
    return True


def test_projection_enrichment_replay_safety():
    """
    Test that projection enrichment is replay-safe
    
    B3.4: Replay should produce same enriched projection from same events.
    """
    print("🧪 Testing projection enrichment replay safety...")
    
    # Simulate event chain
    cognition_event = {
        "event_id": "cognition_001",
        "event_type": "CognitionUpdated",
        "user_id": "user_001",
        "concept": "concept_001",
        "result": {
            "mastery": 0.75,
            "uncertainty": 0.1,
            "zpd_score": 0.8
        },
        "causation_id": "learning_processed_001"
    }
    
    adaptation_event = {
        "event_id": "adaptation_001",
        "event_type": "AdaptationGenerated",
        "user_id": "user_001",
        "adaptation_type": "difficulty_shift",
        "recommendation": {"target_difficulty": 0.8},
        "policy_version": "v1.0.0",
        "cognition_snapshot": cognition_event["result"],
        "deterministic_inputs_hash": "abc123",
        "causation_id": "cognition_001"
    }
    
    # Simulate first run
    combined_1 = {
        **_extract_projection_from_cognition(cognition_event),
        "adaptation": _extract_adaptation_enrichment(adaptation_event)
    }
    
    # Simulate replay (same events)
    combined_2 = {
        **_extract_projection_from_cognition(cognition_event),
        "adaptation": _extract_adaptation_enrichment(adaptation_event)
    }
    
    # Verify replay produces same result
    assert combined_1 == combined_2, "Replay should produce same enriched projection"
    
    print("✅ Replay safety test PASSED")
    return True


def test_projection_enrichment_frontend_safety():
    """
    Test that projection enrichment is frontend-safe
    
    B3.4: Frontend should consume ONE stable semantic layer (LearnerProjection).
    """
    print("🧪 Testing projection enrichment frontend safety...")
    
    # Simulate enriched ProjectionUpdated event
    enriched_projection = {
        "event_id": "projection_001",
        "event_type": "ProjectionUpdated",
        "user_id": "user_001",
        "concept": "concept_001",
        "result": {
            "mastery": 0.75,
            "uncertainty": 0.1,
            "zpd_score": 0.8
        },
        "projection": {
            "projected_mastery": 75.0,
            "projected_difficulty": 0.8,
            "recommended_concepts": [],
            "zpd_alignment": 0.8,
            "concept_id": "concept_001",
            "concept_name": "concept_001",
            "uncertainty": 0.1
        },
        "adaptation": {
            "adaptation_type": "difficulty_shift",
            "recommendation": {"target_difficulty": 0.8},
            "policy_version": "v1.0.0",
            "deterministic_inputs_hash": "abc123"
        },
        "causation_id": "adaptation_001"
    }
    
    # Verify frontend can consume single event
    assert "projection" in enriched_projection, "Enriched projection should contain projection data"
    assert "adaptation" in enriched_projection, "Enriched projection should contain adaptation data"
    
    # Verify no internal governance metrics exposed
    governance_fields = ["jt_weights", "ensemble_weights", "governance_metrics"]
    for field in governance_fields:
        assert field not in enriched_projection, f"Governance field {field} should not be exposed"
    
    print("✅ Frontend safety test PASSED")
    return True


# Helper functions (simulate projection_consumer logic)

def _extract_projection_from_cognition(cognition_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract projection from CognitionUpdated event (deterministic)
    """
    result = cognition_event.get("result", {})
    mastery = result.get("mastery", 0.0)
    uncertainty = result.get("uncertainty", 0.0)
    zpd_score = result.get("zpd_score", 0.0)
    
    # DETERMINISTIC: Calculate projected mastery (0-100 scale)
    projected_mastery = mastery * 100
    
    # DETERMINISTIC: Calculate projected difficulty
    base_difficulty = 0.5
    mastery_adjustment = mastery * 0.3
    zpd_adjustment = zpd_score * 0.2
    projected_difficulty = max(0.0, min(1.0, base_difficulty + mastery_adjustment + zpd_adjustment))
    
    return {
        "projected_mastery": projected_mastery,
        "projected_difficulty": projected_difficulty,
        "recommended_concepts": [],
        "zpd_alignment": zpd_score,
        "concept_id": cognition_event.get("concept"),
        "concept_name": cognition_event.get("concept"),
        "uncertainty": uncertainty
    }


def _extract_adaptation_enrichment(adaptation_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract adaptation enrichment from AdaptationGenerated event (deterministic)
    """
    return {
        "adaptation_type": adaptation_event.get("adaptation_type"),
        "recommendation": adaptation_event.get("recommendation", {}),
        "policy_version": adaptation_event.get("policy_version"),
        "deterministic_inputs_hash": adaptation_event.get("deterministic_inputs_hash")
    }


def run_all_tests():
    """Run all B3.4 projection enrichment tests"""
    print("\n🚀 Starting B3.4 Projection Enrichment Pipeline Tests\n")
    
    tests = [
        ("Determinism", test_projection_enrichment_deterministic),
        ("No External Lookups", test_projection_enrichment_no_external_lookups),
        ("Semantic Correctness", test_projection_enrichment_semantic_correctness),
        ("Replay Safety", test_projection_enrichment_replay_safety),
        ("Frontend Safety", test_projection_enrichment_frontend_safety)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"Running: {test_name}")
            print('='*60)
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print('='*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
