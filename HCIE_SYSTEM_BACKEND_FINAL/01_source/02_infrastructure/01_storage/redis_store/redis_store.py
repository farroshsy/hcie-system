"""
Redis-backed Feature Store for Mathematical Model
Production-aligned implementation of formal mathematical model
Copied from existing working infrastructure
"""

import redis
import json
import logging
import os
from typing import Dict, Tuple, Optional
import math

logger = logging.getLogger(__name__)

class RedisFeatureStore:
    """
    Redis-backed feature store implementing the mathematical model
    Maps mathematical concepts to Redis hash operations
    """
    
    # 🔥 FIXED: Move constants to class level
    MASTERY_KEY = "mastery:{user_id}"
    BANDIT_KEY = "bandit:{user_id}"
    STATE_KEY = "state:{user_id}"
    CONTEXT_KEY = "context:{user_id}"

    def __init__(self, settings=None):
        """Initialize Redis store with settings injection"""
        self.redis_available = False
        self.fallback_data = {}  # In-memory fallback storage
        self.redis_client = None
        self.client = None
        
        # Store configuration for lazy initialization
        if settings:
            self._redis_host = settings.redis_host
            self._redis_port = settings.redis_port
            self._redis_db = settings.redis_db
            self._redis_password = settings.redis_password
        else:
            self._redis_host = os.getenv('REDIS_HOST', 'localhost')
            self._redis_port = int(os.getenv('REDIS_PORT', 6379))
            self._redis_db = int(os.getenv('REDIS_DB', 0))
            self._redis_password = os.getenv('REDIS_PASSWORD', None)
    
    def _ensure_connected(self):
        """Ensure Redis client is initialized (lazy initialization)"""
        if self.redis_client is None and not self.redis_available:
            try:
                self.redis_client = redis.Redis(
                    host=self._redis_host,
                    port=self._redis_port,
                    db=self._redis_db,
                    password=self._redis_password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                self.redis_client.ping()
                self.redis_available = True
                logger.info(f"✅ Redis connected successfully at {self._redis_host}:{self._redis_port}")
                
                # Store client for DI
                self.client = self.redis_client
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self.redis_available = False
                self.redis_client = None
                self.client = None
        
        return self.redis_client
    
    def get_value(self, key: str):
        """Get value from Redis - stable API for StateAdapter"""
        client = self._ensure_connected()
        if client is None:
            return None
        try:
            return client.get(key)
        except Exception as e:
            logger.error(f"Redis get failed for key {key}: {e}")
            return None
    
    def set_value(self, key: str, value, expire_seconds: Optional[int] = None):
        """Set value in Redis - stable API for StateAdapter"""
        client = self._ensure_connected()
        if client is None:
            return False
        try:
            if expire_seconds:
                client.setex(key, expire_seconds, value)
            else:
                client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis set failed for key {key}: {e}")
            return False
        
        # 🔥 FIXED: Removed duplicate constants - using class-level constants
    
    def get_mastery(self, user_id: str, node: str) -> Tuple[float, float]:
        """
        Get mastery parameters: theta_u,i ~ Beta(alpha, beta)
        
        Args:
            user_id: User identifier
            node: Concept node
            
        Returns:
            Tuple of (alpha, beta) parameters
        """
        client = self._ensure_connected()
        if client is None:
            # Return default novice parameters
            return (1.0, 2.33)  # 1/(1+2.33) = 0.3 novice
        
        try:
            key = self.MASTERY_KEY.format(user_id=user_id)
            alpha = float(client.hget(key, f"{node}:alpha") or 1.0)
            beta = float(client.hget(key, f"{node}:beta") or 2.33)  # 1/(1+2.33) = 0.3 novice
            mastery = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.0
            logger.debug(f"Redis mastery for {user_id}/{node}: alpha={alpha:.3f}, beta={beta:.3f}, mastery={mastery:.3f}")
            return alpha, beta
        except Exception as e:
            logger.error(f"Error getting mastery for user {user_id}, node {node}: {e}")
            return 1.0, 1.0  # Uninformative prior
    
    def set_mastery(self, user_id: str, concept: str, mastery: float):
        """
        Set mastery for a user and concept (for TransferAwareLearner compatibility)
        
        Args:
            user_id: User identifier
            concept: Learning concept
            mastery: Mastery level (0-1)
            
        Returns:
            bool: Success status
        """
        client = self._ensure_connected()
        if client is None:
            return False
            
        try:
            # Convert mastery to alpha/beta parameters
            # Use confidence-based conversion
            confidence = max(0.1, min(10.0, mastery * 10))  # Scale mastery to confidence
            alpha = mastery * confidence
            beta = (1.0 - mastery) * confidence
            
            # Store in Redis
            key = self.MASTERY_KEY.format(user_id=user_id)
            client.hset(key, f"{concept}:alpha", alpha)
            client.hset(key, f"{concept}:beta", beta)
            
            # Set TTL (30 days)
            client.expire(key, 86400 * 30)
            
            logger.debug(f"Set mastery for {user_id}/{concept}: mastery={mastery:.3f} (alpha={alpha:.3f}, beta={beta:.3f})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set mastery for {user_id}/{concept}: {e}")
            return False
    
    def update_mastery_absolute(self, user_id: str, node: str, alpha: float, beta: float):
        """
        Update mastery parameters directly with alpha/beta values
        
        Args:
            user_id: User identifier
            node: Concept node
            alpha: Alpha parameter
            beta: Beta parameter
        """
        client = self._ensure_connected()
        if client is None:
            return
            
        try:
            key = self.MASTERY_KEY.format(user_id=user_id)
            client.hset(key, f"{node}:alpha", alpha)
            client.hset(key, f"{node}:beta", beta)
            client.expire(key, 86400 * 30)
            logger.debug(f"Updated mastery for {user_id}/{node}: alpha={alpha:.3f}, beta={beta:.3f}")
        except Exception as e:
            logger.error(f"Failed to update mastery for {user_id}/{node}: {e}")
    
    # REMOVED: Duplicate clear_user_data function - keeping the one below with return type annotation
    
    def get_bandit_params(self, user_id: str, arm: str) -> Tuple[float, float]:
        """
        Get bandit parameters for Thompson sampling: alpha, beta ~ Beta(alpha, beta)
        
        Args:
            user_id: User identifier
            arm: Arm identifier (concept or representation)
            
        Returns:
            Tuple of (alpha, beta) parameters
        """
        client = self._ensure_connected()
        if client is None:
            return (1.0, 1.0)  # Uninformative prior
            
        try:
            key = self.BANDIT_KEY.format(user_id=user_id)
            alpha = float(client.hget(key, f"{arm}:alpha") or 1.0)
            beta = float(client.hget(key, f"{arm}:beta") or 1.0)
            return (alpha, beta)
        except Exception:
            # Silent fail in fallback mode
            return 1.0, 1.0
    
    def get_representation(self, user_id: str, arm: str) -> Tuple[float, float]:
        """
        Get representation parameters: phi_u,r ~ Beta(alpha, beta)
        
        Args:
            arm: Format "{node}:{representation}"
        
        Returns:
            (alpha, beta) parameters for Beta distribution
        """
        client = self._ensure_connected()
        if client is None:
            return (1.0, 1.0)
            
        key = self.BANDIT_KEY.format(user_id=user_id)
        
        try:
            alpha = float(client.hget(key, f"{arm}:alpha") or 1.0)
            beta = float(client.hget(key, f"{arm}:beta") or 1.0)
            return alpha, beta
        except Exception:
            # Silent fail in fallback mode
            return 1.0, 1.0
        else:
            # Fallback mode - use in-memory storage
            user_key = f"{user_id}:bandit"
            if user_key not in self.fallback_data:
                self.fallback_data[user_key] = {}
            
            bandit_data = self.fallback_data[user_key]
            if arm not in bandit_data:
                bandit_data[arm] = {"alpha": 1.0, "beta": 1.0}
            
            return bandit_data[arm]["alpha"], bandit_data[arm]["beta"]
    
    def update_representation(self, user_id: str, arm: str, reward: float):
        """
        Update representation effectiveness
        
        If reward > 0.5: alpha <- alpha + 1
        If reward <= 0.5: beta <- beta + 1
        """
        client = self._ensure_connected()
        if client is None:
            return
            
        key = self.BANDIT_KEY.format(user_id=user_id)
        
        try:
            if reward > 0.5:
                client.hincrbyfloat(key, f"{arm}:alpha", 1)
            else:
                client.hincrbyfloat(key, f"{arm}:beta", 1)
            
            # Set TTL (14 days for representations)
            client.expire(key, 86400 * 14)
            
            logger.debug(f"Updated representation for user {user_id}, arm {arm}: reward={reward}")
            
        except Exception:
            # Silent fail in fallback mode
            pass
    
    def get_user_context(self, user_id: str) -> Dict[str, any]:
        """
        Get user context for policy decisions
        Includes prev_concept, difficulty_bin, etc.
        """
        client = self._ensure_connected()
        if client is None:
            # Fallback mode - use in-memory storage
            user_key = f"{user_id}:context"
            if user_key not in self.fallback_data:
                self.fallback_data[user_key] = {
                    "prev_concept": None,
                    "difficulty_bin": "medium", 
                    "last_interaction": 0,
                    "policy_mode": "hcie"
                }
            
            return self.fallback_data[user_key]
            
        key = self.CONTEXT_KEY.format(user_id=user_id)
        
        try:
            context_data = client.hgetall(key)
            return {
                "policy_mode": context_data.get("policy_mode", "hcie"),
                "prev_concept": context_data.get("prev_concept") or "START",  
                "difficulty_bin": context_data.get("difficulty_bin"),
                "last_interaction": float(context_data.get("last_interaction", 0)),
                "real_components": context_data.get("real_components")
            }
        except Exception:
            # Silent fail in fallback mode
            return {"prev_concept": None, "difficulty_bin": "medium", "last_interaction": 0, "policy_mode": "hcie"}
    
    def update_user_context(self, user_id: str, context: Dict[str, any]):
        """
        Update user context for policy decisions
        """
        client = self._ensure_connected()
        if client is None:
            return
            
        key = self.CONTEXT_KEY.format(user_id=user_id)
        
        try:
            for field, value in context.items():
                if value is not None:
                    client.hset(key, field, str(value))
            
            # Set TTL (7 days for context)
            client.expire(key, 86400 * 7)
            
            logger.debug(f"Updated context for user {user_id}: {context}")
            
        except Exception:
            # Silent fail in fallback mode
            pass
    
    def get_user_mastery(self, user_id: str, concept_id: str = None) -> Dict[str, float]:
        """
        Get user mastery for specific concept or all concepts
        
        Returns:
            Dict with concept -> mastery_level or single mastery value
        """
        key = self.MASTERY_KEY.format(user_id=user_id)
        
        try:
            if concept_id:
                # Get specific concept mastery
                alpha = float(self.redis_client.hget(key, f"{concept_id}:alpha") or 1.0)
                beta = float(self.redis_client.hget(key, f"{concept_id}:beta") or 1.0)
                return {concept_id: alpha / (alpha + beta) if (alpha + beta) > 0 else 0.5}
            else:
                # Get all mastery
                mastery_data = self.redis_client.hgetall(key)
                result = {}
                for field, value in mastery_data.items():
                    if ":" in field:
                        concept, param = field.split(":", 1)
                        if concept not in result:
                            result[concept] = {"alpha": 1.0, "beta": 1.0}
                        result[concept][param] = float(value)
                
                # Convert to mastery levels
                return {k: (v["alpha"] / (v["alpha"] + v["beta"])) if (v["alpha"] + v["beta"]) > 0 else 0.5 
                       for k, v in result.items()}
        except Exception:
            # Fallback to default mastery
            return {concept_id: 0.3} if concept_id else {}
    
    # REMOVED: get_ct_mastery function - was causing state corruption
    # All mastery should use the unified Bayesian model via get_mastery()
    
    def get_user_representation_summary(self, user_id: str) -> Dict[str, Dict[str, float]]:
        """
        Get complete representation effectiveness summary for user
        """
        key = self.BANDIT_KEY.format(user_id=user_id)
        
        try:
            rep_data = self.redis_client.hgetall(key)
            summary = {}
            
            for field, value in rep_data.items():
                if ":" in field:
                    arm, param = field.split(":", 1)
                    
                    if arm not in summary:
                        summary[arm] = {"alpha": 1.0, "beta": 1.0}
                    
                    summary[arm][param] = float(value)
            
            # Calculate derived statistics
            for arm, params in summary.items():
                alpha = params["alpha"]
                beta = params["beta"]
                
                mean = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.5
                variance = (alpha * beta) / (
                    (alpha + beta) ** 2 * (alpha + beta + 1)
                ) if (alpha + beta) > 0 else 0.25
                
                summary[arm].update({
                    "mean": mean,
                    "variance": variance,
                    "uncertainty": math.sqrt(variance),
                    "samples": alpha + beta
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting representation summary for user {user_id}: {e}")
            return {}
    
    def get_user_mastery_summary(self, user_id: str) -> Dict[str, Dict[str, float]]:
        """
        Get summary of user's mastery across all concepts
        """
        try:
            if not self.redis_available:
                return {}
            
            # Get all mastery keys for user
            pattern = f"mastery:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            
            summary = {}
            for key in keys:
                concept_id = key.split(":")[-1]
                alpha, beta = self.get_mastery(user_id, concept_id)
                summary[concept_id] = {
                    "alpha": alpha,
                    "beta": beta,
                    "mean": self._beta_mean(alpha, beta),
                    "uncertainty": self._beta_uncertainty(alpha, beta)
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting user mastery summary: {e}")
            return {}
    
    def append_interaction(self, user_id: str, interaction_data: Dict[str, any]):
        """
        Append interaction to user history for behavior policy estimation
        🔥 CRITICAL for Phase 4 alignment
        """
        try:
            if not self.redis_available:
                return
            
            # Store interaction in list
            history_key = f"history:{user_id}"
            self.redis_client.lpush(history_key, json.dumps(interaction_data))
            
            # Keep only last 100 interactions to prevent memory bloat
            self.redis_client.ltrim(history_key, 0, 99)
            
        except Exception as e:
            logger.error(f"Error appending interaction: {e}")
    
    def clear_user_data(self, user_id: str) -> bool:
        """Clear all data for a user (for testing/recovery)"""
        try:
            keys = [
                self.MASTERY_KEY.format(user_id=user_id),
                self.BANDIT_KEY.format(user_id=user_id),
                self.STATE_KEY.format(user_id=user_id),
                self.CONTEXT_KEY.format(user_id=user_id)
            ]
            
            for key in keys:
                self.redis_client.delete(key)
            
            logger.info(f"Cleared all data for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing user data for {user_id}: {e}")
            return False
    
    def get_user_stats(self, user_id: str) -> Dict[str, any]:
        """Get overall user statistics"""
        try:
            mastery_summary = self.get_user_mastery_summary(user_id)
            rep_summary = self.get_user_representation_summary(user_id)
            
            # Calculate overall statistics
            total_mastery_samples = sum(params.get("samples", 0) for params in mastery_summary.values())
            total_rep_samples = sum(params.get("samples", 0) for params in rep_summary.values())
            
            avg_mastery = 0
            if mastery_summary:
                avg_mastery = sum(params.get("mean", 0) for params in mastery_summary.values()) / len(mastery_summary)
            
            return {
                "user_id": user_id,
                "total_mastery_nodes": len(mastery_summary),
                "total_representation_arms": len(rep_summary),
                "total_mastery_samples": total_mastery_samples,
                "total_representation_samples": total_rep_samples,
                "average_mastery": avg_mastery,
                "unique_nodes_learned": len([n for n, p in mastery_summary.items() if p.get("samples", 0) > 2])
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return {"user_id": user_id, "error": str(e)}

# Factory function
def create_redis_feature_store(redis_host: str = "localhost", redis_port: int = 6379) -> RedisFeatureStore:
    """Create and return a configured Redis feature store"""
    # Create a simple settings object with the required attributes
    class SimpleSettings:
        def __init__(self, host, port):
            self.redis_host = host
            self.redis_port = port
            self.redis_db = 0
            self.redis_password = None
    
    settings = SimpleSettings(redis_host, redis_port)
    return RedisFeatureStore(settings)
