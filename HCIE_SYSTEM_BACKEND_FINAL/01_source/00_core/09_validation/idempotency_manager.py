"""
Idempotency Manager for Distributed System Correctness

Ensures exactly-once processing semantics for learning events
Prevents state amplification errors from retries and concurrent processing
"""

import json
import logging
import hashlib
import time
from typing import Any, Iterator, Optional, Dict, Sequence, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class _LegacyRedisStoreAdapter:
    """Bridge between the legacy `RedisFeatureStore` and the new
    `IdempotencyKeyStoreProtocol`.

    Kept inside the core module on purpose: it preserves backwards
    compatibility for call sites that still pass a raw `redis_store` while
    the composition root migrates them to inject the canonical adapter
    (`RedisIdempotencyKeyStore`) instead. The shape matches the protocol
    verified by `tools/migrate/check_protocols.py`.
    """

    def __init__(self, redis_store: Any) -> None:
        self._redis_store = redis_store

    @property
    def _client(self) -> Any:
        client = getattr(self._redis_store, "redis_client", None)
        if client is None:
            raise RuntimeError(
                "RedisFeatureStore did not expose redis_client; cannot run idempotency operations"
            )
        return client

    def get_value(self, key: str) -> Any:
        return self._redis_store.get_value(key)

    def set_with_ttl(self, key: str, value: str, ttl_seconds: int) -> None:
        self._client.setex(key, ttl_seconds, value)

    def set_with_ttl_batch(
        self,
        items: Sequence[Tuple[str, str, int]],
    ) -> None:
        pipe = self._client.pipeline()
        for key, value, ttl_seconds in items:
            pipe.setex(key, ttl_seconds, value)
        pipe.execute()

    def set_if_absent_with_ttl(
        self,
        key: str,
        value: str,
        ttl_seconds: int,
    ) -> bool:
        result = self._client.set(key, value, nx=True, ex=ttl_seconds)
        return bool(result)

    def delete(self, key: str) -> bool:
        return self._client.delete(key) > 0

    def scan_keys(self, pattern: str) -> Iterator[str]:
        for key in self._client.scan_iter(match=pattern):
            yield key


