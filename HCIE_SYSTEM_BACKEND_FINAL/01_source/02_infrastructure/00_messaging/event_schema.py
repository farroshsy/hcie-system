"""
Event Schema Management with Avro Support
Provides versioning and serialization for event schemas
"""

import json
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class SchemaVersion(str, Enum):
    """Event schema version enumeration"""
    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"
    CURRENT = V1_0

@dataclass
class EventMetadata:
    """Event metadata for versioning and tracking"""
    event_id: str
    event_type: str
    version: str
    timestamp: datetime
    source: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class EventSchema:
    """Event schema manager with versioning support"""
    
    def __init__(self):
        self.schemas = {}
        self._register_default_schemas()
    
    def _register_default_schemas(self):
        """Register default event schemas"""
        # Task events
        self.register_schema("task_generated", {
            "type": "record",
            "name": "TaskGeneratedEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "timestamp", "type": "string"},
                {"name": "user_id", "type": ["null", "string"]},
                {"name": "source", "type": "string"},
                {"name": "task_id", "type": "string"},
                {"name": "concept_id", "type": "string"},
                {"name": "representation", "type": "string"},
                {"name": "difficulty", "type": "double"},
                {"name": "policy_mode", "type": "string"},
                {"name": "selection_metrics", "type": {"type": "map", "values": "string"}},
                {"name": "processing_time_ms", "type": "double"}
            ]
        })
        
        self.register_schema("task_submitted", {
            "type": "record",
            "name": "TaskSubmittedEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "timestamp", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "task_id", "type": "string"},
                {"name": "concept_id", "type": "string"},
                {"name": "representation", "type": "string"},
                {"name": "answer", "type": "string"},
                {"name": "correct_answer", "type": "string"},
                {"name": "correct", "type": "boolean"},
                {"name": "response_time", "type": "double"},
                {"name": "difficulty", "type": "double"},
                {"name": "reward", "type": "double"}
            ]
        })
        
        self.register_schema("task_completed", {
            "type": "record",
            "name": "TaskCompletedEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "reward", "type": "double"},
                {"name": "task_id", "type": "string"},
                {"name": "concept", "type": "string"},
                {"name": "timestamp", "type": "string"},
                {"name": "difficulty_level", "type": "string"},
                {"name": "engagement_time", "type": "double"},
                {"name": "attempts", "type": "int"},
                {"name": "hints_used", "type": "int"},
                {"name": "version", "type": "int"}
            ]
        })
        
        # Learning events
        self.register_schema("learning_update", {
            "type": "record",
            "name": "LearningUpdateEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "timestamp", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "concept", "type": "string"},
                {"name": "mastery_before", "type": "double"},
                {"name": "mastery_after", "type": "double"},
                {"name": "mastery_delta", "type": "double"},
                {"name": "uncertainty", "type": "double"},
                {"name": "confidence", "type": "double"},
                {"name": "J_value", "type": "double"},
                {"name": "transfer_amounts", "type": {"type": "map", "values": "double"}},
                {"name": "transfer_efficiency", "type": "double"},
                {"name": "policy", "type": "string"},
                {"name": "policy_multiplier", "type": "double"},
                {"name": "zpd_target", "type": "double"},
                {"name": "zpd_alignment_error", "type": "double"},
                {"name": "zpd_score", "type": "double"},
                {"name": "processing_mode", "type": "string"}
            ]
        })
        
        # Learning interaction events (NEW)
        self.register_schema("learning_interaction", {
            "type": "record",
            "name": "LearningInteractionEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "timestamp", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "concept", "type": "string"},
                {"name": "interaction", "type": {
                    "type": "map",
                    "values": "string"
                }},
                {"name": "source", "type": "string"}
            ]
        })
        
        # Auth events
        self.register_schema("user_registered", {
            "type": "record",
            "name": "UserRegisteredEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "timestamp", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "email", "type": "string"},
                {"name": "username", "type": "string"},
                {"name": "registration_source", "type": "string"},
                {"name": "metadata", "type": {"type": "map", "values": "string"}}
            ]
        })
        
        self.register_schema("user_logged_in", {
            "type": "record",
            "name": "UserLoggedInEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "timestamp", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "session_id", "type": "string"},
                {"name": "ip_address", "type": "string"},
                {"name": "user_agent", "type": "string"},
                {"name": "login_method", "type": "string"}
            ]
        })
        
        # System events
        self.register_schema("system_health_check", {
            "type": "record",
            "name": "SystemHealthCheckEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "timestamp", "type": "string"},
                {"name": "service_name", "type": "string"},
                {"name": "status", "type": "string"},
                {"name": "metrics", "type": {"type": "map", "values": "double"}},
                {"name": "checks", "type": {"type": "map", "values": "boolean"}}
            ]
        })
    
    def register_schema(self, event_type: str, schema: Dict[str, Any]):
        """Register an event schema"""
        self.schemas[event_type] = schema
        logger.info(f"✅ Registered schema for {event_type}")
    
    def get_schema(self, event_type: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Get schema for event type and version"""
        if event_type not in self.schemas:
            raise ValueError(f"Unknown event type: {event_type}")
        
        schema = self.schemas[event_type]
        
        # TODO: Handle version-specific schemas
        if version:
            # For now, return default schema
            logger.warning(f"⚠️ Version {version} not implemented for {event_type}, using default")
        
        return schema
    
    def validate_event(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Validate event data against schema"""
        try:
            schema = self.get_schema(event_type)
            
            # Basic validation - check required fields
            required_fields = [field['name'] for field in schema['fields'] 
                              if field.get('type') != 'null' and 'default' not in field]
            
            for field_name in required_fields:
                if field_name not in event_data:
                    logger.error(f"❌ Missing required field: {field_name} for {event_type}")
                    return False
            
            # TODO: Add more sophisticated validation (type checking, etc.)
            return True
            
        except Exception as e:
            logger.error(f"❌ Validation failed for {event_type}: {e}")
            return False
    
    def serialize_event(self, event_type: str, event_data: Dict[str, Any], 
                        format: str = "json") -> Union[str, bytes]:
        """Serialize event data"""
        self.validate_event(event_type, event_data)
        
        if format == "json":
            return json.dumps(event_data, default=str)
        elif format == "avro":
            # TODO: Implement Avro serialization
            logger.warning("⚠️ Avro serialization not implemented, falling back to JSON")
            return json.dumps(event_data, default=str)
        else:
            raise ValueError(f"Unknown serialization format: {format}")
    
    def deserialize_event(self, event_type: str, serialized_data: Union[str, bytes], 
                          format: str = "json") -> Dict[str, Any]:
        """Deserialize event data"""
        if format == "json":
            return json.loads(serialized_data)
        elif format == "avro":
            # TODO: Implement Avro deserialization
            logger.warning("⚠️ Avro deserialization not implemented, falling back to JSON")
            return json.loads(serialized_data)
        else:
            raise ValueError(f"Unknown serialization format: {format}")

# Global schema manager
event_schema_manager = EventSchema()
