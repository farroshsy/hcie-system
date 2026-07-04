#!/usr/bin/env python3
"""
Cross-Layer Invariant Validators
Ensures schema, database, and application layers are perfectly aligned
"""

import uuid
import re
import time
from datetime import datetime
from typing import Any, List, Dict

class CrossLayerValidators:
    """
    Validators that enforce consistency across all system layers
    Schema validation = Database constraints = Application invariants
    """
    
    @staticmethod
    def is_valid_uuid(value: Any) -> bool:
        """Validate UUID format (matches database UUID type)"""
        if not isinstance(value, str):
            return False
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def is_valid_timestamp(value: Any) -> bool:
        """Validate timestamp format (matches database timestamp type)"""
        if not isinstance(value, str):
            return False
        try:
            # Try ISO 8601 format
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return True
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def is_valid_reward(value: Any) -> bool:
        """Validate reward range (matches database constraint)"""
        if not isinstance(value, (int, float)):
            return False
        return 0.0 <= value <= 1.0
    
    @staticmethod
    def is_valid_event_type(value: Any) -> bool:
        """Validate event type enum (matches database enum)"""
        if not isinstance(value, str):
            return False
        valid_types = ["task_submitted", "task_completed", "concept_mastered", "hint_requested", "task_abandoned"]
        return value in valid_types
    
    @staticmethod
    def is_valid_difficulty_level(value: Any) -> bool:
        """Validate difficulty level enum"""
        if not isinstance(value, str):
            return False
        valid_levels = ["easy", "medium", "hard"]
        return value in valid_levels
    
    @staticmethod
    def is_valid_engagement_time(value: Any) -> bool:
        """Validate engagement time constraints"""
        if not isinstance(value, (int, float)):
            return False
        return 0 <= value <= 3600  # Max 1 hour
    
    @staticmethod
    def is_valid_user_id(value: Any) -> bool:
        """Validate user_id format (matches database constraints)"""
        if not isinstance(value, str):
            return False
        # Alphanumeric + underscore, 1-100 chars
        return bool(re.match(r'^[a-zA-Z0-9_]{1,100}$', value))
    
    @staticmethod
    def is_valid_task_id(value: Any) -> bool:
        """Validate task_id format"""
        if not isinstance(value, str):
            return False
        # Alphanumeric + underscore + dash + dot, 1-100 chars (allow version numbers like 0.5)
        return bool(re.match(r'^[a-zA-Z0-9_.-]{1,100}$', value))
    
    @staticmethod
    def is_valid_concept(value: Any) -> bool:
        """Validate concept format (ct_* pattern)"""
        if not isinstance(value, str):
            return False
        return bool(re.match(r'^ct_[a-z_]{1,50}$', value))
    
    @staticmethod
    def validate_task_id(value: Any) -> List[str]:
        """Validate task_id format"""
        errors = []
        if not CrossLayerValidators.is_valid_task_id(value):
            errors.append(f"task_id must be alphanumeric/dash/underscore/dot (1-100 chars), got: {value}")
        return errors
    
    @staticmethod
    def validate_concept_field(value: Any) -> List[str]:
        """Validate concept format"""
        errors = []
        if not CrossLayerValidators.is_valid_concept(value):
            errors.append(f"concept must match ct_* pattern, got: {value}")
        return errors
    
    @staticmethod
    def validate_event_type_field(value: Any) -> List[str]:
        """Validate event type enum"""
        errors = []
        if not CrossLayerValidators.is_valid_event_type(value):
            errors.append(f"event_type must be valid enum, got: {value}")
        return errors
    
    @staticmethod
    def validate_event_id(value: Any, field_name: str = "event_id") -> List[str]:
        """Cross-layer event_id validation"""
        errors = []
        if not CrossLayerValidators.is_valid_uuid(value):
            errors.append(f"{field_name} must be valid UUID, got: {value} (type: {type(value).__name__})")
        return errors
    
    @staticmethod
    def validate_timestamp_field(value: Any, field_name: str = "timestamp") -> List[str]:
        """Cross-layer timestamp validation"""
        errors = []
        if not CrossLayerValidators.is_valid_timestamp(value):
            errors.append(f"{field_name} must be valid ISO 8601 timestamp, got: {value}")
        return errors
    
    @staticmethod
    def validate_reward_field(value: Any, field_name: str = "reward") -> List[str]:
        """Cross-layer reward validation"""
        errors = []
        if not CrossLayerValidators.is_valid_reward(value):
            errors.append(f"{field_name} must be number between 0.0 and 1.0, got: {value}")
        return errors
    
    @staticmethod
    def validate_user_id_field(value: Any, field_name: str = "user_id") -> List[str]:
        """Cross-layer user_id validation"""
        errors = []
        if not CrossLayerValidators.is_valid_user_id(value):
            errors.append(f"{field_name} must be alphanumeric/underscore (1-100 chars), got: {value}")
        return errors
    
    @staticmethod
    def validate_cross_layer_invariants(event: Dict[str, Any]) -> List[str]:
        """
        Validate all cross-layer invariants for an event
        This ensures schema = database = application consistency
        """
        errors = []
        
        # Core identity fields (must match database exactly)
        errors.extend(CrossLayerValidators.validate_event_id(event.get("event_id")))
        errors.extend(CrossLayerValidators.validate_user_id_field(event.get("user_id")))
        errors.extend(CrossLayerValidators.validate_task_id(event.get("task_id")))
        errors.extend(CrossLayerValidators.validate_concept_field(event.get("concept")))
        
        # Data integrity fields
        errors.extend(CrossLayerValidators.validate_timestamp_field(event.get("timestamp")))
        errors.extend(CrossLayerValidators.validate_reward_field(event.get("reward")))
        errors.extend(CrossLayerValidators.validate_event_type_field(event.get("event_type")))
        
        # V2 specific fields
        if event.get("version", 1) >= 2:
            if "difficulty_level" in event:
                if not CrossLayerValidators.is_valid_difficulty_level(event["difficulty_level"]):
                    errors.append(f"difficulty_level must be easy/medium/hard, got: {event['difficulty_level']}")
            
            if "engagement_time" in event:
                if not CrossLayerValidators.is_valid_engagement_time(event["engagement_time"]):
                    errors.append(f"engagement_time must be 0-3600 seconds, got: {event['engagement_time']}")
        
        return errors

# Convenience functions
def validate_uuid(value: Any) -> List[str]:
    return CrossLayerValidators.validate_event_id(value)

def validate_timestamp(value: Any) -> List[str]:
    return CrossLayerValidators.validate_timestamp_field(value)

def validate_cross_layer_consistency(event: Dict[str, Any]) -> List[str]:
    return CrossLayerValidators.validate_cross_layer_invariants(event)
