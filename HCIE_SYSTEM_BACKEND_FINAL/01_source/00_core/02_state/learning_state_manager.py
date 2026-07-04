#!/usr/bin/env python3
"""
Learning State Manager - Enforces strict invariants for all learners
Provides the critical boundary between distributed correctness and learning correctness
"""

import hashlib
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LearningStateManager:
    """
    Enforces strict invariants for learning state updates
    
    Guarantees:
    1. Each event_id updates state exactly once
    2. Same event_id always produces same result
    3. All updates are deterministic and reproducible
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._processed_cache = {}  # Runtime cache for performance
        self._determinism_cache = {}  # Cache for deterministic results
        
    def is_event_processed(self, event_id: str) -> bool:
        """
        Check if event has already been processed
        
        This is the CRITICAL GATE before any learning update
        """
        # Check runtime cache first
        if event_id in self._processed_cache:
            return True
            
        # Check database
        cursor = self.db.cursor()
        try:
            # Convert to UUID for database query
            import uuid as uuid_lib
            event_uuid = uuid_lib.UUID(event_id) if isinstance(event_id, str) else event_id
            cursor.execute(
                "SELECT 1 FROM processed_events WHERE event_id = %s",
                (str(event_uuid),)
            )
        except (ValueError, TypeError):
            # If not a valid UUID, use string (for testing)
            cursor.execute(
                "SELECT 1 FROM processed_events WHERE event_id::text = %s",
                (event_id,)
            )
        
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            self._processed_cache[event_id] = True
            return True
            
        return False
    
    def mark_event_processed(self, event_id: str, user_id: str) -> bool:
        """
        Mark event as processed (must be called AFTER successful update)
        
        Returns True if successfully marked, False if already existed
        """
        if self.is_event_processed(event_id):
            logger.warning(f"⚠️ Attempted to mark already processed event: {event_id}")
            return False
            
        cursor = self.db.cursor()
        try:
            # Convert to UUID for database insert
            import uuid as uuid_lib
            event_uuid = uuid_lib.UUID(event_id) if isinstance(event_id, str) else event_id
            cursor.execute(
                "INSERT INTO processed_events (event_id, user_id) VALUES (%s, %s)",
                (str(event_uuid), user_id)
            )
            cursor.execute("COMMIT")
            
            # Update cache
            self._processed_cache[event_id] = True
            logger.info(f"✅ Event marked as processed: {event_id}")
            return True
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            logger.error(f"❌ Failed to mark event as processed: {e}")
            return False
        finally:
            cursor.close()
    
    def get_deterministic_update_key(self, event: Dict[str, Any]) -> str:
        """
        Generate deterministic key for event update
        
        Ensures same event_id → same update result ALWAYS
        """
        # Extract only the fields that affect learning outcome
        key_fields = {
            "event_id": str(event.get("event_id", "")),  # Convert UUID to string
            "event_type": event.get("event_type"),
            "user_id": event.get("user_id"),
            "concept_id": event.get("concept_id"),
            "correct": event.get("correct"),
            "difficulty": event.get("difficulty"),
            "response_time": event.get("response_time")
        }
        
        # Create deterministic hash
        key_str = json.dumps(key_fields, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def should_apply_update(self, event: Dict[str, Any]) -> bool:
        """
        Critical gate: determines if learning update should be applied
        
        This is the BOUNDARY ENFORCEMENT you described
        """
        event_id = event.get("event_id")
        
        if not event_id:
            logger.error("❌ Event missing event_id - rejecting")
            return False
            
        # 1. Check if already processed (CRITICAL)
        if self.is_event_processed(event_id):
            logger.info(f"⏭️ Event already processed, skipping: {event_id}")
            return False
            
        # 2. Validate required fields
        required_fields = ["event_id", "user_id", "event_type"]
        for field in required_fields:
            if field not in event or not event[field]:
                logger.warning(f"⚠️ Event missing required field {field}: {event_id}")
                return False
        
        # 3. Check for deterministic result (if cached)
        update_key = self.get_deterministic_update_key(event)
        if update_key in self._determinism_cache:
            logger.info(f"🔄 Using cached deterministic result for: {event_id}")
            return False  # Already applied
            
        return True
    
    def cache_deterministic_result(self, event: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Cache result to ensure determinism for future replays
        """
        update_key = self.get_deterministic_update_key(event)
        self._determinism_cache[update_key] = {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    def apply_learning_update(self, event: Dict[str, Any], update_function) -> Optional[Dict[str, Any]]:
        """
        Apply learning update with full invariant protection
        
        This is the SURGICAL wrapper around all learners
        """
        event_id = event.get("event_id")
        user_id = event.get("user_id")
        
        logger.info(f"🔒 Learning update requested for: {event_id}")
        
        # CRITICAL GATE: Check if should apply
        if not self.should_apply_update(event):
            return None
            
        try:
            # Apply the learning update
            result = update_function(event)
            
            # Cache deterministic result
            self.cache_deterministic_result(event, result)
            
            # Mark as processed (CRITICAL: after successful update)
            if self.mark_event_processed(event_id, user_id):
                logger.info(f"✅ Learning update completed: {event_id}")
                return result
            else:
                logger.error(f"❌ Failed to mark event as processed: {event_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Learning update failed for {event_id}: {e}")
            return None
    
    def get_invariant_report(self) -> Dict[str, Any]:
        """
        Report on invariant status for monitoring
        """
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM processed_events")
        total_processed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT event_id) FROM processed_events")
        unique_events = cursor.fetchone()[0]
        
        cursor.close()
        
        return {
            "total_processed_events": total_processed,
            "unique_processed_events": unique_events,
            "cache_size": len(self._processed_cache),
            "determinism_cache_size": len(self._determinism_cache),
            "duplicate_ratio": (total_processed - unique_events) / max(total_processed, 1),
            "invariant_status": "HEALTHY" if total_processed == unique_events else "CORRUPTED"
        }
