"""
Redis Caching Strategy for CQRS
Multi-layer caching with proper invalidation
"""

import json
import logging
from typing import Any, Optional, Dict
from datetime import datetime
import redis

logger = logging.getLogger(__name__)

class RedisCacheManager:
    """Redis cache manager with layered caching strategy"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.default_ttl = 900  # 15 minutes
    
    def _get_redis_client(self):
        """Get redis client, fallback to direct connection"""
        if self.redis_client:
            return self.redis_client
        
        # Fallback to direct Redis connection
        try:
            import os
            client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            client.ping()  # Test connection
            return client
        except Exception as e:
            logger.warning(f"⚠️ Redis not available for caching: {e}")
            return None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        client = self._get_redis_client()
        if not client:
            return None
        
        try:
            value = client.get(key)
            if value:
                logger.debug(f"🎯 Cache HIT: {key}")
                return json.loads(value)
            else:
                logger.debug(f"🎯 Cache MISS: {key}")
                return None
        except Exception as e:
            logger.error(f"❌ Cache get error for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with TTL"""
        client = self._get_redis_client()
        if not client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            result = client.setex(key, ttl, serialized_value)
            
            if result:
                logger.debug(f"💾 Cache SET: {key} (TTL: {ttl}s)")
            return bool(result)
        except Exception as e:
            logger.error(f"❌ Cache set error for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        client = self._get_redis_client()
        if not client:
            return False
        
        try:
            result = client.delete(key)
            if result:
                logger.debug(f"🗑️ Cache DELETE: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"❌ Cache delete error for {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        client = self._get_redis_client()
        if not client:
            return 0
        
        try:
            keys = client.keys(pattern)
            if keys:
                result = client.delete(*keys)
                logger.debug(f"🗑️ Cache DELETE PATTERN: {pattern} ({result} keys)")
                return result
            return 0
        except Exception as e:
            logger.error(f"❌ Cache delete pattern error for {pattern}: {e}")
            return 0

class UserCacheManager:
    """User-specific cache manager for CQRS read side"""
    
    def __init__(self, cache_manager: RedisCacheManager):
        self.cache = cache_manager
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from cache"""
        key = f"user_profile:{user_id}"
        return self.cache.get(key)
    
    def set_user_profile(self, user_id: str, user_data: Dict[str, Any], ttl: int = 900):
        """Set user profile in cache"""
        key = f"user_profile:{user_id}"
        self.cache.set(key, user_data, ttl)
    
    def invalidate_user_profile(self, user_id: str):
        """Invalidate user profile cache"""
        key = f"user_profile:{user_id}"
        self.cache.delete(key)
    
    def get_user_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user progress from cache (short TTL)"""
        key = f"user_progress:{user_id}"
        return self.cache.get(key)
    
    def set_user_progress(self, user_id: str, progress_data: Dict[str, Any], ttl: int = 300):
        """Set user progress in cache (short TTL for real-time feel)"""
        key = f"user_progress:{user_id}"
        self.cache.set(key, progress_data, ttl)
    
    def invalidate_user_progress(self, user_id: str):
        """Invalidate user progress cache"""
        key = f"user_progress:{user_id}"
        self.cache.delete(key)
    
    def invalidate_user_all(self, user_id: str):
        """Invalidate all user-related caches"""
        patterns = [
            f"user_profile:{user_id}",
            f"user_progress:{user_id}",
            f"user_analytics:{user_id}",
            f"user_session:{user_id}"
        ]
        
        for key in patterns:
            self.cache.delete(key)
        
        # Also delete pattern-based keys
        self.cache.delete_pattern(f"user_*:{user_id}")

class ReadThroughCache:
    """Read-through cache for CQRS pattern"""
    
    def __init__(self, cache_manager: RedisCacheManager):
        self.cache = cache_manager
    
    def get_or_fetch(self, key: str, fetch_func, ttl: int = None) -> Any:
        """Get from cache or fetch from source"""
        # Try cache first
        cached_value = self.cache.get(key)
        if cached_value is not None:
            return cached_value
        
        # Cache miss - fetch from source
        try:
            value = fetch_func()
            if value is not None:
                # Cache the fetched value
                self.cache.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"❌ Fetch function error for {key}: {e}")
            return None

# Singleton cache managers
_cache_manager_instance: Optional[RedisCacheManager] = None
_user_cache_manager_instance: Optional[UserCacheManager] = None

def get_cache_manager() -> RedisCacheManager:
    """Get singleton cache manager"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = RedisCacheManager()
    return _cache_manager_instance

def get_user_cache_manager() -> UserCacheManager:
    """Get singleton user cache manager"""
    global _user_cache_manager_instance
    if _user_cache_manager_instance is None:
        _user_cache_manager_instance = UserCacheManager(get_cache_manager())
    return _user_cache_manager_instance
