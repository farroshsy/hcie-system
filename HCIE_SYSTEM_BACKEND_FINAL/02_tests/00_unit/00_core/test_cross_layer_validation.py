#!/usr/bin/env python3
"""
Test Cross-Layer Validation and Safety Classification
Demonstrates improved validation flow and fix safety
"""

import json
import uuid
import time
from kafka import KafkaProducer

def create_invalid_uuid_event():
    """Create event with invalid UUID (should fail cross-layer validation)"""
    return {
        "event_id": "invalid-uuid-format",
        "user_id": "cross_layer_test_1",
        "event_type": "task_submitted",
        "reward": 0.6,
        "task_id": "cross_layer_task_1",
        "concept": "ct_algorithm",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": 2,
        "difficulty_level": "medium",
        "engagement_time": 45
    }

def create_invalid_reward_event():
    """Create event with invalid reward (should fail cross-layer validation)"""
    return {
        "event_id": str(uuid.uuid4()),
        "user_id": "cross_layer_test_2",
        "event_type": "task_submitted",
        "reward": 1.5,  # Invalid: > 1.0
        "task_id": "cross_layer_task_2",
        "concept": "ct_decomposition",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": 2,
        "difficulty_level": "hard",
        "engagement_time": 60
    }

def create_safe_fixable_event():
    """Create event that needs safe fixes (missing UUID/timestamp)"""
    return {
        "user_id": "cross_layer_test_3",
        "event_type": "task_submitted",
        "reward": 0.7,
        "task_id": "cross_layer_task_3",
        "concept": "ct_algorithm",
        # Missing event_id and timestamp (safe to fix)
        "version": 2,
        "difficulty_level": "medium",
        "engagement_time": 30
    }

def create_risky_fixable_event():
    """Create event that needs risky fixes (event type normalization)"""
    return {
        "event_id": str(uuid.uuid4()),
        "user_id": "cross_layer_test_4",
        "event_type": "submit",  # Needs normalization (risky)
        "reward": 0.8,
        "task_id": "cross_layer_task_4",
        "concept": "ct_decomposition",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": 2,
        "difficulty_level": "easy",
        "engagement_time": 25
    }

def test_cross_layer_validation():
    """Test cross-layer validation locally"""
    print("🧪 Testing Cross-Layer Validation...")
    
    try:
        from schema.cross_layer_validators import validate_cross_layer_consistency
        
        # Test invalid UUID
        invalid_uuid_event = create_invalid_uuid_event()
        uuid_errors = validate_cross_layer_consistency(invalid_uuid_event)
        print(f"❌ Invalid UUID errors: {uuid_errors}")
        
        # Test invalid reward
        invalid_reward_event = create_invalid_reward_event()
        reward_errors = validate_cross_layer_consistency(invalid_reward_event)
        print(f"❌ Invalid reward errors: {reward_errors}")
        
        # Test valid event
        valid_event = create_safe_fixable_event()
        valid_event["event_id"] = str(uuid.uuid4())
        valid_event["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        valid_errors = validate_cross_layer_consistency(valid_event)
        print(f"✅ Valid event errors: {valid_errors}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cross-layer validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fix_safety():
    """Test fix safety classification"""
    print("\n🧪 Testing Fix Safety Classification...")
    
    try:
        from schema.fix_safety import classify_fix_safety, should_auto_apply_fix
        
        # Test safe fix
        safe_context = {"missing_fields": ["event_id", "timestamp"]}
        safe_classification = classify_fix_safety("missing_required_fields", safe_context)
        safe_auto_apply = should_auto_apply_fix("missing_required_fields", safe_context)
        print(f"✅ Safe fix: {safe_classification['level'].value} (confidence: {safe_classification['confidence']})")
        print(f"   Auto-apply: {safe_auto_apply}")
        
        # Test risky fix
        risky_context = {"event_type": "submit"}
        risky_classification = classify_fix_safety("invalid_event_type", risky_context)
        risky_auto_apply = should_auto_apply_fix("invalid_event_type", risky_context)
        print(f"⚠️ Risky fix: {risky_classification['level'].value} (confidence: {risky_classification['confidence']})")
        print(f"   Auto-apply: {risky_auto_apply}")
        
        # Test manual fix
        manual_context = {}
        manual_classification = classify_fix_safety("schema_validation_failed", manual_context)
        manual_auto_apply = should_auto_apply_fix("schema_validation_failed", manual_context)
        print(f"🔒 Manual fix: {manual_classification['level'].value} (confidence: {manual_classification['confidence']})")
        print(f"   Auto-apply: {manual_auto_apply}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fix safety test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_cross_layer_test_events():
    """Send events to test cross-layer validation in production"""
    print("\n📤 Sending cross-layer validation test events...")
    
    producer = KafkaProducer(
        bootstrap_servers='kafka:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )
    
    test_events = [
        ("invalid_uuid", create_invalid_uuid_event()),
        ("invalid_reward", create_invalid_reward_event()),
        ("safe_fixable", create_safe_fixable_event()),
        ("risky_fixable", create_risky_fixable_event())
    ]
    
    for name, event in test_events:
        future = producer.send('user-interactions', key=f'cross_layer_{name}', value=event)
        meta = future.get(timeout=10)
        print(f'📤 {name} sent to partition {meta.partition} offset {meta.offset}')
    
    producer.close()
    print("✅ Cross-layer test events sent - watch consumer and DLQ replay worker")

if __name__ == "__main__":
    try:
        # Test locally first
        validation_success = test_cross_layer_validation()
        safety_success = test_fix_safety()
        
        if validation_success and safety_success:
            # Send events to test production
            send_cross_layer_test_events()
            print("\n🎉 Cross-layer validation test complete!")
            print("📊 Watch consumer logs for cross-layer validation failures")
            print("🔧 Watch DLQ replay worker for safe/risky fix classifications")
        else:
            print("\n❌ Local tests failed - not sending production events")
    
    except Exception as e:
        print(f"❌ Cross-layer validation test failed: {e}")
        import traceback
        traceback.print_exc()
