#!/usr/bin/env python3
"""
Shared Schema Validator for Learning Events
Used by API, consumer, and tests to ensure consistent event validation
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class LearningEventValidator:
    """
    Centralized schema validator for learning events
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize validator with schema file
        """
        if schema_path is None:
            schema_path = Path(__file__).parent / "learning_event_schema.json"
        
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict[str, Any]:
        """
        Load schema from file
        """
        try:
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            logger.info(f"✅ Loaded schema from {self.schema_path}")
            return schema
        except Exception as e:
            logger.error(f"❌ Failed to load schema from {self.schema_path}: {e}")
            raise
    
    def validate_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate event against schema
        
        Returns:
            {
                "valid": bool,
                "errors": List[str],
                "event": Dict[str, Any]  # Normalized event if valid
            }
        """
        try:
            # Basic structure validation (without jsonschema library dependency)
            validation_result = self._validate_structure(event)
            
            if not validation_result["valid"]:
                return validation_result
                
            # Return normalized event
            return {
                "valid": True,
                "errors": [],
                "event": self._normalize_event(event)
            }
            
        except Exception as e:
            logger.error(f"❌ Validation error: {e}")
            return {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "event": None
            }
    
    def _validate_structure(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate basic structure without external dependencies
        """
        errors = []
        
        # Type check
        if not isinstance(event, dict):
            errors.append(f"Event must be object, got {type(event)}")
            return {"valid": False, "errors": errors, "event": None}
        
        # Required fields
        required_fields = self.schema.get("required", [])
        missing_fields = [field for field in required_fields if field not in event]
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")
        
        # Version check (only if version is specified)
        if "version" in event:
            allowed_versions = [enum_val for enum_val in self.schema.get("properties", {}).get("version", {}).get("enum", [])]
            if allowed_versions and event["version"] not in allowed_versions:
                errors.append(f"Unsupported version: {event['version']}, allowed: {allowed_versions}")
        
        # Type checks for key fields
        properties = self.schema.get("properties", {})
        
        # event_id (string)
        if "event_id" in event:
            if not isinstance(event["event_id"], str):
                errors.append(f"event_id must be string, got {type(event['event_id'])}")
        
        # user_id (string)
        if "user_id" in event:
            if not isinstance(event["user_id"], str) or not event["user_id"].strip():
                errors.append("user_id must be non-empty string")
        
        # event_type (enum)
        if "event_type" in event:
            allowed_types = properties.get("event_type", {}).get("enum", [])
            if allowed_types and event["event_type"] not in allowed_types:
                errors.append(f"Invalid event_type: {event['event_type']}, allowed: {allowed_types}")
        
        # reward (number)
        if "reward" in event:
            if not isinstance(event["reward"], (int, float)):
                errors.append(f"reward must be number, got {type(event['reward'])}")
            else:
                reward_props = properties.get("reward", {})
                if "minimum" in reward_props and event["reward"] < reward_props["minimum"]:
                    errors.append(f"reward {event['reward']} below minimum {reward_props['minimum']}")
                if "maximum" in reward_props and event["reward"] > reward_props["maximum"]:
                    errors.append(f"reward {event['reward']} above maximum {reward_props['maximum']}")
        
        # task_id (string)
        if "task_id" in event:
            if not isinstance(event["task_id"], str) or not event["task_id"].strip():
                errors.append("task_id must be non-empty string")
        
        # concept (string)
        if "concept" in event:
            if not isinstance(event["concept"], str) or not event["concept"].strip():
                errors.append("concept must be non-empty string")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "event": event if len(errors) == 0 else None
        }
    
    def _normalize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize event (add defaults, clean up)
        """
        normalized = event.copy()
        
        # Add default version if missing
        if "version" not in normalized:
            default_version = self.schema.get("properties", {}).get("version", {}).get("default", 1)
            normalized["version"] = default_version
        
        # Strip whitespace from string fields
        string_fields = ["event_id", "user_id", "task_id", "concept", "event_type"]
        for field in string_fields:
            if field in normalized and isinstance(normalized[field], str):
                normalized[field] = normalized[field].strip()
        
        return normalized
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get schema information
        """
        return {
            "version": self.schema.get("version", 1),
            "required_fields": self.schema.get("required", []),
            "event_types": self.schema.get("properties", {}).get("event_type", {}).get("enum", []),
            "schema_path": str(self.schema_path)
        }

# Global validator instance
_validator = None

def get_validator() -> LearningEventValidator:
    """
    Get global validator instance (singleton)
    """
    global _validator
    if _validator is None:
        _validator = LearningEventValidator()
    return _validator

def validate_learning_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function for validation
    """
    return get_validator().validate_event(event)
