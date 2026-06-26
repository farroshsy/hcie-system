#!/usr/bin/env python3
"""
Pre-Validation Safe Fixer
Applies safe fixes BEFORE schema validation
"""

import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple

class PreValidationFixer:
    """
    Applies safe fixes to incomplete events before strict validation
    Only fixes things that are guaranteed safe and unambiguous
    """
    
    @staticmethod
    def apply_safe_fixes(event: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Apply safe fixes to an event
        Returns: (fixed_event, applied_fixes, remaining_issues)
        """
        fixed_event = event.copy()
        applied_fixes = []
        remaining_issues = []
        
        # === SAFE FIX 1: Generate missing UUID ===
        if not fixed_event.get("event_id"):
            new_id = str(uuid.uuid4())
            fixed_event["event_id"] = new_id
            applied_fixes.append(f"Generated event_id: {new_id}")
        
        # === SAFE FIX 2: Generate missing timestamp ===
        if not fixed_event.get("timestamp"):
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            fixed_event["timestamp"] = timestamp
            applied_fixes.append(f"Generated timestamp: {timestamp}")
        
        # === SAFE FIX 3: Set default version ===
        if not fixed_event.get("version"):
            fixed_event["version"] = 2
            applied_fixes.append("Set default version: 2")
        
        # === SAFE FIX 4: Generate missing engagement_time (V2) ===
        if fixed_event.get("version", 1) >= 2 and not fixed_event.get("engagement_time"):
            fixed_event["engagement_time"] = 60  # Default 1 minute
            applied_fixes.append("Set default engagement_time: 60")
        
        # === SAFE FIX 5: Generate missing attempts (V2) ===
        if fixed_event.get("version", 1) >= 2 and not fixed_event.get("attempts"):
            fixed_event["attempts"] = 1
            applied_fixes.append("Set default attempts: 1")
        
        # === SAFE FIX 6: Generate missing hints_used (V2) ===
        if fixed_event.get("version", 1) >= 2 and not fixed_event.get("hints_used"):
            fixed_event["hints_used"] = 0
            applied_fixes.append("Set default hints_used: 0")
        
        # === SAFE FIX 7: Generate missing metadata (V2) ===
        if fixed_event.get("version", 1) >= 2 and not fixed_event.get("metadata"):
            fixed_event["metadata"] = {}
            applied_fixes.append("Set empty metadata: {}")
        
        # === DETECT REMAINING ISSUES (for classification) ===
        if not fixed_event.get("user_id"):
            remaining_issues.append("missing_user_id")
        
        if not fixed_event.get("event_type"):
            remaining_issues.append("missing_event_type")
        
        if not fixed_event.get("reward"):
            remaining_issues.append("missing_reward")
        
        if not fixed_event.get("task_id"):
            remaining_issues.append("missing_task_id")
        
        if not fixed_event.get("concept"):
            remaining_issues.append("missing_concept")
        
        # Check for invalid values (these are NOT fixable)
        if fixed_event.get("reward") and not (0.0 <= float(fixed_event["reward"]) <= 1.0):
            remaining_issues.append("invalid_reward")
        
        if fixed_event.get("event_id") and not PreValidationFixer._is_valid_uuid(fixed_event["event_id"]):
            remaining_issues.append("invalid_uuid")
        
        return fixed_event, applied_fixes, remaining_issues
    
    @staticmethod
    def _is_valid_uuid(value: str) -> bool:
        """Check if value is valid UUID"""
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def classify_fix_safety(applied_fixes: List[str], remaining_issues: List[str]) -> Dict[str, Any]:
        """
        Classify the safety of applied fixes and remaining issues
        """
        # All our fixes are SAFE by design
        if applied_fixes and not remaining_issues:
            return {
                "level": "safe",
                "confidence": 0.95,
                "description": "Applied only safe fixes, no remaining issues",
                "auto_fixable": True
            }
        
        elif applied_fixes and remaining_issues:
            # We applied some fixes but still have issues
            dangerous_issues = ["invalid_uuid", "invalid_reward"]
            has_dangerous = any(issue in dangerous_issues for issue in remaining_issues)
            
            if has_dangerous:
                return {
                    "level": "manual",
                    "confidence": 0.0,
                    "description": f"Applied safe fixes but dangerous issues remain: {remaining_issues}",
                    "auto_fixable": False
                }
            else:
                return {
                    "level": "risky", 
                    "confidence": 0.75,
                    "description": f"Applied safe fixes but issues remain: {remaining_issues}",
                    "auto_fixable": False  # Require manual review for remaining issues
                }
        
        elif not applied_fixes and remaining_issues:
            # No fixes applied, only issues detected
            return {
                "level": "manual",
                "confidence": 0.0,
                "description": f"No safe fixes available for issues: {remaining_issues}",
                "auto_fixable": False
            }
        
        else:
            # No fixes, no issues - event was already valid
            return {
                "level": "safe",
                "confidence": 1.0,
                "description": "Event was already valid",
                "auto_fixable": True
            }

# Convenience functions
def apply_safe_pre_validation_fixes(event: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
    return PreValidationFixer.apply_safe_fixes(event)

def classify_pre_validation_fixes(applied_fixes: List[str], remaining_issues: List[str]) -> Dict[str, Any]:
    return PreValidationFixer.classify_fix_safety(applied_fixes, remaining_issues)
