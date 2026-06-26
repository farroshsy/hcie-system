"""
Canonical State Schema Freeze - Phase E1.4

Versioned canonical cognition contracts for Tier1 state.
Ensures migration-controlled, replay-compatible, backward-readable schemas.

Required before P4/P5 to prevent replay evolution breakage.
"""

from typing import Dict, Any, Set, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class SchemaVersion(Enum):
    """Canonical cognition schema versions"""
    V1_0 = "1.0"  # Initial canonical schema (P3 baseline)
    # Future versions will be added here with migration paths


@dataclass
class CanonicalFieldDefinition:
    """Definition of a canonical cognitive field"""
    name: str
    field_type: str  # 'float', 'int', 'str', 'bool', 'dict'
    required: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""
    
    def validate(self, value: Any) -> bool:
        """
        Validate a value against this field definition.
        
        Args:
            value: Value to validate
            
        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return not self.required
        
        # Type validation
        if self.field_type == 'float':
            if not isinstance(value, (int, float)):
                return False
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        elif self.field_type == 'int':
            if not isinstance(value, int):
                return False
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        elif self.field_type == 'str':
            if not isinstance(value, str):
                return False
        elif self.field_type == 'bool':
            if not isinstance(value, bool):
                return False
        elif self.field_type == 'dict':
            if not isinstance(value, dict):
                return False
        
        return True


@dataclass
class CanonicalSchema:
    """Canonical cognition schema for a specific version"""
    version: SchemaVersion
    tier1_fields: Dict[str, CanonicalFieldDefinition] = field(default_factory=dict)
    tier2_fields: Dict[str, CanonicalFieldDefinition] = field(default_factory=dict)
    
    def validate_tier1_state(self, state: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate Tier1 canonical state against this schema.
        
        Args:
            state: State to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check all required Tier1 fields are present
        for field_name, field_def in self.tier1_fields.items():
            if field_name not in state:
                if field_def.required:
                    errors.append(f"Missing required Tier1 field: {field_name}")
            else:
                if not field_def.validate(state[field_name]):
                    errors.append(f"Invalid Tier1 field {field_name}: {state[field_name]}")
        
        return len(errors) == 0, errors
    
    def validate_tier2_state(self, state: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate Tier2 runtime control state against this schema.
        
        Args:
            state: State to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Tier2 fields are optional (informational only)
        for field_name, field_def in self.tier2_fields.items():
            if field_name in state:
                if not field_def.validate(state[field_name]):
                    errors.append(f"Invalid Tier2 field {field_name}: {state[field_name]}")
        
        return len(errors) == 0, errors


class CanonicalSchemaRegistry:
    """
    Registry of canonical cognition schemas with version support.
    
    Provides:
    - Schema validation for current version
    - Migration paths between versions
    - Backward compatibility checking
    """
    
    def __init__(self):
        self.schemas: Dict[SchemaVersion, CanonicalSchema] = {}
        self.current_version: SchemaVersion = SchemaVersion.V1_0
        self._initialize_schemas()
    
    def _initialize_schemas(self):
        """Initialize all canonical schemas"""
        # Version 1.0 - P3 baseline schema
        v1_0 = CanonicalSchema(
            version=SchemaVersion.V1_0,
            tier1_fields={
                'mastery': CanonicalFieldDefinition(
                    name='mastery',
                    field_type='float',
                    required=True,
                    min_value=0.0,
                    max_value=1.0,
                    description='Core cognitive mastery level'
                ),
                'uncertainty': CanonicalFieldDefinition(
                    name='uncertainty',
                    field_type='float',
                    required=True,
                    min_value=0.0,
                    max_value=1.0,
                    description='Cognitive uncertainty estimate'
                ),
                'zpd_score': CanonicalFieldDefinition(
                    name='zpd_score',
                    field_type='float',
                    required=True,
                    min_value=0.0,
                    max_value=1.0,
                    description='Zone of Proximal Development score'
                ),
                'bayesian_alpha': CanonicalFieldDefinition(
                    name='bayesian_alpha',
                    field_type='float',
                    required=True,
                    min_value=0.0,
                    description='Bayesian alpha parameter (success count)'
                ),
                'bayesian_beta': CanonicalFieldDefinition(
                    name='bayesian_beta',
                    field_type='float',
                    required=True,
                    min_value=0.0,
                    description='Bayesian beta parameter (failure count)'
                ),
                'kalman_mastery': CanonicalFieldDefinition(
                    name='kalman_mastery',
                    field_type='float',
                    required=True,
                    min_value=0.0,
                    max_value=1.0,
                    description='Kalman filter mastery estimate'
                ),
                'kalman_covariance': CanonicalFieldDefinition(
                    name='kalman_covariance',
                    field_type='float',
                    required=True,
                    min_value=0.0,
                    description='Kalman filter covariance estimate'
                ),
                'lyapunov_mastery': CanonicalFieldDefinition(
                    name='lyapunov_mastery',
                    field_type='float',
                    required=True,
                    min_value=0.0,
                    max_value=1.0,
                    description='Lyapunov stability mastery'
                )
            },
            tier2_fields={
                'J_value': CanonicalFieldDefinition(
                    name='J_value',
                    field_type='float',
                    required=False,
                    min_value=0.0,
                    description='Control-theoretic cost function value'
                ),
                'adaptive_rate': CanonicalFieldDefinition(
                    name='adaptive_rate',
                    field_type='float',
                    required=False,
                    min_value=0.0,
                    max_value=1.0,
                    description='Adaptive learning rate'
                )
            }
        )
        
        self.schemas[SchemaVersion.V1_0] = v1_0
    
    def get_current_schema(self) -> CanonicalSchema:
        """Get the current canonical schema"""
        return self.schemas[self.current_version]
    
    def validate_tier1_state(self, state: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate Tier1 state against current schema.
        
        Args:
            state: State to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        schema = self.get_current_schema()
        return schema.validate_tier1_state(state)
    
    def validate_tier2_state(self, state: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate Tier2 state against current schema.
        
        Args:
            state: State to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        schema = self.get_current_schema()
        return schema.validate_tier2_state(state)
    
    def get_tier1_field_names(self) -> Set[str]:
        """Get all Tier1 canonical field names"""
        schema = self.get_current_schema()
        return set(schema.tier1_fields.keys())
    
    def get_tier2_field_names(self) -> Set[str]:
        """Get all Tier2 runtime control field names"""
        schema = self.get_current_schema()
        return set(schema.tier2_fields.keys())
    
    def serialize_schema(self, version: SchemaVersion = None) -> str:
        """
        Serialize a schema to JSON for documentation/migration.
        
        Args:
            version: Schema version to serialize (defaults to current)
            
        Returns:
            JSON string representation
        """
        if version is None:
            version = self.current_version
        
        schema = self.schemas[version]
        
        def field_def_to_dict(field_def: CanonicalFieldDefinition) -> Dict[str, Any]:
            return {
                'name': field_def.name,
                'field_type': field_def.field_type,
                'required': field_def.required,
                'min_value': field_def.min_value,
                'max_value': field_def.max_value,
                'description': field_def.description
            }
        
        schema_dict = {
            'version': version.value,
            'tier1_fields': {k: field_def_to_dict(v) for k, v in schema.tier1_fields.items()},
            'tier2_fields': {k: field_def_to_dict(v) for k, v in schema.tier2_fields.items()},
            'frozen_at': datetime.utcnow().isoformat()
        }
        
        return json.dumps(schema_dict, indent=2)


# Global schema registry instance
_canonical_schema_registry = CanonicalSchemaRegistry()


def get_canonical_schema_registry() -> CanonicalSchemaRegistry:
    """Get the global canonical schema registry"""
    return _canonical_schema_registry


def validate_canonical_state(state: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate canonical cognitive state against current schema.
    
    Convenience function for quick validation.
    
    Args:
        state: State to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    registry = get_canonical_schema_registry()
    
    tier1_valid, tier1_errors = registry.validate_tier1_state(state)
    tier2_valid, tier2_errors = registry.validate_tier2_state(state)
    
    all_errors = tier1_errors + tier2_errors
    return tier1_valid and tier2_valid, all_errors


def get_tier1_fields() -> Set[str]:
    """Get Tier1 canonical field names"""
    registry = get_canonical_schema_registry()
    return registry.get_tier1_field_names()


def get_tier2_fields() -> Set[str]:
    """Get Tier2 runtime control field names"""
    registry = get_canonical_schema_registry()
    return registry.get_tier2_field_names()
