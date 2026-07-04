"""
User Domain Service
Handles user profile and preferences (separate from auth)
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..auth.events import AuthEventProducer, AuthEventType
from ...infrastructure.redis.cache import get_user_cache_manager

logger = logging.getLogger(__name__)

class UserService:
    """User domain service - handles user lifecycle excluding auth"""
    
    def __init__(self, user_repo, event_producer: AuthEventProducer = None):
        self.user_repo = user_repo
        self.event_producer = event_producer
        self.cache_manager = get_user_cache_manager()
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user profile with cache invalidation"""
        if not updates:
            return None
        
        # Validate allowed fields
        allowed_fields = {"name", "learning_rate", "forgetting_rate"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            logger.warning(f"⚠️ No allowed fields to update for user {user_id}")
            return None
        
        try:
            # Update in database
            self.user_repo.update_profile(user_id, filtered_updates)
            
            # Invalidate cache
            self.cache_manager.invalidate_user_profile(user_id)
            
            # Get updated user data
            updated_user = self.user_repo.get_by_id(user_id)
            
            # Emit profile update event
            if self.event_producer and updated_user:
                try:
                    self.event_producer.user_profile_updated(
                        user_id=user_id,
                        email=updated_user.get('email'),
                        updated_fields=filtered_updates
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to emit profile update event: {e}")
            
            logger.info(f"✅ Updated profile for user {user_id}: {list(filtered_updates.keys())}")
            return updated_user
            
        except Exception as e:
            logger.error(f"❌ Failed to update profile for user {user_id}: {e}")
            return None
    
    def get_profile(self, user_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get user profile with CQRS read-through cache"""
        if use_cache:
            # Try cache first
            cached_profile = self.cache_manager.get_user_profile(user_id)
            if cached_profile:
                return cached_profile
        
        # Fetch from database
        user = self.user_repo.get_by_id(user_id)
        if user:
            # Cache for future reads
            if use_cache:
                self.cache_manager.set_user_profile(user_id, user)
            return user
        
        return None
    
    def update_last_active(self, user_id: str):
        """Update user's last active timestamp"""
        try:
            self.user_repo.update_last_active(user_id)
            # Invalidate cache since timestamp changed
            self.cache_manager.invalidate_user_profile(user_id)
        except Exception as e:
            logger.error(f"❌ Failed to update last active for user {user_id}: {e}")
    
    def assign_experiment(self, user_id: str, experiment_id: str, experiment_group: str):
        """Assign user to experiment group"""
        try:
            self.user_repo.update_experiment_assignment(user_id, experiment_id, experiment_group)
            
            # Invalidate cache
            self.cache_manager.invalidate_user_profile(user_id)
            
            logger.info(f"🧪 Assigned user {user_id} to experiment {experiment_group}")
            
        except Exception as e:
            logger.error(f"❌ Failed to assign experiment for user {user_id}: {e}")
