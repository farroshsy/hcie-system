#!/usr/bin/env python3
"""
Test shared schema validation
Used by API, consumer, and tests to ensure consistent event validation
"""

import sys


import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema.schema_validator import validate_learning_event, get_validator

def test_valid_event():
    """Test valid event passes validation"""
    event = {
        "version": 2,
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "user_id": "test_user",
        "event_type": "task_submitted",
        "reward": 0.85,
        "task_id": "algebra_problem_1",
        "concept": "ct_algebra",
        "timestamp": "2024-01-01T12:00:00Z",
        "difficulty_level": "medium",
        "engagement_time": 30.0
    }
    
    result = validate_learning_event(event)
    assert result["valid"] == True, f"Valid event should pass: {result['errors']}"
    assert result["event"]["version"] == 2
    print("✅ Valid event test passed")

def test_missing_required_fields():
    """Test missing required fields fail validation"""
    event = {
        "user_id": "test_user",
        "event_type": "task_submitted",
        "reward": 0.85
        # Missing event_id, task_id, concept, timestamp
    }
    
    result = validate_learning_event(event)
    assert result["valid"] == False, "Event with missing fields should fail"
    assert any("Missing required fields" in error for error in result["errors"])
    print("✅ Missing required fields test passed")

def test_invalid_reward():
    """Test invalid reward values fail validation"""
    event = {
        "version": 2,
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "user_id": "test_user",
        "event_type": "task_submitted",
        "reward": 1.5,  # Above maximum of 1.0
        "task_id": "algebra_problem_1",
        "concept": "ct_algebra",
        "timestamp": "2024-01-01T12:00:00Z",
        "difficulty_level": "medium",
        "engagement_time": 30.0
    }
    
    result = validate_learning_event(event)
    assert result["valid"] == False, "Event with invalid reward should fail"
    assert any("reward" in error and "above maximum" in error for error in result["errors"])
    print("✅ Invalid reward test passed")

def test_invalid_event_type():
    """Test invalid event type fails validation"""
    event = {
        "version": 2,
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "user_id": "test_user",
        "event_type": "invalid_event_type",
        "reward": 0.85,
        "task_id": "algebra_problem_1",
        "concept": "ct_algebra",
        "timestamp": "2024-01-01T12:00:00Z",
        "difficulty_level": "medium",
        "engagement_time": 30.0
    }
    
    result = validate_learning_event(event)
    assert result["valid"] == False, "Event with invalid type should fail"
    assert any("Invalid event_type" in error for error in result["errors"])
    print("✅ Invalid event type test passed")

def test_version_default():
    """Test version gets default value"""
    event = {
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "user_id": "test_user",
        "event_type": "task_submitted",
        "reward": 0.85,
        "task_id": "algebra_problem_1",
        "concept": "ct_algebra",
        "timestamp": "2024-01-01T12:00:00Z",
        "difficulty_level": "medium",
        "engagement_time": 30.0
        # Missing version
    }
    
    result = validate_learning_event(event)
    assert result["valid"] == True, "Event without version should get default"
    assert result["event"]["version"] == 2
    print("✅ Version default test passed")

def test_schema_info():
    """Test schema info retrieval"""
    validator = get_validator()
    info = validator.get_schema_info()
    
    assert info["version"] == 2
    assert "event_id" in info["required_fields"]
    assert "task_submitted" in info["event_types"]
    print("✅ Schema info test passed")

if __name__ == "__main__":
    print("🧪 Running schema validation tests...")
    
    try:
        test_valid_event()
        test_missing_required_fields()
        test_invalid_reward()
        test_invalid_event_type()
        test_version_default()
        test_schema_info()
        
        print("\n🎉 All schema validation tests passed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
