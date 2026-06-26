"""
🔥 POSTGRES LEARNING STATE REPOSITORY - Phase 4 Implementation
Postgres as source of truth, Redis as cache only

Phase E1 - Ownership Enforcement:
Only UnifiedBrain and ReplayEngine may mutate canonical cognition fields.
Everything else becomes read-only derived topology.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from core.learning.numpy_converter import serialize_for_storage, assert_no_numpy_leakage

logger = logging.getLogger(__name__)


class LearningStateRepository:
    """
    🔥 POSTGRES SOURCE OF TRUTH for learning state
    Redis becomes cache-only for performance
    
    Phase E1 - Ownership Enforcement:
    Repository-level guards for canonical cognition writes.
    Only UnifiedBrain and ReplayEngine may mutate canonical cognition fields.
    """
    
    def __init__(self, postgres_store, redis_store=None):
        self.postgres_store = postgres_store
        self.redis_store = redis_store  # Optional cache layer
        
        # Import ownership enforcement (lazy import to avoid circular deps)
        try:
            from core.ownership.ownership_enforcement import get_ownership_enforcement
            self.ownership = get_ownership_enforcement()
        except ImportError:
            logger.warning("⚠️  Ownership enforcement module not available - enforcement disabled")
            self.ownership = None
        
        # Import canonical schema validation (lazy import to avoid circular deps)
        try:
            from core.ownership.canonical_schema import get_canonical_schema_registry
            self.schema_registry = get_canonical_schema_registry()
        except ImportError:
            logger.warning("⚠️  Canonical schema registry not available - schema validation disabled")
            self.schema_registry = None
        
        # Ensure Postgres table exists
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create learning_state table if it doesn't exist"""
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS learning_state (
                user_id uuid NOT NULL,
                concept VARCHAR(255) NOT NULL,
                state_data JSONB NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                PRIMARY KEY (user_id, concept)
            );
            
            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_learning_state_user_id ON learning_state(user_id);
            CREATE INDEX IF NOT EXISTS idx_learning_state_concept ON learning_state(concept);
            CREATE INDEX IF NOT EXISTS idx_learning_state_updated_at ON learning_state(updated_at);
            
            -- JSONB indexes for querying state data
            CREATE INDEX IF NOT EXISTS idx_learning_state_mastery ON learning_state USING GIN ((state_data->'mastery'));
            CREATE INDEX IF NOT EXISTS idx_learning_state_uncertainty ON learning_state USING GIN ((state_data->'uncertainty'));
            """
            
            self.postgres_store.execute_write(create_table_sql)
            logger.info("✅ Learning state table ensured in Postgres")
            
        except Exception as e:
            logger.error(f"❌ Failed to create learning_state table: {e}")
            raise
    
    def _validate_state_data(self, state_data: Dict[str, Any], source: str = "unknown") -> bool:
        """Validate canonical state schema integrity"""
        required_fields = ['mastery', 'uncertainty', 'zpd_score']
        missing_fields = [field for field in required_fields if field not in state_data]
        
        if missing_fields:
            logger.error(f"❌ CORRUPTED STATE from {source}: missing fields: {missing_fields}")
            return False
        
        mastery = state_data.get('mastery', 0.3)
        if not isinstance(mastery, (int, float)) or mastery < 0 or mastery > 1:
            logger.error(f"❌ CORRUPTED STATE from {source}: invalid mastery: {mastery}")
            return False
            
        return True
    
    def _serialize_state(self, state_data: Dict[str, Any]) -> str:
        """Safely serialize state data to JSON with NumPy type conversion"""
        try:
            # Convert NumPy types to native Python types for JSON serialization
            converted_data = serialize_for_storage(state_data, validate=True)
            return json.dumps(converted_data)
        except (TypeError, ValueError) as e:
            logger.error(f"❌ JSON serialization failed: {e}")
            raise
        except AssertionError as e:
            logger.error(f"❌ NumPy type leakage detected: {e}")
            raise
    
    def get_state(self, user_id: str, concept: str) -> Optional[Dict[str, Any]]:
        """
        Get learning state with lazy hydration: Redis → Postgres → Redis cache
        Ensures temporal consistency across restarts
        """
        cache_key = f"learning_state:{user_id}:{concept}"
        
        # STEP 1: Try Redis cache first (fast path)
        if self.redis_store:
            cached_data = self.redis_store.get_value(cache_key)
            
            if cached_data:
                try:
                    state_data = json.loads(cached_data)
                    
                    # Validate cached data (defense against stale/corrupted cache)
                    if not self._validate_state_data(state_data, source="cache"):
                        logger.warning(f"⚠️ Cache corruption: {user_id}/{concept} - will hydrate from Postgres")
                    else:
                        logger.debug(f"📖 Cache HIT: {user_id}/{concept}")
                        return state_data
                        
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Cache corruption (invalid JSON): {user_id}/{concept} - will hydrate from Postgres")
        
        # STEP 2: Hydrate from Postgres (source of truth)
        try:
            sql = """
            SELECT state_data, updated_at 
            FROM learning_state 
            WHERE user_id = %s AND concept = %s
            """
            
            result = self.postgres_store.execute_read(sql, (user_id, concept), fetch_one=True)
            
            if result:
                state_data = dict(result['state_data'])  # Copy to avoid mutating store cache
                state_data['updated_at'] = result['updated_at'].isoformat()
                
                # Validate canonical state schema integrity
                if not self._validate_state_data(state_data, source="postgres"):
                    return None
                
                # STEP 3: Update Redis cache (hydrate for future reads)
                if self.redis_store:
                    try:
                        self.redis_store.set_value(
                            cache_key, 
                            self._serialize_state(state_data), 
                            expire_seconds=3600
                        )
                        logger.debug(f"📖 Cache HYDRATED: {user_id}/{concept}")
                    except Exception as cache_error:
                        logger.warning(f"⚠️ Failed to update Redis cache: {cache_error}")
                
                logger.debug(f"📖 Retrieved VALID state from Postgres: {user_id}/{concept}")
                return state_data
            else:
                logger.debug(f"📖 No state found in Postgres: {user_id}/{concept}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get state from Postgres: {e}")
            
            # STRICT MODE: No Redis fallback - Postgres is ONLY source of truth
            # If Postgres fails, we fail fast rather than return potentially stale data
            logger.error(f"❌ CRITICAL: Postgres unavailable for {user_id}/{concept} - no fallback")
            return None
    
    def save_state(self, user_id: str, concept: str, state_data: Dict[str, Any]) -> bool:
        """
        Save learning state to Postgres (source of truth)
        Updates Redis cache after successful commit

        Phase E1 - Ownership Enforcement:
        Validates that canonical cognition writes are only performed by approved writers.
        """
        try:
            # 🔥 CRITICAL: Set ownership context for experiment writes
            if self.ownership:
                from core.ownership.ownership_enforcement import CognitionWriter
                import inspect
                caller_module = inspect.currentframe().f_back.f_code.co_name
                # Set writer context before validation
                self.ownership.set_writer(CognitionWriter.EXPERIMENT)
                self.ownership.validate_state_mutation(state_data, caller_module)
            
            # Phase E1.4: Validate canonical schema before write
            if self.schema_registry:
                is_valid, errors = self.schema_registry.validate_tier1_state(state_data)
                if not is_valid:
                    logger.error(f"❌ Canonical schema validation failed: {errors}")
                    raise ValueError(f"Canonical state validation failed: {errors}")
            
            # CRITICAL: Save to Postgres first (source of truth)
            sql = """
            INSERT INTO learning_state (user_id, concept, state_data, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (user_id, concept) 
            DO UPDATE SET 
                state_data = EXCLUDED.state_data,
                updated_at = NOW()
            RETURNING updated_at
            """
            
            # Remove timestamp from state_data (Postgres manages it)
            state_to_save = state_data.copy()
            state_to_save.pop('updated_at', None)

            result = self.postgres_store.execute_write(
                sql,
                (user_id, concept, self._serialize_state(state_to_save)),
                fetch_one=True
            )
            
            if result:
                # CACHE: Update Redis cache AFTER successful Postgres commit
                # Build a fresh dict to avoid mutating caller's state_data
                cache_data = state_to_save.copy()
                cache_data['updated_at'] = result['updated_at'].isoformat()
                
                if self.redis_store:
                    try:
                        cache_key = f"learning_state:{user_id}:{concept}"
                        self.redis_store.set_value(
                            cache_key, 
                            self._serialize_state(cache_data), 
                            expire_seconds=3600
                        )
                    except Exception as cache_error:
                        logger.warning(f"⚠️ Failed to update Redis cache: {cache_error}")
                
                logger.debug(f"💾 Saved state to Postgres: {user_id}/{concept}")

                # 🔥 CRITICAL: Clear ownership context after write
                if self.ownership:
                    self.ownership.clear_writer()

                return True
            else:
                logger.error(f"❌ Failed to save state to Postgres: {user_id}/{concept}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to save state to Postgres: {e}")
            return False
    
    def get_user_concepts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all concepts for a user"""
        try:
            sql = """
            SELECT concept, state_data, updated_at
            FROM learning_state 
            WHERE user_id = %s
            ORDER BY updated_at DESC
            """
            
            results = self.postgres_store.execute_read(sql, (user_id,), fetch_one=False)
            
            concepts = []
            for result in results:
                state_data = dict(result['state_data'])  # Copy to avoid mutating store internals
                state_data['updated_at'] = result['updated_at'].isoformat()
                concepts.append({
                    'concept': result['concept'],
                    'state_data': state_data,
                    'updated_at': result['updated_at'].isoformat()
                })
            
            return concepts
            
        except Exception as e:
            logger.error(f"❌ Failed to get user concepts: {e}")
            return []  # Fixed: return empty list instead of False

    def batch_save_states(self, batched_writes: List[Dict[str, Any]]) -> bool:
        """
        BULLETPROOF: Save multiple states in a single atomic transaction
        Prevents multiple commits per event and ensures consistency

        Phase E1 - Ownership Enforcement:
        Validates that canonical cognition writes are only performed by approved writers.
        """
        if not batched_writes:
            return True

        # 🔥 CRITICAL: Set ownership context for experiment writes
        if self.ownership:
            from core.ownership.ownership_enforcement import CognitionWriter
            import inspect
            caller_module = inspect.currentframe().f_back.f_code.co_name
            self.ownership.set_writer(CognitionWriter.EXPERIMENT)
            for i, write_op in enumerate(batched_writes):
                state_data = write_op.get('state_data', {})
                self.ownership.validate_state_mutation(state_data, f"{caller_module}[{i}]")
        
        # Phase E1.4: Validate canonical schema before batch writes
        if self.schema_registry:
            for i, write_op in enumerate(batched_writes):
                state_data = write_op.get('state_data', {})
                is_valid, errors = self.schema_registry.validate_tier1_state(state_data)
                if not is_valid:
                    logger.error(f"❌ Canonical schema validation failed at index {i}: {errors}")
                    raise ValueError(f"Canonical state validation failed at index {i}: {errors}")
        
        # Validate input structure before touching the database
        required_keys = {'user_id', 'concept', 'state_data'}
        for i, write_op in enumerate(batched_writes):
            if not isinstance(write_op, dict):
                logger.error(f"❌ Invalid write_op at index {i}: expected dict, got {type(write_op)}")
                return False
            missing = required_keys - set(write_op.keys())
            if missing:
                logger.error(f"❌ Missing keys {missing} in write_op at index {i}")
                return False
        
        try:
            # Execute all writes in a single transaction
            result = self.postgres_store.execute_batch_write(batched_writes)
            
            if result:
                logger.debug(f"💾 Batch saved {len(batched_writes)} states atomically")

                # 🔥 CRITICAL: Clear ownership context after write
                if self.ownership:
                    self.ownership.clear_writer()

                # Update Redis cache for all saved states
                if self.redis_store:
                    now_iso = datetime.now(timezone.utc).isoformat()
                    for write_op in batched_writes:
                        try:
                            user_id = write_op['user_id']
                            concept = write_op['concept']
                            
                            # Copy to avoid mutating caller's data
                            state_data = write_op['state_data'].copy()
                            state_data.pop('updated_at', None)
                            state_data['updated_at'] = now_iso
                            
                            cache_key = f"learning_state:{user_id}:{concept}"
                            self.redis_store.set_value(
                                cache_key, 
                                self._serialize_state(state_data), 
                                expire_seconds=3600
                            )
                        except Exception as cache_error:
                            logger.warning(f"⚠️ Failed to update Redis cache for {write_op['user_id']}/{write_op['concept']}: {cache_error}")
                
                return True
            else:
                logger.error(f"❌ Failed to batch save {len(batched_writes)} states")
                return False
                
        except Exception as e:
            # 🔥 CRITICAL: Clear ownership context on error
            if self.ownership:
                self.ownership.clear_writer()
            logger.error(f"❌ Failed to batch save states: {e}")
            return False

    def delete_state(self, user_id: str, concept: str) -> bool:
        """Delete learning state from Postgres and cache"""
        cache_key = f"learning_state:{user_id}:{concept}"
        
        try:
            sql = "DELETE FROM learning_state WHERE user_id = %s AND concept = %s"
            self.postgres_store.execute_write(sql, (user_id, concept))
            
            # CACHE: Best-effort invalidation (prevents stale reads)
            if self.redis_store:
                try:
                    if hasattr(self.redis_store, 'delete_value'):
                        self.redis_store.delete_value(cache_key)
                        logger.debug(f"🗑️ Cache invalidated: {cache_key}")
                    else:
                        # Tombstone: overwrite with short TTL to block stale reads
                        self.redis_store.set_value(cache_key, "null", expire_seconds=5)
                        logger.debug(f"🗑️ Cache tombstoned (expires in 5s): {cache_key}")
                except Exception as cache_error:
                    logger.warning(f"⚠️ Failed to invalidate Redis cache: {cache_error}")
            
            logger.debug(f"🗑️ Deleted state: {user_id}/{concept}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete state: {e}")
            return False
    
    def get_state_stats(self) -> Dict[str, Any]:
        """Get statistics about learning state storage"""
        try:
            sql = """
            SELECT 
                COUNT(*) as total_states,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT concept) as unique_concepts,
                AVG((state_data->>'mastery')::float) as avg_mastery,
                MAX(updated_at) as last_updated
            FROM learning_state
            """
            
            result = self.postgres_store.execute_read(sql, fetch_one=True)
            
            if result:
                return {
                    'total_states': result['total_states'],
                    'unique_users': result['unique_users'],
                    'unique_concepts': result['unique_concepts'],
                    'avg_mastery': float(result['avg_mastery']) if result['avg_mastery'] else 0.0,
                    'last_updated': result['last_updated'].isoformat() if result['last_updated'] else None
                }
            else:
                return {
                    'total_states': 0,
                    'unique_users': 0,
                    'unique_concepts': 0,
                    'avg_mastery': 0.0,
                    'last_updated': None
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get state stats: {e}")
            return {
                'total_states': 0,
                'unique_users': 0,
                'unique_concepts': 0,
                'avg_mastery': 0.0,
                'last_updated': None
            }