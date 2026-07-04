"""
Decision Consistency Layer
Prevents mid-transition reads and provides stable decisions in distributed system
"""

import time
import hashlib
import json
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DecisionConsistencyLayer:
    """
    Provides decision consistency guarantees in async distributed system
    Prevents race conditions between state updates and decision reads
    """
    
    def __init__(self, consistency_window: float = 2.0):
        """
        Initialize consistency layer
        
        Args:
            consistency_window: Seconds to wait after updates before allowing new decisions
        """
        self.consistency_window = consistency_window
        self.last_decisions: Dict[str, Dict[str, Any]] = {}
        self.pending_updates: Dict[str, float] = {}
        self.state_versions: Dict[str, str] = {}
        
    def mark_update_start(self, user_id: str) -> None:
        """Mark that an update is starting for this user"""
        self.pending_updates[user_id] = time.time()
        logger.debug(f"🔄 Update started for {user_id}")
    
    def mark_update_complete(self, user_id: str, state_version: str) -> None:
        """Mark that an update is complete for this user"""
        if user_id in self.pending_updates:
            del self.pending_updates[user_id]
        
        self.state_versions[user_id] = state_version
        logger.debug(f"✅ Update complete for {user_id}, version: {state_version}")
    
    def get_consistent_decision(self, user_id: str, bandit_decision: Dict[str, Any], current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a consistent decision, potentially reusing last stable decision
        
        Args:
            user_id: User identifier
            bandit_decision: Fresh decision from bandit
            current_state: Current user state
            
        Returns:
            Consistent decision with metadata
        """
        current_time = time.time()
        
        # Check if we're in consistency window
        is_in_consistency_window = self._is_in_consistency_window(user_id, current_time)
        has_pending_update = user_id in self.pending_updates
        
        # Generate state version
        state_version = self._generate_state_version(current_state)
        
        decision_metadata = {
            "user_id": user_id,
            "state_version": state_version,
            "state_timestamp": current_time,
            "consistency_window": self.consistency_window,
            "pending_update": has_pending_update,
            "in_consistency_window": is_in_consistency_window,
            "decision_source": "bandit" if not is_in_consistency_window else "cached"
        }
        
        # Decision logic
        if is_in_consistency_window or has_pending_update:
            # Use last stable decision if available
            last_decision = self.last_decisions.get(user_id)
            if last_decision:
                logger.info(f"🛡️ Using cached decision for {user_id} (consistency window)")
                
                # Return cached decision with updated metadata
                cached_decision = last_decision["decision"].copy()
                cached_decision.update(decision_metadata)
                cached_decision["decision_source"] = "cached_stable"
                cached_decision["reasoning"] = {
                    "strategy": "consistency_cached",
                    "reason": "Decision cached during update window",
                    "original_decision": bandit_decision.get("selected_arm"),
                    "cache_age": current_time - last_decision["timestamp"]
                }
                
                return cached_decision
            else:
                # No cached decision available, delay or use bandit with warning
                logger.warning(f"⚠️ No cached decision for {user_id} during consistency window")
                
                bandit_decision.update(decision_metadata)
                bandit_decision["decision_source"] = "bandit_forced"
                bandit_decision["reasoning"] = {
                    "strategy": "bandit_forced",
                    "reason": "No cached decision available during update window",
                    "consistency_warning": True
                }
                
                return bandit_decision
        
        # Normal path: use fresh bandit decision
        logger.info(f"🎯 Using fresh bandit decision for {user_id}")
        
        # Store this decision for future consistency
        self.last_decisions[user_id] = {
            "decision": bandit_decision.copy(),
            "timestamp": current_time,
            "state_version": state_version
        }
        
        bandit_decision.update(decision_metadata)
        return bandit_decision
    
    def _is_in_consistency_window(self, user_id: str, current_time: float) -> bool:
        """Check if user is in consistency window"""
        last_decision = self.last_decisions.get(user_id)
        if not last_decision:
            return False
        
        time_since_last_decision = current_time - last_decision["timestamp"]
        return time_since_last_decision < self.consistency_window
    
    def _generate_state_version(self, state: Dict[str, Any]) -> str:
        """Generate a version hash from current state"""
        # Create a deterministic hash of relevant state
        state_str = json.dumps({
            "mastery": state.get("mastery", {}),
            "bandit": state.get("bandit", {}),
            "transfer": state.get("transfer", {}),
            "meta": state.get("meta", {})
        }, sort_keys=True)
        
        return hashlib.md5(state_str.encode(), usedforsecurity=False).hexdigest()[:8]
    
    def get_user_status(self, user_id: str) -> Dict[str, Any]:
        """Get current consistency status for a user"""
        current_time = time.time()
        
        status = {
            "user_id": user_id,
            "pending_update": user_id in self.pending_updates,
            "in_consistency_window": self._is_in_consistency_window(user_id, current_time),
            "has_cached_decision": user_id in self.last_decisions,
            "current_state_version": self.state_versions.get(user_id),
            "consistency_window": self.consistency_window
        }
        
        if user_id in self.last_decisions:
            status["last_decision_age"] = current_time - self.last_decisions[user_id]["timestamp"]
            status["last_decision_version"] = self.last_decisions[user_id]["state_version"]
        
        if user_id in self.pending_updates:
            status["update_duration"] = current_time - self.pending_updates[user_id]
        
        return status
    
    def clear_user_cache(self, user_id: str) -> None:
        """Clear cached decision for user (useful for testing)"""
        if user_id in self.last_decisions:
            del self.last_decisions[user_id]
            logger.info(f"🗑️ Cleared cache for {user_id}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        current_time = time.time()
        
        stats = {
            "total_cached_users": len(self.last_decisions),
            "pending_updates": len(self.pending_updates),
            "consistency_window": self.consistency_window,
            "timestamp": current_time
        }
        
        # Calculate average cache age
        if self.last_decisions:
            ages = [current_time - decision["timestamp"] for decision in self.last_decisions.values()]
            stats["average_cache_age"] = sum(ages) / len(ages)
            stats["oldest_cache_age"] = max(ages)
            stats["newest_cache_age"] = min(ages)
        
        return stats

# Global instance for consistency layer
_consistency_layer = None

def get_consistency_layer() -> DecisionConsistencyLayer:
    """Get global consistency layer instance"""
    global _consistency_layer
    if _consistency_layer is None:
        _consistency_layer = DecisionConsistencyLayer()
        logger.info("🛡️ Decision Consistency Layer initialized")
    return _consistency_layer

def mark_update_start(user_id: str) -> None:
    """Convenience function to mark update start"""
    get_consistency_layer().mark_update_start(user_id)

def mark_update_complete(user_id: str, state_version: str) -> None:
    """Convenience function to mark update complete"""
    get_consistency_layer().mark_update_complete(user_id, state_version)

def get_consistent_decision(user_id: str, bandit_decision: Dict[str, Any], current_state: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to get consistent decision"""
    return get_consistency_layer().get_consistent_decision(user_id, bandit_decision, current_state)
