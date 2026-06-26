"""
State Adapter Layer - Single Source of Truth for All Learner State Operations
Eliminates direct Redis access and normalizes state formats
"""

import logging
from .state import LearnerState
from ..learners.prior_config import get_prior

logger = logging.getLogger(__name__)

class StateAdapter:
    """
    Centralized state management adapter for all learners
    
    This is the ONLY place that talks to Redis directly.
    All learners go through this layer for state operations.
    """
    
    def __init__(self, redis_store, learning_state_repo=None):
        # 🔥 Fail fast against silent corruption
        if redis_store is None:
            raise ValueError("StateAdapter initialized with redis=None — this is a bug in LearnerFactory initialization")
        
        self.redis = redis_store
        self.learning_state_repo = learning_state_repo
        self._canonical_store = learning_state_repo if learning_state_repo else redis_store  # Use repository if available
        logger.info(f"State Adapter initialized (repository={learning_state_repo is not None})")
    
    def _key(self, learner_type: str, user_id: str, concept_id: str) -> str:
        """Generate namespaced key for state storage"""
        return f"state:{learner_type}:{user_id}:{concept_id}"
    
    def get(self, learner_type: str, user_id: str, concept_id, allow_create: bool = False) -> LearnerState:
        """
        Get normalized state for any learner type
        
        🔥 FIXED: Now reads from canonical state store instead of Redis cold starts
        This eliminates the second major architectural leak
        
        Args:
            allow_create: If False (READ mode), fail hard when canonical state missing
                         If True (WRITE mode), create canonical state when missing
        """
        # Try learning state repository first (preferred), then fallback to Redis/memory
        if self.learning_state_repo:
            # Use Postgres learning state repository
            try:
                canonical_data = self.learning_state_repo.get_state(user_id, concept_id)
                if canonical_data and "mastery" in canonical_data:
                    mastery = canonical_data["mastery"]
                    learner_state = self._convert_canonical_to_learner(learner_type, canonical_data)
                    logger.info(f"🔥 CONVERTED CANONICAL TO {learner_type}: mastery={mastery:.3f}")
                    return learner_state
                else:
                    logger.warning(f"❌ No mastery in canonical state: {canonical_data}")
                    raise RuntimeError(f"Canonical state missing for {user_id}_{concept_id} - read-only invariant violated")
            except Exception as e:
                logger.warning(f"Learning state repository failed: {e}")
                # Continue to fallback method
        
        # Fallback to Redis/memory store
        if self._canonical_store:
            state_key = f"{user_id}_{concept_id}"
            try:
                if hasattr(self._canonical_store, 'get_value'):
                    # Redis store case
                    stored_data = self._canonical_store.get_value(state_key)
                    if stored_data:
                        import json
                        canonical_state = json.loads(stored_data)
                        # 🔥 CRITICAL: Use UnifiedBrain's canonical format
                        if "mastery" in canonical_state:
                            mastery = canonical_state["mastery"]
                            learner_state = self._convert_canonical_to_learner(learner_type, canonical_state)
                            logger.info(f"🔥 CONVERTED CANONICAL TO {learner_type}: mastery={mastery:.3f}")
                            return learner_state
                        else:
                            logger.warning(f"❌ No mastery in canonical state: {list(canonical_state.keys())}")
                            raise RuntimeError("No mastery found in canonical state")
                elif isinstance(self._canonical_store, dict):
                    # Local dictionary case
                    if state_key in self._canonical_store:
                        canonical_state = self._canonical_store[state_key]
                        # 🔥 CRITICAL: Use UnifiedBrain's canonical format
                        if "mastery" in canonical_state:
                            mastery = canonical_state["mastery"]
                            learner_state = self._convert_canonical_to_learner(learner_type, canonical_state)
                            logger.info(f"🔥 CONVERTED CANONICAL TO {learner_type}: mastery={mastery:.3f}")
                            return learner_state
                        else:
                            logger.warning(f"❌ No mastery in canonical state: {list(canonical_state.keys())}")
                            raise RuntimeError("No mastery found in canonical state")
            except Exception as e:
                logger.warning(f"Redis retrieval failed: {e}")
        
        # 🔥 CRITICAL: Enforce read-only invariant
        if not allow_create:
            # READ mode - fail hard if no canonical state
            raise RuntimeError(f"Canonical state missing for {user_id}_{concept_id} - read-only invariant violated")
        
        # WRITE mode - create canonical state (only allowed here)
        logger.info(f"🔥 CREATING CANONICAL STATE for {learner_type}/{user_id}/{concept_id}")
        canonical_state = self._create_cold_start_state(learner_type, user_id, concept_id)
        
        # Store the canonical state for future reads
        self._store_canonical_state(user_id, concept_id, canonical_state, learner_type)
        
        return canonical_state
    
    def _convert_canonical_to_learner(self, learner_type: str, canonical_state: dict) -> LearnerState:
        """Convert canonical state to learner-specific state, preserving actual learner parameters"""
        mastery = canonical_state.get("mastery", 0.3)
        
        if learner_type == "lyapunov":
            return LearnerState.create_lyapunov(mastery)
        elif learner_type == "bayesian":
            # 🔥 FIX F-027: Preserve actual Bayesian alpha/beta if available, don't reconstruct from mastery
            alpha = canonical_state.get("bayesian_alpha")
            beta = canonical_state.get("bayesian_beta")
            
            if alpha is not None and beta is not None:
                # Use actual posterior parameters
                return LearnerState.create_bayesian(alpha, beta)
            else:
                # F-027: use conjugate cold-start prior, not mastery×10 reconstruction
                logger.warning(
                    "⚠️ Bayesian alpha/beta missing from canonical state; using cold-start prior (3, 7)"
                )
                return LearnerState.create_bayesian(3.0, 7.0)
        elif learner_type == "kalman":
            # 🔥 FIX F-028: Preserve actual Kalman mastery and covariance if available
            kalman_mastery = canonical_state.get("kalman_mastery")
            kalman_covariance = canonical_state.get("kalman_covariance")
            
            if kalman_mastery is not None and kalman_covariance is not None:
                # Use actual Kalman state
                return LearnerState.create_kalman(kalman_mastery, kalman_covariance)
            else:
                # Fallback
                logger.warning("⚠️ Kalman mastery/covariance missing from canonical state, using defaults")
                covariance = 0.1
                return LearnerState.create_kalman(mastery, covariance)
        else:
            raise ValueError(f"Unknown learner type: {learner_type}")
    
    def _deserialize(self, learner_type: str, raw) -> LearnerState:
        """Strict deserialization with no silent fallbacks"""
        if learner_type == "lyapunov":
            if not isinstance(raw, (float, int)):
                raise ValueError(f"Invalid Lyapunov state: {raw}")
            return LearnerState.create_lyapunov(float(raw))
        
        elif learner_type == "bayesian":
            if not (isinstance(raw, (list, tuple)) and len(raw) == 2):
                raise ValueError(f"Invalid Bayesian state: {raw}")
            return LearnerState.create_bayesian(raw[0], raw[1])
        
        elif learner_type == "kalman":
            if not (isinstance(raw, (list, tuple)) and len(raw) == 2):
                raise ValueError(f"Invalid Kalman state: {raw}")
            return LearnerState.create_kalman(raw[0], raw[1])
        
        else:
            raise ValueError(f"Unknown learner type: {learner_type}")
    
    def _get_lyapunov_state(self, learner_type: str, user_id: str, concept_id: str, raw) -> LearnerState:
        """Get Lyapunov state from raw Redis data"""
        # 🚨 CROSS-LEARNER STATE LEAK DETECTION
        if isinstance(raw, tuple):
            logger.error("🚨 CROSS-LEARNER STATE LEAK DETECTED - forcing cold start")
            return self._create_cold_start_state("lyapunov", user_id, concept_id)
        
        return self._deserialize("lyapunov", raw)
    
    def set(self, learner_type: str, user_id: str, concept_id: str, state: LearnerState):
        """
        Set normalized state for any learner type
        
        Args:
            learner_type: 'lyapunov', 'bayesian', or 'kalman'
            user_id: User identifier
            concept_id: Concept identifier
            state: LearnerState to persist
        """
        try:
            key = self._key(learner_type, user_id, concept_id)
            # Serialize state to JSON for Redis storage
            import json
            state_json = json.dumps(state.to_dict())
            self.redis.set_value(key, state_json)
        except Exception as e:
            logger.error(f"State adapter set failed for {learner_type}/{user_id}/{concept_id}: {e}")
            
    def _store_canonical_state(self, user_id: str, concept_id: str, state: LearnerState, learner_type: str) -> None:
        """Store canonical state for all learners"""
        try:
            state_key = f"{user_id}_{concept_id}"
            
            # Get existing canonical data or create new
            if hasattr(self._canonical_store, 'get_value'):
                # Redis case
                try:
                    existing_data = self._canonical_store.get_value(state_key)
                    if existing_data:
                        import json
                        canonical_data = json.loads(existing_data)
                    else:
                        canonical_data = {}
                except Exception as e:
                    logger.warning(f"Redis retrieval failed: {e}")
                    canonical_data = {}
                
                # 🔥 CRITICAL: Use UnifiedBrain's canonical format, not learner-specific
                import json
                from datetime import datetime
                
                # Create UnifiedBrain format canonical state
                unified_canonical = {
                    "mastery": state.mastery,
                    "confidence": state.confidence if hasattr(state, 'confidence') else 0.5,
                    "uncertainty": state.uncertainty if hasattr(state, 'uncertainty') else 0.5,
                    "timestamp": datetime.now().isoformat(),
                    "transfer_amounts": state.transfer_amounts if hasattr(state, 'transfer_amounts') else {},
                    "processing_mode": state.processing_mode if hasattr(state, 'processing_mode') else "unknown"
                }
                
                self._canonical_store.set_value(state_key, json.dumps(unified_canonical))
                
            elif isinstance(self._canonical_store, dict):
                # Local dictionary case
                import json
                from datetime import datetime
                
                # Create UnifiedBrain format canonical state
                unified_canonical = {
                    "mastery": state.mastery,
                    "confidence": state.confidence if hasattr(state, 'confidence') else 0.5,
                    "uncertainty": state.uncertainty if hasattr(state, 'uncertainty') else 0.5,
                    "timestamp": datetime.now().isoformat(),
                    "transfer_amounts": state.transfer_amounts if hasattr(state, 'transfer_amounts') else {},
                    "processing_mode": state.processing_mode if hasattr(state, 'processing_mode') else "unknown"
                }
                
                self._canonical_store[state_key] = unified_canonical
            
            logger.info(f"🔥 STORED CANONICAL STATE: {user_id}_{concept_id}")
            
        except Exception as e:
            logger.error(f"Failed to store canonical state: {e}")
    
    def _create_cold_start_state(self, learner_type: str, user_id: str = None, concept_id: str = None) -> LearnerState:
        """Create cold-start state using principled priors with personalization"""
        prior = get_prior(learner_type, user_id=user_id, concept=concept_id)
        logger.info(f"🔥 COLD START PRIOR for {learner_type}: {prior}")
        
        if learner_type == "lyapunov":
            return LearnerState.create_lyapunov(prior["mastery"])
        elif learner_type == "bayesian":
            return LearnerState.create_bayesian(prior["alpha"], prior["beta"])
        elif learner_type == "kalman":
            # 🔥 FIX KALMAN: Ensure proper cold-start from 0.3, not 1.0
            mastery = prior["mastery"]
            covariance = prior["covariance"]
            logger.info(f"🔥 KALMAN COLD START: mastery={mastery}, covariance={covariance}")
            return LearnerState.create_kalman(mastery, covariance)
        else:
            raise ValueError(f"Unknown learner type: {learner_type}")
    
    def _get_default_state(self, learner_type: str, user_id: str = None, concept_id: str = None) -> LearnerState:
        """Get safe default state for learner type (fallback)"""
        logger.warning(f"Using fallback default for {learner_type}")
        return self._create_cold_start_state(learner_type, user_id, concept_id)
