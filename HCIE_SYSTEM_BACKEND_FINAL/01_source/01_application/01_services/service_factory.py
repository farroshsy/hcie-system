"""
Service Factory - Singleton Pattern
Ensures shared state across all requests
"""

import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ServiceFactory:
    """Singleton factory for shared service instances"""
    
    _instance: Optional['ServiceFactory'] = None
    _lock = False  # Simple lock for thread safety during init
    _reconstruction_complete = False  # Guard to prevent duplicate reconstruction
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize class-level storage ONCE, never reset
            cls._instance._services = {}
            cls._instance._initialized = False
            cls._instance._reconstruction_complete = False
        return cls._instance
    
    def __init__(self):
        # Only initialize once - never clear _services
        if not self._initialized:
            self._initialized = True
            self._reconstruction_complete = False
            self._session_repos = None  # PostgreSQL session runtime repositories
            logger.info("ServiceFactory initialized")
    
    def get_task_service(self):
        """Get singleton TaskService instance with guaranteed reconstruction"""
        if 'task_service' not in self._services:
            from .task.task_service import TaskService
            task_service = TaskService()
            self._services['task_service'] = task_service
            
            # D1 - Initialize PostgreSQL session runtime repositories
            self._initialize_session_repositories(task_service)
            
            # Reconstruct state AFTER service is fully initialized
            # Only once per process lifetime
            if not self._reconstruction_complete:
                self._reconstruct_user_state_tiered(task_service)
                self._reconstruction_complete = True
            
            logger.info("TaskService singleton created with tiered state reconstruction")
        return self._services['task_service']
    
    def get_auth_service(self):
        """Get singleton AuthService instance with repositories"""
        if 'auth_service' not in self._services:
            from .auth.dependencies import create_auth_service
            
            # Get repositories (may be None - will fallback to in-memory)
            user_repo = self._get_user_repository()
            token_store = self._get_redis_token_store()
            
            # Get auth event producer
            event_producer = self._get_auth_event_producer()
            
            # Create auth service with proper repositories (or None for fallback)
            auth_service = create_auth_service(user_repo, token_store, event_producer)
            self._services['auth_service'] = auth_service
            
            repo_status = "PostgreSQL + Redis" if user_repo and token_store else "In-memory fallback"
            logger.info(f"AuthService singleton created with {repo_status}")
        return self._services['auth_service']
    
    def get_session_service(self):
        """Get singleton SessionService instance"""
        if 'session_service' not in self._services:
            from core.session.session_service import SessionService
            from core.session.models import LearningSession, SessionStatus
            
            # Create simple in-memory repository for now
            class SimpleSessionRepository:
                def __init__(self):
                    self._sessions = {}
                
                def save(self, session: LearningSession):
                    self._sessions[session.id] = session
                
                def get(self, session_id: str):
                    return self._sessions.get(session_id)
                
                def get_active(self, user_id: str):
                    for session in self._sessions.values():
                        if session.user_id == user_id and session.status == SessionStatus.ACTIVE:
                            return session
                    return None
            
            session_repository = SimpleSessionRepository()
            
            # Try to get PostgreSQL repository if available
            postgres_repo = None
            try:
                task_service = self.get_task_service()
                postgres_store = self._find_postgres_store(task_service)
                if postgres_store:
                    from app.repositories.session_runtime_repository import PostgreSQLSessionRuntimeRepository
                    postgres_repo = PostgreSQLSessionRuntimeRepository(postgres_store)
                    logger.info("SessionService using PostgreSQL repository")
            except Exception as e:
                logger.warning(f"Could not create PostgreSQL session repository: {e}")
            
            session_service = SessionService(
                session_repository=session_repository,
                postgres_repo=postgres_repo
            )
            self._services['session_service'] = session_service
            
            repo_status = "PostgreSQL" if postgres_repo else "In-memory"
            logger.info(f"SessionService singleton created with {repo_status} repository")
        return self._services['session_service']
    
    def _get_user_repository(self):
        """Get user repository from various sources"""
        try:
            logger.info("🔍 Creating UserRepository...")
            task_service = self.get_task_service()
            logger.info(f"🔍 Got task_service: {type(task_service)}")
            postgres_store = self._find_postgres_store(task_service)
            logger.info(f"🔍 Found postgres_store: {type(postgres_store)}")
            if postgres_store:
                logger.info(f"🔍 About to call UserRepository({type(postgres_store)})")
                from ..repositories.user_repository import UserRepository
                from storage.postgres_store.interaction_store import PostgresInteractionStore
                # Use the interaction store which has the execute methods
                interaction_store = PostgresInteractionStore()
                user_repo = UserRepository(interaction_store)
                logger.info("✅ UserRepository created successfully")
                return user_repo
        except Exception as e:
            logger.warning(f"⚠️ Could not create user repository: {e}")
            import traceback
            logger.warning(f"🔍 Full traceback: {traceback.format_exc()}")
        return None
    
    def _get_redis_token_store(self):
        """Get Redis token store from various sources"""
        try:
            logger.info("🔍 Creating RedisTokenStore...")
            # First try to get existing Redis client
            redis_obj = self._find_redis_client(self.get_task_service())
            logger.info(f"🔍 Found redis_obj: {type(redis_obj)}")
            if redis_obj:
                # If it's a RedisFeatureStore, get its internal redis_client
                if hasattr(redis_obj, 'redis_client') and hasattr(redis_obj.redis_client, 'setex'):
                    logger.info("🔍 Using RedisFeatureStore.redis_client")
                    from ..repositories.redis_token_store import RedisTokenStore
                    token_store = RedisTokenStore(redis_obj.redis_client)
                    logger.info("✅ RedisTokenStore created successfully")
                    return token_store
                # If it's already a proper Redis client
                elif hasattr(redis_obj, 'setex'):
                    logger.info("🔍 Using direct Redis client")
                    from ..repositories.redis_token_store import RedisTokenStore
                    token_store = RedisTokenStore(redis_obj)
                    logger.info("✅ RedisTokenStore created successfully")
                    return token_store
                else:
                    logger.warning(f"⚠️ Redis object doesn't have setex method: {type(redis_obj)}")
            
            # Create direct Redis connection for auth
            import redis
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            redis_client.ping()
            
            from ..repositories.redis_token_store import RedisTokenStore
            return RedisTokenStore(redis_client)
            
        except Exception as e:
            logger.warning(f"⚠️ Could not create Redis token store: {e}")
        return None
    
    def _get_auth_event_producer(self):
        """Get auth event producer for event-driven architecture"""
        try:
            from ..domains.auth.events import AuthEventProducer
            return AuthEventProducer()
        except Exception as e:
            logger.warning(f"⚠️ Could not create auth event producer: {e}")
        return None
    
    def _reconstruct_user_state_tiered(self, task_service):
        """Tiered state reconstruction for 300k+ users scalability"""
        import time
        start_time = time.time()
        
        try:
            logger.info("🔥 Starting tiered state reconstruction for production scale")
            
            # Get postgres store
            postgres_store = self._find_postgres_store(task_service)
            
            if not postgres_store:
                logger.warning("⚠️ No PostgreSQL store found - tiered reconstruction skipped")
                return
            
            # Get Redis client
            redis_client = self._find_redis_client(task_service)
            
            if not redis_client:
                logger.warning("⚠️ No Redis client found - tiered reconstruction will work without persistence")
            
            # Initialize tiered reconstructor
            from .tiered_reconstructor import TieredStateReconstructor, ReconstructionConfig
            
            config = ReconstructionConfig(
                hot_user_threshold=1000,      # Top 1000 active users in memory
                warm_user_threshold=50000,     # Users active in last 30 days
                chunk_size=1000,               # Batch processing size
                max_interactions_per_user=50   # Cap replay for performance
            )
            
            reconstructor = TieredStateReconstructor(
                postgres_store=postgres_store,
                redis_client=redis_client,
                task_service=task_service,
                config=config
            )
            
            # Run tiered reconstruction
            reconstructor.initialize_system()
            
            # Attach to task_service for runtime access
            task_service.tiered_reconstructor = reconstructor
            
            # Get system stats
            stats = reconstructor.get_system_stats()
            
            duration = time.time() - start_time
            
            logger.info(
                f"✅ Tiered reconstruction completed in {duration:.2f}s: "
                f"{stats['hot_users']} hot, {stats['warm_users']} warm, {stats['cold_users']} cold users"
            )
            logger.info(
                f"📊 Memory usage: {stats['memory_usage_mb']:.1f}MB, "
                f"Hot capacity: {stats['hot_capacity']}"
            )
            
            # Apply hot states to actual bandit
            self._apply_hot_states_to_bandit(task_service, reconstructor)
            
        except Exception as e:
            logger.error(f"❌ Tiered reconstruction crashed HARD: {e}", exc_info=True)
            # 🔥 DO NOT SILENTLY FALL BACK - let the system fail visibly
            raise RuntimeError(f"Tiered reconstruction failed: {e}") from e
    
    def _find_redis_client(self, task_service):
        """Find Redis client from various possible locations in TaskService"""
        # Check direct attribute
        if hasattr(task_service, 'redis') and task_service.redis:
            return task_service.redis
        
        # Check redis_store
        if hasattr(task_service, 'redis_store') and task_service.redis_store:
            return task_service.redis_store
        
        # Check inside engine
        if hasattr(task_service, 'engine') and task_service.engine:
            engine = task_service.engine
            if hasattr(engine, 'redis') and engine.redis:
                return engine.redis
        
        # Check for global getter
        try:
            from storage.redis_store.redis_store import get_redis_client
            return get_redis_client()
        except Exception:
            pass
            
        return None
    
    def _initialize_session_repositories(self, task_service):
        """D1 - Initialize PostgreSQL session runtime repositories"""
        try:
            postgres_store = self._find_postgres_store(task_service)
            if postgres_store:
                from core.session.repositories import get_postgres_session_repositories
                self._session_repos = get_postgres_session_repositories(postgres_store)
                if self._session_repos:
                    logger.info("✅ PostgreSQL session runtime repositories initialized")
                else:
                    logger.warning("⚠️ Session repositories import failed - using in-memory fallback")
            else:
                logger.warning("⚠️ No PostgreSQL store found - session repositories using in-memory fallback")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize session repositories: {e}")
    
    def get_session_repositories(self):
        """Get PostgreSQL session runtime repositories"""
        if self._session_repos is None:
            # Try to initialize if not done yet
            if 'task_service' in self._services:
                self._initialize_session_repositories(self._services['task_service'])
            else:
                # Force task service initialization
                self.get_task_service()
        return self._session_repos
    
    def _apply_hot_states_to_bandit(self, task_service, reconstructor):
        """Apply hot tier states to the actual bandit for immediate availability"""
        if not hasattr(task_service, 'bandit') or not task_service.bandit:
            logger.warning("⚠️ No bandit found to apply hot states")
            return
        
        bandit = task_service.bandit
        hot_users = list(reconstructor.hot_state.keys())
        
        logger.info(f"🔥 Applying {len(hot_users)} hot states to bandit")
        
        applied_count = 0
        for user_id in hot_users:
            try:
                state = reconstructor.hot_state[user_id]
                bandit_state = state.get('bandit', {})
                
                # Apply bandit state
                if 'arm_contexts' in bandit_state:
                    bandit.arm_contexts[user_id] = bandit_state['arm_contexts']
                
                if 'alpha_beta_params' in bandit_state:
                    bandit.alpha_beta_params[user_id] = bandit_state['alpha_beta_params']
                
                if 'step_count' in bandit_state:
                    bandit.step_count[user_id] = bandit_state['step_count']
                
                # Apply learner state if available
                learner_state = state.get('learner', {})
                if hasattr(task_service, 'engine') and task_service.engine and hasattr(task_service.engine, 'learner'):
                    learner = task_service.engine.learner
                    mastery_data = learner_state.get('mastery_data', {})
                    
                    for concept_id, mastery in mastery_data.items():
                        if hasattr(learner, 'update_mastery'):
                            learner.update_mastery(user_id, concept_id, mastery)
                        elif hasattr(learner, 'user_mastery'):
                            if user_id not in learner.user_mastery:
                                learner.user_mastery[user_id] = {}
                            learner.user_mastery[user_id][concept_id] = mastery
                
                applied_count += 1
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to apply hot state for {user_id}: {e}")
        
        logger.info(f"✅ Applied {applied_count}/{len(hot_users)} hot states to bandit")
    
    def _reconstruct_user_state(self, task_service):
        """Reconstruct user state from interaction history with batch loading"""
        import time
        start_time = time.time()
        
        try:
            # Get postgres store first
            postgres_store = self._find_postgres_store(task_service)
            
            if not postgres_store:
                logger.warning("⚠️ No PostgreSQL store found - state reconstruction skipped")
                return
            
            # Verify store is actually working
            try:
                stats = postgres_store.get_interaction_stats()
                logger.info(f"📊 PostgreSQL stats: {stats}")
            except Exception as e:
                logger.error(f"❌ PostgreSQL store not accessible: {e}")
                return
            
            # Get all users with interactions
            try:
                all_users = postgres_store.get_all_users_with_interactions(limit=100000)
                total_users = len(all_users)
                
                if total_users == 0:
                    logger.warning("⚠️ No users found for reconstruction — check data source!")
                    return
                
                logger.info(f"🔥 Starting batch state reconstruction ({total_users} users)")
                
            except Exception as e:
                logger.error(f"❌ Could not get users: {e}")
                return
            
            # 🔥 BATCH LOAD: Load all interactions in chunks to avoid connection pool exhaustion
            logger.info("🔄 Starting batch interaction loading...")
            user_interactions = self._batch_load_interactions(postgres_store, all_users)
            logger.info(f"✅ Batch loaded interactions for {len(user_interactions)} users")
            
            # Process users with detailed progress tracking
            success_count = 0
            skipped_count = 0
            error_count = 0
            
            for idx, user_id in enumerate(all_users, start=1):
                try:
                    interactions = user_interactions.get(user_id, [])
                    interaction_count = len(interactions)

                    if interaction_count == 0:
                        skipped_count += 1
                        logger.debug(f"⚠️ [{idx}/{total_users}] {user_id} has no interactions — skipped")
                        continue

                    logger.info(
                        f"🔄 [{idx}/{total_users}] Reconstructing {user_id} "
                        f"({interaction_count} interactions)"
                    )

                    # Interactions are already in OLDEST→NEWEST order from batch load
                    
                    # Sample logging for first few users
                    if idx <= 3:
                        logger.debug(f"📊 Sample interactions for {user_id}: {interactions[:2]}")

                    self._reconstruct_single_user_state(task_service, postgres_store, user_id, interactions)
                    success_count += 1

                    logger.info(
                        f"✅ [{idx}/{total_users}] {user_id} reconstructed "
                        f"(processed {interaction_count} interactions)"
                    )
                    
                    # Progress logging every 50 users
                    if idx % 50 == 0:
                        logger.info(f"🚀 Progress: {idx}/{total_users} users reconstructed")

                except Exception as e:
                    error_count += 1
                    logger.error(
                        f"❌ [{idx}/{total_users}] Failed reconstructing {user_id}: {e}",
                        exc_info=True
                    )
            
            # Final summary with timing
            duration = time.time() - start_time
            
            logger.info(
                f"🎯 Reconstruction completed: "
                f"{success_count} reconstructed, "
                f"{skipped_count} skipped (0 interactions), "
                f"{error_count} errors "
                f"(total processed: {total_users})"
            )
            
            logger.info(
                f"⏱️ Reconstruction time: {duration:.2f}s "
                f"({duration / max(total_users, 1):.3f}s per user)"
            )
                    
        except Exception as e:
            logger.error(f"❌ State reconstruction failed: {e}", exc_info=True)
    
    def _batch_load_interactions(self, postgres_store, user_ids: List[str], chunk_size: int = 1000) -> Dict[str, List[Dict]]:
        """Batch load interactions for multiple users to avoid connection pool exhaustion"""
        import time
        start_time = time.time()
        
        # Initialize result dict
        user_interactions: Dict[str, List[Dict]] = {uid: [] for uid in user_ids}
        
        # Process in chunks to avoid memory issues
        for i in range(0, len(user_ids), chunk_size):
            chunk = user_ids[i:i + chunk_size]
            logger.debug(f"🔄 Loading chunk {i//chunk_size + 1}/{(len(user_ids) + chunk_size - 1)//chunk_size}: {len(chunk)} users")
            
            try:
                # Use a single connection for the entire chunk
                if hasattr(postgres_store, '_get_connection'):
                    conn = postgres_store._get_connection()
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute("""
                                SELECT 
                                    user_id, concept_id, representation, correct, reward,
                                    response_time, difficulty, task_id, policy_mode,
                                    learning_gain, timestamp
                                FROM interactions
                                WHERE user_id = ANY(%s)
                                ORDER BY user_id, timestamp ASC
                            """, (chunk,))
                            
                            for row in cursor:
                                uid = row[0]  # user_id is first column
                                if uid in user_interactions:
                                    user_interactions[uid].append({
                                        'user_id': uid,
                                        'concept_id': row[1],
                                        'representation': row[2],
                                        'correct': row[3],
                                        'reward': float(row[4]) if row[4] is not None else 0.0,
                                        'response_time': row[5],
                                        'difficulty': row[6],
                                        'task_id': row[7],
                                        'policy_mode': row[8],
                                        'learning_gain': row[9],
                                        'timestamp': row[10]
                                    })
                    
                    finally:
                        postgres_store._put_connection(conn, success=True)
                else:
                    # Fallback to individual calls (less efficient)
                    logger.warning("⚠️ Using fallback individual user loading (less efficient)")
                    for uid in chunk:
                        interactions = postgres_store.get_user_interactions(uid, limit=1000)
                        user_interactions[uid] = interactions
                        
            except Exception as e:
                logger.error(f"❌ Failed to load chunk {i//chunk_size + 1}: {e}")
                # Continue with next chunk rather than failing completely
        
        duration = time.time() - start_time
        total_interactions = sum(len(interactions) for interactions in user_interactions.values())
        logger.info(f"✅ Batch loading completed: {total_interactions} interactions for {len(user_interactions)} users in {duration:.2f}s")
        
        return user_interactions
    
    def _persist_all_states(self, task_service):
        """Persist all reconstructed in-memory states to Redis"""
        import json
        from datetime import datetime, timedelta
        
        if not hasattr(task_service, 'bandit') or not task_service.bandit:
            logger.warning("⚠️ No bandit found for Redis persistence")
            return
        
        bandit = task_service.bandit
        persisted_count = 0
        
        for user_id in bandit.step_count:
            try:
                # Build state dict
                state = {
                    'arm_contexts': bandit.arm_contexts.get(user_id, {}),
                    'alpha_beta_params': bandit.alpha_beta_params.get(user_id, {}),
                    'step_count': bandit.step_count.get(user_id, 0),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Persist to Redis if available
                redis_client = None
                if hasattr(task_service, 'redis_store') and task_service.redis_store:
                    redis_client = task_service.redis_store
                elif hasattr(task_service, 'redis') and task_service.redis:
                    redis_client = task_service.redis
                elif hasattr(bandit, 'redis_client') and bandit.redis_client:
                    redis_client = bandit.redis_client
                
                if redis_client:
                    key = f"bandit:state:{user_id}"
                    redis_client.set(key, json.dumps(state))
                    redis_client.expire(key, timedelta(hours=24))
                    persisted_count += 1
                
                # Also persist regret
                if hasattr(bandit, 'redis_regret') and user_id not in bandit.redis_regret:
                    bandit.redis_regret[user_id] = {
                        'learning_regret': 0.0,
                        'decision_regret': 0.0,
                        'steps': bandit.step_count.get(user_id, 0)
                    }
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to persist state for {user_id}: {e}")
        
        logger.info(f"💾 Persisted {persisted_count} user states to Redis")
    
    def _find_postgres_store(self, task_service):
        """Find PostgreSQL store from various possible locations in TaskService"""
        # Check direct attribute
        if hasattr(task_service, 'postgres_store') and task_service.postgres_store:
            return task_service.postgres_store
        
        # Check if it's a property or method
        if hasattr(task_service, 'get_postgres_store'):
            try:
                return task_service.get_postgres_store()
            except:
                pass
        
        # Check inside engine
        if hasattr(task_service, 'engine') and task_service.engine:
            engine = task_service.engine
            if hasattr(engine, 'postgres_store') and engine.postgres_store:
                return engine.postgres_store
            if hasattr(engine, 'interaction_store') and engine.interaction_store:
                return engine.interaction_store
        
        # Check inside data layer
        if hasattr(task_service, 'data_layer') and task_service.data_layer:
            dl = task_service.data_layer
            if hasattr(dl, 'postgres_store') and dl.postgres_store:
                return dl.postgres_store
        
        # Check for global getter
        try:
            from .postgres_interaction_store import get_postgres_interaction_store
            return get_postgres_interaction_store()
        except Exception:
            pass
            
        return None
    
    def _reconstruct_single_user_state(self, task_service, postgres_store, user_id: str, interactions: List[Dict] = None):
        """Reconstruct state for a single user from their interaction history"""
        try:
            # Get user's interaction history if not provided
            if interactions is None:
                interactions = postgres_store.get_user_interactions(user_id, limit=1000)
                
                if not interactions:
                    logger.debug(f"No interactions found for user {user_id}")
                    return
                
                # 🔥 CRITICAL FIX: Reverse to OLDEST→NEWEST for correct temporal reconstruction
                interactions = list(reversed(interactions))
            
            logger.debug(f"🔥 Reconstructing state for user {user_id} from {len(interactions)} interactions (OLDEST→NEWEST)")
            
            # Reconstruct bandit state
            if hasattr(task_service, 'bandit') and task_service.bandit:
                self._reconstruct_bandit_state(task_service.bandit, user_id, interactions)
            else:
                logger.warning(f"⚠️ No bandit found in TaskService for user {user_id}")
            
            # Reconstruct learner state  
            if hasattr(task_service, 'engine') and task_service.engine and hasattr(task_service.engine, 'learner'):
                self._reconstruct_learner_state(task_service.engine.learner, user_id, interactions)
            else:
                logger.debug(f"📊 No learner engine found for user {user_id}")
                
        except Exception as e:
            logger.warning(f"❌ Could not reconstruct state for user {user_id}: {e}", exc_info=True)
    
    def _reconstruct_bandit_state(self, bandit, user_id: str, interactions: List[Dict]):
        """Reconstruct bandit state from interaction history"""
        # Ensure user exists in bandit
        if not hasattr(bandit, 'arm_contexts'):
            logger.warning("Bandit missing arm_contexts attribute")
            return
        
        # Initialize user containers
        if user_id not in bandit.arm_contexts:
            bandit.arm_contexts[user_id] = {}
        if hasattr(bandit, 'alpha_beta_params') and user_id not in bandit.alpha_beta_params:
            bandit.alpha_beta_params[user_id] = {}
        if hasattr(bandit, 'step_count'):
            if user_id not in bandit.step_count:
                bandit.step_count[user_id] = 0
        
        # Process interactions
        for interaction in interactions:
            task_id = interaction.get('task_id', 'unknown')
            concept_id = interaction.get('concept_id', 'unknown')
            reward = float(interaction.get('reward', 0.0))
            
            # Update arm contexts
            if task_id not in bandit.arm_contexts[user_id]:
                bandit.arm_contexts[user_id][task_id] = []
            
            bandit.arm_contexts[user_id][task_id].append({
                'concept_id': concept_id,
                'reward': reward,
                'timestamp': interaction.get('timestamp')
            })
            
            # Update alpha/beta for Thompson sampling
            if hasattr(bandit, 'alpha_beta_params'):
                if task_id not in bandit.alpha_beta_params[user_id]:
                    bandit.alpha_beta_params[user_id][task_id] = {'alpha': 1.0, 'beta': 1.0}
                
                alpha = bandit.alpha_beta_params[user_id][task_id]['alpha']
                beta = bandit.alpha_beta_params[user_id][task_id]['beta']
                bandit.alpha_beta_params[user_id][task_id]['alpha'] = alpha + reward
                bandit.alpha_beta_params[user_id][task_id]['beta'] = beta + (1.0 - reward)
        
        # Update step count
        if hasattr(bandit, 'step_count'):
            bandit.step_count[user_id] = len(interactions)
        
        arm_count = len(bandit.arm_contexts.get(user_id, {}))
        step_count = bandit.step_count.get(user_id, 0)
        logger.info(f"✅ Bandit state for {user_id}: {arm_count} arms, {step_count} steps")
    
    def _reconstruct_learner_state(self, learner, user_id: str, interactions: List[Dict]):
        """Reconstruct learner state from interaction history"""
        # Build mastery from most recent interaction per concept
        concept_mastery = {}
        for interaction in interactions:
            concept_id = interaction.get('concept_id', 'unknown')
            # Use mastery_after if available, otherwise infer from correctness
            mastery = interaction.get('mastery_after')
            if mastery is None:
                correct = interaction.get('correct', False)
                mastery = 0.7 if correct else 0.3
            
            # Keep the most recent value (interactions are DESC ordered)
            if concept_id not in concept_mastery:
                concept_mastery[concept_id] = float(mastery)
        
        # Update learner
        if hasattr(learner, 'update_mastery'):
            for concept_id, mastery in concept_mastery.items():
                learner.update_mastery(user_id, concept_id, mastery)
        elif hasattr(learner, 'user_mastery'):
            if user_id not in learner.user_mastery:
                learner.user_mastery[user_id] = {}
            learner.user_mastery[user_id].update(concept_mastery)
        elif hasattr(learner, 'mastery_data'):
            if user_id not in learner.mastery_data:
                learner.mastery_data[user_id] = {}
            learner.mastery_data[user_id].update(concept_mastery)
        
        logger.info(f"✅ Learner state for {user_id}: {len(concept_mastery)} concepts")
    
    def get_signal_extractor(self):
        """Get singleton SignalExtractor instance"""
        if 'signal_extractor' not in self._services:
            from core.signal.signal_extractor import SignalExtractor
            self._services['signal_extractor'] = SignalExtractor()
            logger.info("SignalExtractor singleton created")
        return self._services['signal_extractor']
    
    def get_debug_service(self):
        """Get singleton DebugService instance"""
        if 'debug_service' not in self._services:
            from .debug.debug_service import DebugService
            self._services['debug_service'] = DebugService(self)
            logger.info("DebugService singleton created")
        return self._services['debug_service']
    
    def get_analytics_service(self):
        """Get singleton AnalyticsService instance"""
        if 'analytics_service' not in self._services:
            from .analytics.analytics_service import AnalyticsService
            self._services['analytics_service'] = AnalyticsService(self)
            logger.info("AnalyticsService singleton created")
        return self._services['analytics_service']
    
    def reset_services(self):
        """Clear all services - USE WITH CAUTION, mainly for testing"""
        self._services.clear()
        logger.warning("All services cleared from factory")


# Global singleton instance
service_factory = ServiceFactory()

def get_service_factory() -> ServiceFactory:
    """Get the global service factory instance"""
    return service_factory