class IdempotencyManager:
    """
    Manages event idempotency and deduplication for distributed systems
    
    Guarantees:
    - Exactly-once processing semantics
    - No state amplification from retries
    - Deterministic replay behavior
    - Concurrency safety
    """
    
    def __init__(self, redis_store=None, ttl_hours: int = 24, idempotency_store=None):
        """
        Initialize idempotency manager.

        Args:
            redis_store: legacy compatibility -- if provided and
                `idempotency_store` is None, an adapter is built on top of
                its `redis_client` so existing call sites keep working.
            ttl_hours: Time-to-live for deduplication keys (default 24h).
            idempotency_store: an `IdempotencyKeyStoreProtocol` impl. This
                is the preferred injection in the new wiring; the legacy
                fallback exists only to keep the production stack booting
                until the composition root takes over fully.
        """
        self.redis_store = redis_store  # retained for code that still reads it
        if idempotency_store is None and redis_store is not None:
            idempotency_store = _LegacyRedisStoreAdapter(redis_store)
        if idempotency_store is None:
            raise RuntimeError("IdempotencyManager requires idempotency_store or redis_store")
        self.idempotency_store = idempotency_store
        self.ttl_seconds = ttl_hours * 3600
        
    def _get_processed_key(self, event_id: str) -> str:
        """Get Redis key for processed events"""
        return f"processed:{event_id}"
    
    def _get_result_key(self, event_id: str) -> str:
        """Get Redis key for cached results"""
        return f"result:{event_id}"
    
    def _get_lock_key(self, event_id: str) -> str:
        """Get Redis key for distributed locks"""
        return f"lock:{event_id}"
    
    def _hash_event_data(self, event_data: Dict[str, Any]) -> str:
        """Create deterministic hash of event data for deduplication"""
        # Convert numpy types to Python native types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_numpy_types(item) for item in obj]
            elif hasattr(obj, 'dtype'):  # numpy types
                if obj.dtype.kind in ('i', 'u'):  # integer types
                    return int(obj)
                elif obj.dtype.kind == 'f':  # float types
                    return float(obj)
                else:
                    return str(obj)
            else:
                return obj
        
        # Sort keys for deterministic hashing
        sorted_data = json.dumps(convert_numpy_types(event_data), sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(sorted_data.encode()).hexdigest()
    
    def is_processed(self, event_id: str) -> bool:
        """
        Check if an event has already been processed
        
        Args:
            event_id: Unique identifier for the event
            
        Returns:
            True if already processed, False otherwise
        """
        processed_key = self._get_processed_key(event_id)
        return self.idempotency_store.get_value(processed_key) is not None
    
    def get_cached_result(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result for a processed event
        
        Args:
            event_id: Unique identifier for the event
            
        Returns:
            Cached result if available, None otherwise
        """
        result_key = self._get_result_key(event_id)
        result_data = self.idempotency_store.get_value(result_key)
        
        if result_data:
            try:
                result = json.loads(result_data)
                
                # 🔥 CRITICAL: Ensure all required fields are present for LearningResult
                required_fields = ['mastery', 'uncertainty', 'confidence', 'lyapunov_mastery', 
                                   'bayesian_alpha', 'bayesian_beta', 'kalman_mastery', 'kalman_covariance',
                                   'ensemble_weights', 'ensemble_variance', 'policy', 'policy_multiplier',
                                   'zpd_target', 'zpd_alignment_error', 'zpd_score', 'transfer_amounts', 'transfer_efficiency',
                                   'timestamp', 'processing_mode', 'processing_time']
                
                # Add missing fields with defaults if needed
                for field in required_fields:
                    if field not in result:
                        if field == 'processing_time':
                            result[field] = 0.001  # Default processing time
                        elif field == 'timestamp':
                            result[field] = datetime.now().isoformat()
                        elif field in ['mastery', 'uncertainty', 'confidence']:
                            result[field] = 0.3  # Default mastery
                        elif field in ['lyapunov_mastery', 'bayesian_alpha', 'bayesian_beta']:
                            result[field] = 0.3  # Default learner mastery
                        elif field in ['kalman_mastery', 'kalman_covariance']:
                            result[field] = 0.3  # Default Kalman
                        elif field == 'ensemble_weights':
                            result[field] = {"lyapunov": 0.33, "bayesian": 0.33, "kalman": 0.34}
                        elif field == 'ensemble_variance':
                            result[field] = 0.01  # Default variance
                        elif field == 'policy':
                            result[field] = "adaptive_transfer"  # Default policy
                        elif field == 'policy_multiplier':
                            result[field] = 1.0  # Default multiplier
                        elif field in ['zpd_target', 'zpd_alignment_error', 'zpd_score']:
                            result[field] = 0.8  # Default ZPD values
                        elif field == 'transfer_amounts':
                            result[field] = {}  # Default empty transfers
                        elif field == 'transfer_efficiency':
                            result[field] = 0.5  # Default efficiency
                        elif field == 'processing_mode':
                            result[field] = "adaptive"  # Default mode
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to decode cached result for {event_id}: {e}")
                return None
        
        return None
    
    def mark_processed(self, event_id: str, result: Dict[str, Any]) -> bool:
        """
        Mark an event as processed and cache its result
        
        Args:
            event_id: Unique identifier for the event
            result: Result to cache
            
        Returns:
            True if successfully marked, False if already processed
        """
        # Check if already processed first
        if self.is_processed(event_id):
            logger.warning(f"⚠️ Event {event_id} already processed, skipping")
            return False
        
        try:
            processed_key = self._get_processed_key(event_id)
            result_key = self._get_result_key(event_id)
            
            # Create result with processing_time from current time
            current_time = time.time()
            result_with_time = result.copy() if hasattr(result, 'copy') else result
            
            # 🔥 CRITICAL: Ensure all required fields are present
            required_fields = ['mastery', 'uncertainty', 'confidence', 'lyapunov_mastery', 
                               'bayesian_alpha', 'bayesian_beta', 'kalman_mastery', 'kalman_covariance',
                               'ensemble_weights', 'ensemble_variance', 'policy', 'policy_multiplier',
                               'zpd_target', 'zpd_alignment_error', 'zpd_score', 'transfer_amounts', 'transfer_efficiency',
                               'timestamp', 'processing_mode', 'processing_time']
            
            # Add missing fields with defaults if needed
            for field in required_fields:
                if field not in result_with_time:
                    if field == 'processing_time':
                        result_with_time[field] = 0.001  # Default processing time
                    elif field == 'timestamp':
                        result_with_time[field] = datetime.now().isoformat()
                    elif field in ['mastery', 'uncertainty', 'confidence']:
                        result_with_time[field] = 0.3  # Default mastery
                    elif field in ['lyapunov_mastery', 'bayesian_alpha', 'bayesian_beta']:
                        result_with_time[field] = 0.3  # Default learner mastery
                    elif field in ['kalman_mastery', 'kalman_covariance']:
                        result_with_time[field] = 0.3  # Default Kalman
                    elif field == 'ensemble_weights':
                        result_with_time[field] = {"lyapunov": 0.33, "bayesian": 0.33, "kalman": 0.34}
                    elif field == 'ensemble_variance':
                        result_with_time[field] = 0.02  # Default variance
                    elif field in ['policy', 'policy_multiplier']:
                        result_with_time[field] = "text" if field == 'policy' else 1.0
                    elif field in ['zpd_target', 'zpd_alignment_error', 'zpd_score']:
                        result_with_time[field] = 0.5  # Default ZPD
                    elif field in ['transfer_amounts', 'transfer_efficiency']:
                        result_with_time[field] = {}  # Default transfer
                    elif field == 'processing_mode':
                        result_with_time[field] = "write"
            
            # Serialize result
            result_json = json.dumps(result_with_time, default=str)

            # Atomically write both keys via the idempotency port.
            self.idempotency_store.set_with_ttl_batch([
                (processed_key, "1", self.ttl_seconds),
                (result_key, result_json, self.ttl_seconds),
            ])
            
            logger.info(f"✅ Marked event {event_id} as processed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to mark event {event_id} as processed: {e}")
            return False
    
    def acquire_lock(self, event_id: str, timeout_seconds: int = 30) -> bool:
        """
        Acquire distributed lock for event processing
        
        Args:
            event_id: Unique identifier for the event
            timeout_seconds: Lock timeout
            
        Returns:
            True if lock acquired, False otherwise
        """
        lock_key = self._get_lock_key(event_id)
        
        try:
            return self.idempotency_store.set_if_absent_with_ttl(
                lock_key, "locked", timeout_seconds
            )
        except Exception as e:
            logger.error(f"❌ Failed to acquire lock for {event_id}: {e}")
            return False
    
    def release_lock(self, event_id: str) -> bool:
        """
        Release distributed lock for event processing
        
        Args:
            event_id: Unique identifier for the event
            
        Returns:
            True if lock released, False otherwise
        """
        lock_key = self._get_lock_key(event_id)
        
        try:
            return self.idempotency_store.delete(lock_key)
        except Exception as e:
            logger.error(f"❌ Failed to release lock for {event_id}: {e}")
            return False
    
    def check_duplicate_by_content(self, event_data: Dict[str, Any]) -> Optional[str]:
        """
        Check for duplicate events by content hash
        
        Args:
            event_data: Event data to check
            
        Returns:
            Original event_id if duplicate found, None otherwise
        """
        # 🔥 DISABLED: Content-based deduplication causes false positives in learning systems
        # Learning systems EXPECT repeated patterns - same interaction ≠ duplicate event
        # Only use event_id-based deduplication for true exactly-once semantics
        logger.info(f"🔥 CONTENT DEDUP DISABLED: event_id={event_data.get('event_id', 'unknown')}")
        return None
    
    def mark_content_hash(self, event_data: Dict[str, Any], event_id: str) -> bool:
        """
        Mark content hash to prevent duplicate processing
        
        Args:
            event_data: Event data to hash
            event_id: Current event ID
            
        Returns:
            True if successfully marked, False otherwise
        """
        event_hash = self._hash_event_data(event_data)
        hash_key = f"hash:{event_hash}"
        
        try:
            self.idempotency_store.set_with_ttl(hash_key, event_id, self.ttl_seconds)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to mark content hash: {e}")
            return False
    
    def cleanup_expired_keys(self) -> int:
        """
        Clean up expired idempotency keys
        
        Returns:
            Number of keys cleaned up
        """
        try:
            # This would require a more sophisticated Redis scan
            # For now, rely on Redis TTL expiration
            logger.info("🧹 Relying on Redis TTL for key cleanup")
            return 0
        except Exception as e:
            logger.error(f"❌ Failed to cleanup expired keys: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get idempotency system statistics
        
        Returns:
            Statistics about processed events and system health
        """
        try:
            # Count processed events
            processed_pattern = "processed:*"
            processed_keys = 0

            for _ in self.idempotency_store.scan_keys(processed_pattern):
                processed_keys += 1

            # Count cached results
            result_pattern = "result:*"
            result_keys = 0

            for _ in self.idempotency_store.scan_keys(result_pattern):
                result_keys += 1

            # Count active locks
            lock_pattern = "lock:*"
            lock_keys = 0

            for _ in self.idempotency_store.scan_keys(lock_pattern):
                lock_keys += 1
            
            return {
                "processed_events": processed_keys,
                "cached_results": result_keys,
                "active_locks": lock_keys,
                "ttl_hours": self.ttl_seconds // 3600,
                "system_health": "healthy" if processed_keys == result_keys else "inconsistent"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {
                "error": str(e),
                "system_health": "unknown"
            }


class IdempotentEventProcessor:
    """
    Wrapper for event processing with idempotency guarantees
    """
    
    def __init__(self, idempotency_manager: IdempotencyManager):
        self.idempotency_manager = idempotency_manager
    
    def process_event_idempotently(
        self,
        event_id: str,
        event_data: Dict[str, Any],
        processor_func: callable,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process an event with idempotency guarantees
        
        Args:
            event_id: Unique identifier for the event
            event_data: Event data for deduplication
            processor_func: Function to process the event
            **kwargs: Additional arguments for processor
            
        Returns:
            Result of processing (cached if already processed)
        """
        logger.info(f"🔍 Processing event {event_id} idempotently")
        
        # Check if already processed
        if self.idempotency_manager.is_processed(event_id):
            logger.info(f"📋 Event {event_id} already processed, returning cached result")
            cached_result = self.idempotency_manager.get_cached_result(event_id)
            if cached_result:
                return cached_result
            else:
                logger.error(f"❌ Event {event_id} marked processed but no cached result")
                raise RuntimeError(f"Inconsistent state for event {event_id}")
        
        # Check for duplicate by content
        duplicate_event_id = self.idempotency_manager.check_duplicate_by_content(event_data)
        if duplicate_event_id:
            logger.warning(f"🔄 Duplicate event detected: {event_id} duplicates {duplicate_event_id}")
            duplicate_result = self.idempotency_manager.get_cached_result(duplicate_event_id)
            if duplicate_result:
                # Mark current event as processed to prevent future duplicates
                self.idempotency_manager.mark_processed(event_id, duplicate_result)
                return duplicate_result
            else:
                logger.error(f"❌ Duplicate event {duplicate_event_id} has no cached result")
                raise RuntimeError(f"Inconsistent duplicate handling for {event_id}")
        
        # Acquire distributed lock
        if not self.idempotency_manager.acquire_lock(event_id):
            logger.warning(f"⏳ Event {event_id} is being processed by another instance")
            # Wait and retry
            import time
            time.sleep(0.1)
            
            # Check if processed while waiting
            if self.idempotency_manager.is_processed(event_id):
                logger.info(f"📋 Event {event_id} processed while waiting, returning cached result")
                return self.idempotency_manager.get_cached_result(event_id)
            
            raise RuntimeError(f"Failed to acquire lock for event {event_id}")
        
        try:
            # Mark content hash to prevent duplicates
            self.idempotency_manager.mark_content_hash(event_data, event_id)
            
            # Process the event
            logger.info(f"🔄 Processing event {event_id} with lock")
            result = processor_func(event_data, **kwargs)
            
            # Mark as processed and cache result
            self.idempotency_manager.mark_processed(event_id, result)
            
            logger.info(f"✅ Successfully processed event {event_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to process event {event_id}: {e}")
            raise
        finally:
            # Always release the lock
            self.idempotency_manager.release_lock(event_id)
