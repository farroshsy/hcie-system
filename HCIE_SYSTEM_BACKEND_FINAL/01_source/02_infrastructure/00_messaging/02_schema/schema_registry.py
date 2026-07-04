#!/usr/bin/env python3
"""
Schema Registry - Versioned Schema Management and Evolution
Handles schema versioning, migration, and backward compatibility
"""

import json
import logging
import os
from typing import Dict, Any, List
from enum import Enum
import time

logger = logging.getLogger(__name__)

class SchemaVersion(Enum):
    """Supported schema versions"""
    V1 = 1
    V2 = 2

class SchemaRegistry:
    """
    Centralized schema registry with version management and migration
    """
    
    def __init__(self, schema_dir: str = None):
        if schema_dir is None:
            schema_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.schema_dir = schema_dir
        self.schemas = {}
        self.migrations = {}
        self.current_version = SchemaVersion.V2
        
        # Load all schemas
        self._load_schemas()
        self._register_migrations()
        
        logger.info(f"✅ Schema Registry initialized with {len(self.schemas)} schemas")
    
    def _load_schemas(self):
        """Load all schema versions"""
        for version in SchemaVersion:
            schema_file = os.path.join(self.schema_dir, f"learning_event_schema_v{version.value}.json")
            
            if os.path.exists(schema_file):
                with open(schema_file, 'r') as f:
                    self.schemas[version] = json.load(f)
                logger.info(f"✅ Loaded schema v{version.value} from {schema_file}")
            else:
                logger.warning(f"⚠️ Schema file not found: {schema_file}")
    
    def _register_migrations(self):
        """Register schema migration functions"""
        # V1 → V2 migration
        self.migrations[(SchemaVersion.V1, SchemaVersion.V2)] = self._migrate_v1_to_v2
        
        logger.info(f"✅ Registered {len(self.migrations)} schema migrations")
    
    def get_schema(self, version: SchemaVersion = None) -> Dict[str, Any]:
        """Get schema for specific version (default: current)"""
        if version is None:
            version = self.current_version
        
        if version not in self.schemas:
            raise ValueError(f"Schema version {version.value} not found")
        
        return self.schemas[version]
    
    def validate_event(self, event: Dict[str, Any], version: SchemaVersion = None) -> Dict[str, Any]:
        """
        Validate event against specific schema version
        Returns: {"valid": bool, "errors": List[str], "event": Dict, "version": int}
        """
        if version is None:
            version = self.current_version
        
        schema = self.get_schema(version)
        errors = []
        normalized_event = event.copy()
        
        # Apply version-specific normalization FIRST
        if version == SchemaVersion.V1:
            normalized_event = self._normalize_v1(event)
        elif version == SchemaVersion.V2:
            normalized_event = self._normalize_v2(event)
        
        # Version-specific validation AFTER normalization
        if version == SchemaVersion.V1:
            errors.extend(self._validate_v1(normalized_event, schema))
        elif version == SchemaVersion.V2:
            errors.extend(self._validate_v2(normalized_event, schema))
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "event": normalized_event,
            "version": version.value
        }
    
    def detect_version(self, event: Dict[str, Any]) -> SchemaVersion:
        """
        Detect schema version of an event
        Uses explicit version field or heuristics
        """
        # Explicit version field
        if "version" in event:
            try:
                version_num = int(event["version"])
                return SchemaVersion(version_num)
            except (ValueError, KeyError):
                pass
        
        # Heuristic detection
        if "difficulty_level" in event or "engagement_time" in event:
            return SchemaVersion.V2
        else:
            return SchemaVersion.V1
    
    def migrate_event(self, event: Dict[str, Any], target_version: SchemaVersion) -> Dict[str, Any]:
        """
        Migrate event to target schema version
        Returns: {"success": bool, "event": Dict, "migration_applied": str, "errors": List[str]}
        """
        source_version = self.detect_version(event)
        
        if source_version == target_version:
            return {
                "success": True,
                "event": event,
                "migration_applied": "none",
                "errors": []
            }
        
        migration_key = (source_version, target_version)
        if migration_key not in self.migrations:
            return {
                "success": False,
                "event": event,
                "migration_applied": "none",
                "errors": [f"No migration path from v{source_version.value} to v{target_version.value}"]
            }
        
        try:
            migration_func = self.migrations[migration_key]
            migrated_event = migration_func(event.copy())
            
            # Validate migrated event
            validation = self.validate_event(migrated_event, target_version)
            
            return {
                "success": validation["valid"],
                "event": validation["event"],
                "migration_applied": f"v{source_version.value}→v{target_version.value}",
                "errors": validation["errors"]
            }
        
        except Exception as e:
            return {
                "success": False,
                "event": event,
                "migration_applied": f"v{source_version.value}→v{target_version.value}",
                "errors": [f"Migration failed: {str(e)}"]
            }
    
    def _validate_v1(self, event: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate against V1 schema"""
        errors = []
        
        # Required fields for V1
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in event:
                errors.append(f"Missing required field: {field}")
        
        # Type validation
        properties = schema.get("properties", {})
        for field, prop in properties.items():
            if field in event:
                expected_type = prop.get("type")
                if expected_type == "number" and not isinstance(event[field], (int, float)):
                    errors.append(f"Field {field} must be number, got {type(event[field]).__name__}")
                elif expected_type == "string" and not isinstance(event[field], str):
                    errors.append(f"Field {field} must be string, got {type(event[field]).__name__}")
        
        return errors
    
    def _validate_v2(self, event: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate against V2 schema"""
        errors = []
        
        # V1 validation + V2 specific fields
        errors.extend(self._validate_v1(event, schema))
        
        # V2 specific validations
        if "difficulty_level" in event:
            valid_difficulties = ["easy", "medium", "hard"]
            if event["difficulty_level"] not in valid_difficulties:
                errors.append(f"Invalid difficulty_level: {event['difficulty_level']}")
        
        if "engagement_time" in event:
            if not isinstance(event["engagement_time"], (int, float)) or event["engagement_time"] < 0:
                errors.append("engagement_time must be non-negative number")
        
        return errors
    
    def _normalize_v1(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize event to V1 schema"""
        normalized = event.copy()
        
        # Add default version
        if "version" not in normalized:
            normalized["version"] = 1
        
        # Strip whitespace from string fields
        string_fields = ["event_id", "user_id", "task_id", "concept", "event_type"]
        for field in string_fields:
            if field in normalized and isinstance(normalized[field], str):
                normalized[field] = normalized[field].strip()
        
        return normalized
    
    def _normalize_v2(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize event to V2 schema"""
        normalized = self._normalize_v1(event)  # V1 normalization + V2 defaults
        
        # Add V2 defaults
        if "version" not in normalized:
            normalized["version"] = 2
        
        if "difficulty_level" not in normalized:
            # Infer difficulty from reward if possible
            reward = normalized.get("reward", 0.5)
            if reward > 0.7:
                normalized["difficulty_level"] = "easy"
            elif reward > 0.3:
                normalized["difficulty_level"] = "medium"
            else:
                normalized["difficulty_level"] = "hard"
        
        if "engagement_time" not in normalized:
            # Default engagement time based on difficulty
            difficulty_times = {"easy": 30, "medium": 60, "hard": 120}
            difficulty = normalized.get("difficulty_level", "medium")
            normalized["engagement_time"] = difficulty_times.get(difficulty, 60)
        
        return normalized
    
    def _migrate_v1_to_v2(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate V1 event to V2 schema"""
        migrated = event.copy()
        
        # Update version
        migrated["version"] = 2
        
        # Add V2 fields with defaults/inferred values
        if "difficulty_level" not in migrated:
            reward = migrated.get("reward", 0.5)
            if reward > 0.7:
                migrated["difficulty_level"] = "easy"
            elif reward > 0.3:
                migrated["difficulty_level"] = "medium"
            else:
                migrated["difficulty_level"] = "hard"
        
        if "engagement_time" not in migrated:
            difficulty_times = {"easy": 30, "medium": 60, "hard": 120}
            difficulty = migrated.get("difficulty_level", "medium")
            migrated["engagement_time"] = difficulty_times.get(difficulty, 60)
        
        # Add migration metadata
        migrated["_schema_migration"] = {
            "from_version": 1,
            "to_version": 2,
            "migrated_at": time.time()
        }
        
        return migrated
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema registry information"""
        return {
            "current_version": self.current_version.value,
            "available_versions": [v.value for v in SchemaVersion if v in self.schemas],
            "total_schemas": len(self.schemas),
            "total_migrations": len(self.migrations),
            "schema_directory": self.schema_dir
        }

# Global schema registry instance
_registry = None

def get_schema_registry() -> SchemaRegistry:
    """Get global schema registry instance (singleton)"""
    global _registry
    if _registry is None:
        _registry = SchemaRegistry()
    return _registry

def validate_learning_event(event: Dict[str, Any], version: SchemaVersion = None) -> Dict[str, Any]:
    """Convenience function for event validation"""
    return get_schema_registry().validate_event(event, version)

def migrate_learning_event(event: Dict[str, Any], target_version: SchemaVersion = SchemaVersion.V2) -> Dict[str, Any]:
    """Convenience function for event migration"""
    return get_schema_registry().migrate_event(event, target_version)
