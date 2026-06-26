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
        self.register_schema("TaskAttemptSubmitted", {
            "type": "record",
            "name": "TaskAttemptSubmittedEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "timestamp", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "concept", "type": "string"},
                {"name": "interaction", "type": {
                    "type": "record",
                    "fields": [
                        {"name": "correct", "type": "boolean"},
                        {"name": "response_time", "type": "double"}
                    ]
                }},
                {"name": "source", "type": "string"}
            ]
        })
        
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
        
        # Learning interaction events (UX API - F-002 fix)
        # 🔥 Full canonical state with Tier1 fields for proper Kafka integration
        self.register_schema("learning_interaction", {
            "type": "record",
            "name": "LearningInteractionEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "concept", "type": "string"},
                {"name": "interaction", "type": {
                    "type": "record",
                    "fields": [
                        {"name": "correct", "type": "boolean"},
                        {"name": "response_time", "type": "double"}
                    ]
                }},
                {"name": "mode", "type": "string"},
                {"name": "source", "type": "string"},
                {"name": "timestamp", "type": "string"},
                # Tier1 canonical fields required by learning consumer
                {"name": "mastery", "type": ["null", "double"]},
                {"name": "uncertainty", "type": ["null", "double"]},
                {"name": "zpd_score", "type": ["null", "double"]},
                {"name": "bayesian_alpha", "type": ["null", "double"]},
                {"name": "bayesian_beta", "type": ["null", "double"]},
                {"name": "kalman_mastery", "type": ["null", "double"]},
                {"name": "kalman_covariance", "type": ["null", "double"]},
                {"name": "lyapunov_mastery", "type": ["null", "double"]}
            ]
        })
        
        # Learning processed events (canonical: derived from learning-consumer)
        self.register_schema("LearningProcessed", {
            "type": "record",
            "name": "LearningProcessedEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "original_event_id", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "concept", "type": "string"},
                {"name": "timestamp", "type": "string"},
                {"name": "source", "type": "string"},
                {"name": "result", "type": {
                    "type": "record",
                    "fields": [
                        {"name": "mastery", "type": "double"},
                        {"name": "mastery_before", "type": ["null", "double"]},
                        {"name": "uncertainty", "type": "double"},
                        {"name": "zpd_score", "type": "double"},
                        {"name": "processing_mode", "type": "string"},
                        {"name": "lyapunov_mastery", "type": ["null", "double"]},
                        {"name": "bayesian_alpha", "type": ["null", "double"]},
                        {"name": "bayesian_beta", "type": ["null", "double"]},
                        {"name": "kalman_mastery", "type": ["null", "double"]},
                        {"name": "kalman_covariance", "type": ["null", "double"]},
                        {"name": "selected_concept", "type": ["null", "string"]},
                        {"name": "is_exploration", "type": ["null", "boolean"]}
                    ]
                }}
            ]
        })
        
        # Cognition updated events (canonical: derived from learning-consumer for projection-consumer)
        self.register_schema("CognitionUpdated", {
            "type": "record",
            "name": "CognitionUpdatedEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "concept_id", "type": "string"},
                {"name": "timestamp", "type": "string"},
                {"name": "source", "type": "string"},
                {"name": "result", "type": {
                    "type": "record",
                    "fields": [
                        {"name": "mastery", "type": "double"},
                        {"name": "uncertainty", "type": "double"},
                        {"name": "zpd_score", "type": "double"},
                        {"name": "processing_mode", "type": "string"},
                        {"name": "lyapunov_mastery", "type": ["null", "double"]},
                        {"name": "bayesian_alpha", "type": ["null", "double"]},
                        {"name": "bayesian_beta", "type": ["null", "double"]},
                        {"name": "kalman_mastery", "type": ["null", "double"]},
                        {"name": "kalman_covariance", "type": ["null", "double"]}
                    ]
                }}
            ]
        })
        
        # Projection updated events (canonical: derived from projection-consumer for frontend)
        # B4.1.2: ProjectionUpdated - UX semantics only (pedagogical, NOT cognition internals)
        self.register_schema("ProjectionUpdated", {
            "type": "record",
            "name": "ProjectionUpdatedEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "concept", "type": "string"},
                {"name": "timestamp", "type": "string"},
                {"name": "source", "type": "string"},
                # B4.1.2: UX semantics only - pedagogical projection layer for learner-facing display
                {"name": "ux_semantics", "type": {
                    "type": "record",
                    "fields": [
                        {"name": "readiness", "type": "string"},
                        {"name": "confidence_stability", "type": "string"},
                        {"name": "challenge_suitability", "type": "string"},
                        {"name": "pacing_responsiveness", "type": "string"},
                        {"name": "cognitive_stability", "type": "string"},
                        {"name": "transfer_readiness", "type": "string"},
                        {"name": "learning_momentum", "type": "string"},
                        {"name": "uncertainty_band", "type": "string"},
                        {"name": "next_concept_guidance", "type": "string"},
                        {"name": "pedagogical_state", "type": "string"},
                        {"name": "recommended_action", "type": "string"}
                    ]
                }},
                {"name": "projection", "type": {
                    "type": "record",
                    "fields": [
                        {"name": "projected_mastery", "type": "double"},
                        {"name": "projected_difficulty", "type": "double"},
                        {"name": "recommended_concepts", "type": {"type": "array", "items": "string"}},
                        {"name": "zpd_alignment", "type": "double"},
                        {"name": "concept_id", "type": "string"},
                        {"name": "concept_name", "type": "string"},
                        {"name": "uncertainty", "type": "double"}
                    ]
                }},
                {"name": "adaptation", "type": ["null", {
                    "type": "record",
                    "fields": [
                        {"name": "adaptation_type", "type": "string"},
                        {"name": "recommendation", "type": {"type": "map", "values": "string"}},
                        {"name": "policy_version", "type": "string"},
                        {"name": "deterministic_inputs_hash", "type": "string"}
                    ]
                }]},
                {"name": "causation_id", "type": "string"},
                {"name": "correlation_id", "type": ["null", "string"]}
            ]
        })
        
        # Adaptation generated events (canonical: derived from adaptation-consumer for projection enrichment)
        # B3.3 Phase A - Canonical Contract Freeze
        self.register_schema("AdaptationGenerated", {
            "type": "record",
            "name": "AdaptationGeneratedEvent",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "event_type", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "session_id", "type": ["null", "string"]},
                {"name": "timestamp", "type": "string"},
                {"name": "source", "type": "string"},
                
                # Policy versioning (critical for replay safety)
                {"name": "policy_version", "type": "string"},
                
                # Adaptation classification
                {"name": "adaptation_type", "type": "string"},
                
                # Pedagogical recommendation (derived, not canonical)
                {"name": "recommendation", "type": {
                    "type": "record",
                    "fields": [
                        {"name": "suggested_tasks", "type": {"type": "array", "items": "string"}},
                        {"name": "pacing_adjustment", "type": ["null", "string"]},
                        {"name": "difficulty_shift", "type": ["null", "string"]},
                        {"name": "intervention_hints", "type": {"type": "array", "items": "string"}},
                        {"name": "confidence_score", "type": ["null", "double"]}
                    ]
                }},
                
                # Cognition snapshot (for replay verification)
                {"name": "cognition_snapshot", "type": {
                    "type": "record",
                    "fields": [
                        {"name": "mastery", "type": "double"},
                        {"name": "uncertainty", "type": "double"},
                        {"name": "zpd_score", "type": "double"},
                        {"name": "bayesian_alpha", "type": ["null", "double"]},
                        {"name": "bayesian_beta", "type": ["null", "double"]},
                        {"name": "kalman_mastery", "type": ["null", "double"]},
                        {"name": "kalman_covariance", "type": ["null", "double"]},
                        {"name": "lyapunov_mastery", "type": ["null", "double"]}
                    ]
                }},
                
                # Determinism verification (critical for replay safety)
                {"name": "deterministic_inputs_hash", "type": "string"},
                
                # Schema versioning
                {"name": "schema_version", "type": "string"},
                
                # Policy inputs schema versioning (future-proofing, separate from schema_version)
                {"name": "policy_inputs_schema_version", "type": "string"},
                
                # Causation lineage (semantic trace)
                {"name": "causation_id", "type": "string"},
                
                # Trace context (OTel continuity)
                {"name": "trace_id", "type": ["null", "string"]},
                {"name": "span_id", "type": ["null", "string"]},
                {"name": "parent_span_id", "type": ["null", "string"]}
            ]
        })

        # RecommendationGenerated (canonical: single recommendation authority).
        # P2 fix: this event was NOT registered, so save_event's
        # event_schema_manager.validate_event() raised "Unknown event type"
        # → ValueError → the event was rejected before reaching the outbox.
        # validate_event only enforces presence of fields whose type != 'null'
        # and that lack a 'default'; so only the fields guaranteed present in
        # RecommendationGenerated.model_dump() are marked required here, and
        # every optional field is declared nullable to avoid false rejections.
        self.register_schema("RecommendationGenerated", {
            "type": "record",
            "name": "RecommendationGeneratedEvent",
            "fields": [
                # Required (always present in model_dump)
                {"name": "event_type", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "recommendation_timestamp", "type": "string"},
                {"name": "recommended_concept", "type": "string"},
                {"name": "policy", "type": "string"},
                {"name": "confidence", "type": "double"},
                {"name": "selection_metrics", "type": {"type": "map", "values": "string"}},
                # Present but nullable / defaulted — declared nullable so the
                # presence check never rejects on them.
                {"name": "recommended_task_id", "type": ["null", "string"]},
                {"name": "recommended_difficulty", "type": ["null", "double"]},
                {"name": "governance", "type": ["null", {"type": "map", "values": "string"}]},
                {"name": "capability_manifest_fingerprint", "type": ["null", "string"]},
                {"name": "deterministic_inputs_hash", "type": ["null", "string"]},
                {"name": "event_timestamp", "type": ["null", "string"]},
                {"name": "emitted_at", "type": ["null", "string"]},
                {"name": "schema_version", "type": ["null", "string"]},
                {"name": "source_service", "type": ["null", "string"]},
                {"name": "trace_id", "type": ["null", "string"]},
                {"name": "span_id", "type": ["null", "string"]},
                {"name": "parent_span_id", "type": ["null", "string"]},
                {"name": "causation_id", "type": ["null", "string"]},
                {"name": "correlation_id", "type": ["null", "string"]},
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
