"""
Redis Token Store - Distributed refresh token storage
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RedisTokenStore:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "refresh_token:"
        self.default_ttl = 7 * 24 * 3600  # 7 days in seconds

    def store(self, token: str, user_id: str, ttl_seconds: int = None):
        """Store refresh token with TTL"""
        key = self.prefix + token
        ttl = ttl_seconds or self.default_ttl
        
        self.redis.setex(key, ttl, user_id)
        logger.info(f"🔄 Stored refresh token for user {user_id} (TTL: {ttl}s)")

    def verify(self, token: str) -> Optional[str]:
        """Verify refresh token and return user_id"""
        key = self.prefix + token
        user_id = self.redis.get(key)
        
        if user_id:
            logger.info(f"✅ Verified refresh token for user {user_id.decode()}")
            return user_id.decode()
        
        logger.warning("⚠️ Refresh token not found or expired")
        return None

    def revoke(self, token: str):
        """Revoke refresh token"""
        key = self.prefix + token
        result = self.redis.delete(key)
        
        if result:
            logger.info("🗑️ Revoked refresh token")
        else:
            logger.warning("⚠️ Refresh token not found for revocation")

    def revoke_all_user_tokens(self, user_id: str):
        """Revoke all refresh tokens for a user"""
        pattern = self.prefix + "*"
        keys = self.redis.keys(pattern)
        
        revoked_count = 0
        for key in keys:
            stored_user_id = self.redis.get(key)
            if stored_user_id and stored_user_id.decode() == user_id:
                self.redis.delete(key)
                revoked_count += 1
        
        logger.info(f"🗑️ Revoked {revoked_count} tokens for user {user_id}")
        return revoked_count
