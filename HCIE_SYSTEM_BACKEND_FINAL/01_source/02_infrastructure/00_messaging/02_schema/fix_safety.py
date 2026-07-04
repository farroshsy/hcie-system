#!/usr/bin/env python3
"""
Fix Safety Classification Framework
Classifies fixes by safety level and applies confidence thresholds
"""

from enum import Enum
from typing import Dict, Any
import json

class FixSafetyLevel(Enum):
    """Safety classification for auto-fixes"""
    SAFE = "safe"           # Can auto-apply without review (confidence >= 0.9)
    RISKY = "risky"         # Requires confidence >= 0.8
    DANGEROUS = "dangerous" # Requires confidence >= 0.95 or manual review
    MANUAL = "manual"       # Always requires manual review

class FixClassifier:
    """
    Classifies and evaluates fix safety with confidence thresholds
    """
    
    # Safety thresholds
    SAFE_THRESHOLD = 0.9
    RISKY_THRESHOLD = 0.8
    DANGEROUS_THRESHOLD = 0.95
    
    @staticmethod
    def classify_fix(error_reason: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Classify a fix by safety level and confidence
        Returns: {"level": FixSafetyLevel, "confidence": float, "description": str}
        """
        context = context or {}
        
        classifications = {
            # SAFE fixes (high confidence, low risk)
            "missing_required_fields": FixClassifier._classify_missing_fields(context),
            "add_current_timestamp": FixClassifier._classify_timestamp_fix(context),
            "normalize_event_type": FixClassifier._classify_event_type_fix(context),
            "upgrade_version": FixClassifier._classify_version_fix(context),
            
            # RISKY fixes (moderate confidence, some risk)
            "fix_missing_quotes": FixClassifier._classify_json_syntax_fix(context),
            "remove_trailing_comma": FixClassifier._classify_json_syntax_fix(context),
            
            # DANGEROUS fixes (low confidence, high risk)
            "json_decode_failed": FixClassifier._classify_json_decode_fix(context),
            "invalid_raw_type": FixClassifier._classify_type_fix(context),
            
            # MANUAL fixes (never auto-apply)
            "schema_validation_failed": FixClassifier._classify_schema_fix(context),
            "migration_failed": FixClassifier._classify_migration_fix(context),
            "transaction_failed": FixClassifier._classify_transaction_fix(context),
            
            # NEW ROOT CAUSE CLASSIFICATIONS
            "invalid_reward_range": FixClassifier._classify_invalid_reward(context),
            "invalid_uuid_format": FixClassifier._classify_invalid_uuid(context),
            "missing_business_fields": FixClassifier._classify_missing_business_fields(context),
            "cross_layer_constraint_violation": FixClassifier._classify_cross_layer_violation(context),
            "partial_fix_failed": FixClassifier._classify_partial_fix_failure(context),
            "deserialization_failed": FixClassifier._classify_deserialization_failure(context),
            "schema_structure_violation": FixClassifier._classify_schema_violation(context),
        }
        
        return classifications.get(error_reason, {
            "level": FixSafetyLevel.MANUAL,
            "confidence": 0.0,
            "description": "Unknown error type - requires manual review"
        })
    
    @staticmethod
    def _classify_missing_fields(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify missing field fixes"""
        missing_fields = context.get("missing_fields", [])
        
        # Very safe to generate UUIDs and timestamps
        if all(field in ["event_id", "timestamp"] for field in missing_fields):
            return {
                "level": FixSafetyLevel.SAFE,
                "confidence": 0.95,
                "description": "Generate missing UUID/timestamp (safe)"
            }
        
        # Moderately safe for other standard fields
        elif all(field in ["event_id", "timestamp", "version"] for field in missing_fields):
            return {
                "level": FixSafetyLevel.RISKY,
                "confidence": 0.85,
                "description": "Generate missing standard fields (risky)"
            }
        
        # Dangerous for business logic fields
        else:
            return {
                "level": FixSafetyLevel.DANGEROUS,
                "confidence": 0.7,
                "description": "Generate missing business fields (dangerous)"
            }
    
    @staticmethod
    def _classify_timestamp_fix(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify timestamp fixes"""
        return {
            "level": FixSafetyLevel.SAFE,
            "confidence": 0.95,
            "description": "Add current timestamp (safe)"
        }
    
    @staticmethod
    def _classify_event_type_fix(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify event type normalization"""
        event_type = context.get("event_type", "")
        
        # Safe for obvious typos
        safe_mappings = {
            "submit": "task_submitted",
            "complete": "task_completed",
            "master": "concept_mastered",
            "TASK_SUBMITTED": "task_submitted",
            "TaskSubmitted": "task_submitted"
        }
        
        if event_type in safe_mappings:
            return {
                "level": FixSafetyLevel.SAFE,
                "confidence": 0.9,
                "description": f"Normalize event type: {event_type} → {safe_mappings[event_type]}"
            }
        
        # Risky for uncertain mappings
        elif event_type in ["submit_task", "complete_task", "master_concept"]:
            return {
                "level": FixSafetyLevel.RISKY,
                "confidence": 0.75,
                "description": f"Infer event type: {event_type} (risky)"
            }
        
        # Dangerous for unknown types
        else:
            return {
                "level": FixSafetyLevel.DANGEROUS,
                "confidence": 0.5,
                "description": f"Unknown event type: {event_type} (dangerous)"
            }
    
    @staticmethod
    def _classify_version_fix(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify version upgrade fixes"""
        from_version = context.get("from_version", 0)
        to_version = context.get("to_version", 1)
        
        # Safe for known version paths
        if (from_version, to_version) in [(1, 2), (2, 1)]:
            return {
                "level": FixSafetyLevel.SAFE,
                "confidence": 0.9,
                "description": f"Version {from_version} → {to_version} (safe)"
            }
        
        # Risky for unknown paths
        else:
            return {
                "level": FixSafetyLevel.RISKY,
                "confidence": 0.7,
                "description": f"Version {from_version} → {to_version} (risky)"
            }
    
    @staticmethod
    def _classify_json_syntax_fix(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify JSON syntax fixes"""
        error_msg = context.get("error", "").lower()
        
        # Safe for obvious syntax issues
        if "expecting ',' delimiter" in error_msg or "missing quotes" in error_msg:
            return {
                "level": FixSafetyLevel.RISKY,
                "confidence": 0.8,
                "description": "Fix JSON syntax (risky)"
            }
        
        # Dangerous for complex JSON issues
        else:
            return {
                "level": FixSafetyLevel.DANGEROUS,
                "confidence": 0.6,
                "description": "Complex JSON repair (dangerous)"
            }
    
    @staticmethod
    def _classify_json_decode_fix(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify JSON decode failures"""
        return {
            "level": FixSafetyLevel.DANGEROUS,
            "confidence": 0.4,
            "description": "JSON decode failed (dangerous)"
        }
    
    @staticmethod
    def _classify_type_fix(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify type conversion fixes"""
        return {
            "level": FixSafetyLevel.DANGEROUS,
            "confidence": 0.3,
            "description": "Type conversion (dangerous)"
        }
    
    @staticmethod
    def _classify_schema_fix(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify schema validation fixes"""
        return {
            "level": FixSafetyLevel.MANUAL,
            "confidence": 0.0,
            "description": "Schema validation failed (manual review required)"
        }
    
    @staticmethod
    def _classify_migration_fix(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify migration failure fixes"""
        return {
            "level": FixSafetyLevel.MANUAL,
            "confidence": 0.0,
            "description": "Migration failed (manual review required)"
        }
    
    @staticmethod
    def _classify_transaction_fix(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify transaction failure fixes"""
        return {
            "level": FixSafetyLevel.MANUAL,
            "confidence": 0.0,
            "description": "Transaction failed (manual review required)"
        }
    
    @staticmethod
    def should_auto_apply(classification: Dict[str, Any]) -> bool:
        """Determine if a fix should be auto-applied based on safety and confidence"""
        level = classification["level"]
        confidence = classification["confidence"]
        
        if level == FixSafetyLevel.SAFE:
            return confidence >= FixClassifier.SAFE_THRESHOLD
        elif level == FixSafetyLevel.RISKY:
            return confidence >= FixClassifier.RISKY_THRESHOLD
        elif level == FixSafetyLevel.DANGEROUS:
            return confidence >= FixClassifier.DANGEROUS_THRESHOLD
        else:  # MANUAL
            return False
    
    @staticmethod
    def get_fix_recommendation(classification: Dict[str, Any]) -> str:
        """Get human-readable recommendation for a fix"""
        level = classification["level"]
        confidence = classification["confidence"]
        
        if level == FixSafetyLevel.SAFE and confidence >= FixClassifier.SAFE_THRESHOLD:
            return "AUTO-APPLY: Safe fix with high confidence"
        elif level == FixSafetyLevel.RISKY and confidence >= FixClassifier.RISKY_THRESHOLD:
            return "AUTO-APPLY: Risky fix but above threshold"
        elif level == FixSafetyLevel.DANGEROUS and confidence >= FixClassifier.DANGEROUS_THRESHOLD:
            return "AUTO-APPLY: Dangerous fix but very high confidence"
        else:
            return f"MANUAL REVIEW: {level.value} fix with confidence {confidence:.2f}"
    
    @staticmethod
    def _classify_invalid_reward(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify invalid reward values"""
        return {
            "level": FixSafetyLevel.MANUAL,
            "confidence": 0.0,
            "description": "Invalid reward outside [0,1] range"
        }
    
    @staticmethod
    def _classify_invalid_uuid(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify invalid UUID format"""
        return {
            "level": FixSafetyLevel.MANUAL,
            "confidence": 0.0,
            "description": "Invalid UUID format - requires proper UUID"
        }
    
    @staticmethod
    def _classify_missing_business_fields(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify missing business fields"""
        return {
            "level": FixSafetyLevel.MANUAL,
            "confidence": 0.0,
            "description": "Missing required business fields"
        }
    
    @staticmethod
    def _classify_cross_layer_violation(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify cross-layer constraint violations"""
        return {
            "level": FixSafetyLevel.MANUAL,
            "confidence": 0.0,
            "description": "Cross-layer constraint violation"
        }
    
    @staticmethod
    def _classify_partial_fix_failure(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify partial fix failures"""
        applied_fixes = context.get("applied_fixes", [])
        return {
            "level": FixSafetyLevel.MANUAL,
            "confidence": 0.0,
            "description": f"Partial fix failed (tried: {', '.join(applied_fixes)})"
        }
    
    @staticmethod
    def _classify_deserialization_failure(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify deserialization failures"""
        error_msg = context.get("error", "").lower()
        if "json decode" in error_msg:
            return {
                "level": FixSafetyLevel.DANGEROUS,
                "confidence": 0.3,
                "description": "JSON decode error - corrupted data"
            }
        else:
            return {
                "level": FixSafetyLevel.MANUAL,
                "confidence": 0.0,
                "description": "Data deserialization failed - format unknown"
            }
    
    @staticmethod
    def _classify_schema_violation(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify schema structure violations"""
        validation_errors = context.get("validation_errors", [])
        if validation_errors:
            return {
                "level": FixSafetyLevel.MANUAL,
                "confidence": 0.0,
                "description": f"Schema violation: {', '.join(validation_errors[:2])}"
            }
        else:
            return {
                "level": FixSafetyLevel.MANUAL,
                "confidence": 0.0,
                "description": "Schema structure violation"
            }

# Convenience functions
def classify_fix_safety(error_reason: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    return FixClassifier.classify_fix(error_reason, context)

def should_auto_apply_fix(error_reason: str, context: Dict[str, Any] = None) -> bool:
    classification = classify_fix_safety(error_reason, context)
    return FixClassifier.should_auto_apply(classification)
