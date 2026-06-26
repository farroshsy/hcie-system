"""
Read-Mode Cache Service - High-performance caching for dashboard queries
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ReadModeCache:
    """Redis-based cache for read-mode queries with TTL and invalidation"""

    def __init__(self, redis_client=None, default_ttl: int = 300):
        """Initialize cache with Redis client and TTL"""
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "invalidations": 0,
        }

    def _get_cache_key(self, user_id: str, concept: str) -> str:
        """Generate cache key for user/concept mastery"""
        return f"read_mastery:{user_id}:{concept}"

    def get_cached_mastery(self, user_id: str, concept: str) -> Optional[float]:
        """
        Get cached mastery for user/concept pair

        Returns:
            mastery value if cached, None if not cached or expired
        """
        if not self.redis_client:
            return None

        cache_key = self._get_cache_key(user_id, concept)

        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                cache_entry = json.loads(cached_data)

                cache_time = datetime.fromisoformat(cache_entry["timestamp"])
                if datetime.utcnow() - cache_time < timedelta(seconds=cache_entry["ttl"]):
                    self.cache_stats["hits"] += 1
                    logger.debug(
                        "Cache HIT: %s/%s = %.3f",
                        user_id,
                        concept,
                        cache_entry["mastery"],
                    )
                    return cache_entry["mastery"]

                self.redis_client.delete(cache_key)
                self.cache_stats["misses"] += 1
                logger.debug("Cache EXPIRED: %s/%s", user_id, concept)
                return None

            self.cache_stats["misses"] += 1
            logger.debug("Cache MISS: %s/%s", user_id, concept)
            return None

        except Exception as e:
            logger.error("Cache get error for %s/%s: %s", user_id, concept, e)
            self.cache_stats["misses"] += 1
            return None

    def set_cached_mastery(
        self,
        user_id: str,
        concept: str,
        mastery: float,
        ttl: Optional[int] = None,
    ):
        """Cache mastery for user/concept pair."""
        if not self.redis_client:
            return

        cache_key = self._get_cache_key(user_id, concept)
        cache_ttl = ttl or self.default_ttl

        cache_entry = {
            "mastery": mastery,
            "timestamp": datetime.utcnow().isoformat(),
            "ttl": cache_ttl,
            "user_id": user_id,
            "concept": concept,
        }

        try:
            self.redis_client.setex(cache_key, cache_ttl, json.dumps(cache_entry))
            self.cache_stats["sets"] += 1
            logger.debug(
                "Cache SET: %s/%s = %.3f (TTL: %ss)",
                user_id,
                concept,
                mastery,
                cache_ttl,
            )

        except Exception as e:
            logger.error("Cache set error for %s/%s: %s", user_id, concept, e)

    def invalidate_user_cache(self, user_id: str, concept: Optional[str] = None):
        """Invalidate cache for user (all concepts) or a specific concept."""
        if not self.redis_client:
            return

        try:
            if concept:
                cache_key = self._get_cache_key(user_id, concept)
                self.redis_client.delete(cache_key)
                logger.debug("Cache INVALIDATE: %s/%s", user_id, concept)
            else:
                pattern = f"read_mastery:{user_id}:*"
                keys = self.redis_client.keys(pattern)
                for key in keys:
                    self.redis_client.delete(key)
                logger.debug("Cache INVALIDATE ALL: %s (%s keys)", user_id, len(keys))

            self.cache_stats["invalidations"] += 1

        except Exception as e:
            logger.error("Cache invalidate error for %s: %s", user_id, e)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "sets": self.cache_stats["sets"],
            "invalidations": self.cache_stats["invalidations"],
            "hit_rate": f"{hit_rate:.1f}%",
            "total_requests": total_requests,
        }

    def clear_all_cache(self):
        """Clear all cached data (for testing)."""
        if not self.redis_client:
            return

        try:
            pattern = "read_mastery:*"
            keys = self.redis_client.keys(pattern)
            for key in keys:
                self.redis_client.delete(key)

            self.cache_stats = {"hits": 0, "misses": 0, "sets": 0, "invalidations": 0}
            logger.info("Cache CLEARED: %s entries", len(keys))

        except Exception as e:
            logger.error("Cache clear error: %s", e)

    def _get_projection_key(self, user_id: str) -> str:
        return f"learner_projection:{user_id}:latest"

    def get_cached_projection(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached learner projection payload. Cache is never authority."""
        if not self.redis_client:
            return None
        try:
            cached_data = self.redis_client.get(self._get_projection_key(user_id))
            if not cached_data:
                self.cache_stats["misses"] += 1
                return None
            self.cache_stats["hits"] += 1
            return json.loads(cached_data)
        except Exception as e:
            logger.error("Projection cache get error for %s: %s", user_id, e)
            self.cache_stats["misses"] += 1
            return None

    def set_cached_projection(
        self,
        user_id: str,
        projection: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """Cache a derived projection with TTL; backing Postgres row remains authority."""
        if not self.redis_client:
            return
        try:
            cache_ttl = ttl or self.default_ttl
            self.redis_client.setex(
                self._get_projection_key(user_id),
                cache_ttl,
                json.dumps(projection, default=str),
            )
            self.cache_stats["sets"] += 1
        except Exception as e:
            logger.error("Projection cache set error for %s: %s", user_id, e)
