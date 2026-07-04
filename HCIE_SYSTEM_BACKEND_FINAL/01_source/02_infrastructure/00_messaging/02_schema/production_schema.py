"""
🔥 PRODUCTION SCHEMA FOR FRONTEND-READY HCIE v1.1

Unified schema contract between API and Consumer
Ensures production-ready data flow with proper validation
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import json

@dataclass
class ProductionLearningEvent:
    """
    Production-ready learning event schema v1.1
    Used by both API and Consumer for consistent data flow
    Enforces strict validation and prevents schema drift
    """
    # Required fields - always present
    event_id: str
    event_type: str
    user_id: str
    concept: str
    interaction: Dict[str, Any]
    
    # Learning configuration
    mode: str = "write"
    
    # Optional fields for different event types
    task_id: Optional[str] = None
    reward: Optional[float] = None
    session_id: Optional[str] = None
    difficulty: Optional[float] = None
    
    # System metadata
    timestamp: str = ""
    version: str = "1.1"
    source_service: str = "learning-api"
    
    # Quality metrics
    processing_time_ms: Optional[float] = None
    confidence_score: Optional[float] = None
    zpd_delta_signal: Optional[float] = None
    
    def __post_init__(self):
        """Auto-generate missing fields"""
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'user_id': self.user_id,
            'concept': self.concept,
            'interaction': self.interaction,
            'mode': self.mode,
            'task_id': self.task_id,
            'reward': self.reward,
            'timestamp': self.timestamp
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_api_request(cls, user_id: str, concept: str, interaction: Dict[str, Any], 
                         mode: str = "write", event_type: str = "task_completed") -> 'ProductionLearningEvent':
        """Create from API request parameters"""
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=user_id,
            concept=concept,
            interaction=interaction,
            mode=mode
        )
    
    @classmethod
    def from_feedback_request(cls, user_id: str, action_taken: str, outcome: Dict[str, Any],
                            event_type: str = "decision_feedback") -> 'ProductionLearningEvent':
        """Create from decision/feedback request"""
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=user_id,
            concept=action_taken,  # action_taken is the concept
            interaction=outcome,
            mode="write"
        )

def validate_production_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comprehensive validation against production schema v1.1
    Enforces strict schema compliance and prevents drift
    Returns validated data or detailed error information
    """
    # 🔥 CRITICAL: Handle both ProductionLearningEvent and LearningResult objects
    # Check if this is a LearningResult object (has LearningResult fields)
    learning_result_fields = ["mastery", "uncertainty", "confidence", "lyapunov_mastery", 
                          "bayesian_alpha", "bayesian_beta", "kalman_mastery", "kalman_covariance",
                          "ensemble_weights", "ensemble_variance", "policy", "policy_multiplier",
                          "transfer_amounts", "transfer_efficiency", "zpd_target", "zpd_alignment_error",
                          "zpd_score", "zpd_delta_signal", "timestamp", "processing_mode", "processing_time",
                          "J_value", "confidence_adjusted_mastery", "effective_learning_rate", "mastery_delta",
                          "transfer_amount", "event_id", "interaction_id", "adaptive_rate"]
    
    is_learning_result = all(field in data for field in learning_result_fields)
    
    if is_learning_result:
        # Validate LearningResult object
        required_lr_fields = ["mastery", "uncertainty", "confidence", "zpd_delta_signal", "processing_time"]
        missing_lr = [field for field in required_lr_fields if field not in data]
        
        if missing_lr:
            return {
                "_validation_error": "missing_required_fields",
                "missing_fields": missing_lr,
                "required_fields": required_lr_fields,
                "original_data": data
            }
        
        return data  # LearningResult objects are already validated by construction
    
    # Otherwise validate as ProductionLearningEvent
    # 🔥 CRITICAL: Reject any wrapped format - only accept direct ProductionLearningEvent
    if "data" in data:
        return {
            "_validation_error": "wrapped_format_rejected",
            "message": "Only direct ProductionLearningEvent format accepted",
            "original_data": data
        }
    
    # Required fields validation
    required_fields = ["event_id", "event_type", "user_id", "concept", "interaction"]
    missing = [field for field in required_fields if field not in data]
    
    if missing:
        return {
            "_validation_error": "missing_required_fields",
            "missing_fields": missing,
            "required_fields": required_fields,
            "original_data": data
        }
    
    # Field type validation
    type_errors = []
    
    if not isinstance(data.get("event_id"), str) or len(data["event_id"]) < 10:
        type_errors.append(("event_id", "string (UUID, min 10 chars)"))
    
    if not isinstance(data.get("event_type"), str):
        type_errors.append(("event_type", "string"))
    
    if not isinstance(data.get("user_id"), str) or len(data["user_id"]) < 1:
        type_errors.append(("user_id", "non-empty string"))
    
    if not isinstance(data.get("concept"), str) or len(data["concept"]) < 1:
        type_errors.append(("concept", "non-empty string"))
    
    if not isinstance(data.get("interaction"), dict):
        type_errors.append(("interaction", "dictionary"))
    
    # Validate interaction content
    if isinstance(data.get("interaction"), dict):
        interaction = data["interaction"]
        if "correct" not in interaction and "response_time" not in interaction:
            type_errors.append(("interaction", "must contain 'correct' or 'response_time'"))
    
    # Optional field validation
    if data.get("reward") is not None:
        if not isinstance(data["reward"], (int, float)) or data["reward"] < 0 or data["reward"] > 1:
            type_errors.append(("reward", "float between 0 and 1"))
    
    if data.get("difficulty") is not None:
        if not isinstance(data["difficulty"], (int, float)) or data["difficulty"] < 0 or data["difficulty"] > 1:
            type_errors.append(("difficulty", "float between 0 and 1"))
    
    if data.get("mode") is not None and data["mode"] not in ["read", "write", "simulation"]:
        type_errors.append(("mode", "one of: read, write, simulation"))
    
    if type_errors:
        return {
            "_validation_error": "type_validation_failed",
            "type_errors": type_errors,
            "original_data": data
        }
    
    # Event type validation
    valid_event_types = ["task_completed", "decision_feedback", "assessment_completed", "practice_session", "learning_interaction"]
    if data["event_type"] not in valid_event_types:
        return {
            "_validation_error": "invalid_event_type",
            "event_type": data["event_type"],
            "valid_types": valid_event_types,
            "original_data": data
        }
    
    return data  # All validations passed

def create_production_event(event_type: str, user_id: str, concept: str, 
                          interaction: Dict[str, Any], **kwargs) -> ProductionLearningEvent:
    """
    Factory function to create validated ProductionLearningEvent
    Ensures all events follow the same creation pattern
    """
    return ProductionLearningEvent(
        event_id=kwargs.get("event_id", str(uuid.uuid4())),
        event_type=event_type,
        user_id=user_id,
        concept=concept,
        interaction=interaction,
        mode=kwargs.get("mode", "write"),
        task_id=kwargs.get("task_id"),
        reward=kwargs.get("reward"),
        session_id=kwargs.get("session_id"),
        difficulty=kwargs.get("difficulty"),
        timestamp=kwargs.get("timestamp", datetime.utcnow().isoformat()),
        version="1.1",
        source_service=kwargs.get("source_service", "learning-api"),
        processing_time_ms=kwargs.get("processing_time_ms"),
        confidence_score=kwargs.get("confidence_score")
    )

# Event types for production system
EVENT_TYPES = {
    "task_completed": "Standard learning task completion",
    "decision_feedback": "Bandit decision feedback",
    "assessment_completed": "Formal assessment completion",
    "practice_session": "Practice session interaction"
}
