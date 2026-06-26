"""
Learner Factory - Clean Model Switching
Provides pluggable access to different learning models
"""

import logging
from typing import Dict, Any
from .base_learner import BaseLearner
from .lyapunov_learner import LyapunovLearner
from .bayesian_learner import BayesianLearner
from .kalman_learner import KalmanLearner
from ..state.state_adapter import StateAdapter

logger = logging.getLogger(__name__)


class LearnerFactory:
    """Factory for creating and managing different learner instances"""
    
    def __init__(self, redis_store=None, transfer_engine=None, mastery_model=None, learning_state_repo=None, seed: int = 42):
        self.redis_store = redis_store
        self.transfer_engine = transfer_engine
        self.mastery_model = mastery_model
        self.learning_state_repo = learning_state_repo
        self.seed = seed
        
        # Create state adapter - use learning state repository if available, fallback to Redis
        if learning_state_repo:
            # Create state adapter that uses the same repository as unified brain
            self.state_adapter = StateAdapter(redis_store, learning_state_repo=learning_state_repo)
        else:
            # Fallback to Redis-only
            self.state_adapter = StateAdapter(redis_store)
        
        # Initialize all learners with state adapter and seed
        self._learners = {
            "lyapunov": LyapunovLearner(self.state_adapter, transfer_engine, seed=self.seed),
            "bayesian": BayesianLearner(self.state_adapter, mastery_model),
            "kalman": KalmanLearner(self.state_adapter, transfer_engine),
        }
        
        logger.info(f"🔥 LEARNER FACTORY: Initialized {len(self._learners)} learners")
        for name, learner in self._learners.items():
            logger.info(f"  - {name}: {learner.__class__.__name__}")
    
    def get(self, mode: str) -> BaseLearner:
        """Get learner instance by mode"""
        learner = self._learners.get(mode, self._learners["lyapunov"])
        logger.info(f"🔥 LEARNER SELECTED: {mode} → {learner.__class__.__name__}")
        return learner
    
    def list_available(self) -> Dict[str, str]:
        """List all available learners"""
        return {name: learner.__class__.__name__ for name, learner in self._learners.items()}
    
    def update(self, mode: str, user_id: str, concept_id: str, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Convenience method to update with specific learner"""
        learner = self.get(mode)
        
        # Handle prior override for controlled experiments
        prior_mastery = interaction.get("prior_mastery")
        if prior_mastery is not None:
            logger.info(f"🔥 PRIOR OVERRIDE: Setting {mode} mastery to {prior_mastery} for {user_id}/{concept_id}")
            # Create initial state with prior and store it
            from ..state.state import LearnerState
            if mode == "lyapunov":
                state = LearnerState.create_lyapunov(prior_mastery)
            elif mode == "bayesian":
                # Convert mastery to alpha/beta
                alpha = prior_mastery * 10
                beta = 10 - alpha
                state = LearnerState.create_bayesian(alpha, beta)
            elif mode == "kalman":
                state = LearnerState.create_kalman(prior_mastery, 0.1)
            else:
                raise ValueError(f"Unknown learner mode: {mode}")
            
            self.state_adapter.set(mode, user_id, concept_id, state)
        
        # Get learner result first
        learner_result = learner.update(user_id, concept_id, interaction)
        
        # Apply transfer learning AFTER learning signal (push-based)
        transfer_gain = 0.0
        transfer_sources = []
        transfer_updates = {}
        transfer_events = []
        
        if hasattr(learner, 'transfer_engine') and learner.transfer_engine:
            try:
                # Compute transfer using REAL learning signal
                transfer_updates, transfer_events = learner.transfer_engine.process_mastery_update(
                    user_id=user_id,
                    concept=concept_id,
                    mastery_before=learner_result["mastery_before"],
                    mastery_after=learner_result["mastery_after"],
                    confidence=0.8,
                    learning_gain=learner_result.get("learning_gain", learner_result["mastery_change"])
                )
                
                # Extract transfer correctly - get actual source concepts from events
                transfer_sources = []
                for event in transfer_events:
                    if event.source_concept not in transfer_sources:
                        transfer_sources.append(event.source_concept)
                
                logger.info(f"🔥 TRANSFER COMPUTED: gains={transfer_updates}, sources={transfer_sources}")
                logger.info(f"🔥 TRANSFER TYPE: {type(transfer_updates)}, KEYS: {list(transfer_updates.keys()) if transfer_updates else []}")
                
                # Apply transfer to TARGET concepts (not current concept)
                for transfer_key, transfer_amount in transfer_updates.items():
                    # Parse the normalized key "src→tgt" back to components
                    if "→" in transfer_key:
                        source_concept, target_concept = transfer_key.split("→", 1)
                    else:
                        continue  # Skip malformed keys
                    if transfer_amount > 0:
                        # Get current state of target concept
                        target_state = learner.get_state(user_id, target_concept)
                        
                        if isinstance(target_state, tuple):
                            mastery, P = target_state
                            mastery += transfer_amount
                            learner.set_state(user_id, target_concept, (mastery, P))
                            logger.info(f"🔥 TRANSFER APPLIED TO TARGET: {target_concept} mastery += {transfer_amount:.4f}")
                        else:
                            mastery = target_state + transfer_amount
                            learner.set_state(user_id, target_concept, mastery)
                            logger.info(f"🔥 TRANSFER APPLIED TO TARGET: {target_concept} mastery += {transfer_amount:.4f}")
                        
                        transfer_gain += transfer_amount
                
            except Exception as e:
                logger.error(f"❌ TRANSFER FAILED: {e}")
        
                
        # Apply transfer to state BEFORE final result calculation
        if transfer_gain > 0:
            # Read the updated state after transfer
            current_state = learner.get_state(user_id, concept_id)
            if isinstance(current_state, tuple):
                final_mastery = current_state[0]
            else:
                final_mastery = current_state
            
            # Update learner result with final mastery
            learner_result["mastery_after"] = final_mastery
            learner_result["mastery_change"] = final_mastery - learner_result.get("mastery_before", 0.3)
        
        # Calculate incoming transfer for this concept (multi-source support)
        incoming_transfer = sum(
            amount for transfer_key, amount in transfer_updates.items()
            if "→" in transfer_key and transfer_key.split("→", 1)[1] == concept_id
        )
        prior_mastery = 0.3  # This should match your cold start prior
        
        # For debugging: also calculate the old way
        pre_update_mastery = learner_result.get("mastery_before", prior_mastery)
        calculated_transfer = max(0, pre_update_mastery - prior_mastery)
        
        # Calculate true direct mastery (excluding transfer)
        # Direct mastery is the learning signal from THIS interaction
        true_direct_mastery = learner_result["mastery_after"] - transfer_gain
        
        # Add transfer metadata to result
        learner_result.update({
            'transfer_sources': transfer_sources,
            'transferred_mastery': incoming_transfer,  # Incoming transfer for this concept
            'transferred_mastery_change': incoming_transfer,  # 🔥 FIX: Same source as transferred_mastery
            'transfer_effect': transfer_gain,           # Outgoing transfer from this concept
            'prior_mastery': prior_mastery,             # Cold start prior (0.3)
            'pre_update_mastery': pre_update_mastery, # mastery before this update (prior + transfer)
            'post_update_mastery': learner_result.get("mastery_after", pre_update_mastery),
            'direct_mastery': true_direct_mastery,     # True direct mastery learned (this interaction)
            'transfers_applied': transfer_updates,  # 🔥 FINAL: Engine normalizes, no downstream hacks
            'transfer_events': transfer_events          # Transfer events for persistence
        })
        
        # 🔥 SRE-GRADE INVARIANT TEST: Ensure data consistency
        mastery_change = learner_result.get("mastery_change", 0.0)
        direct_mastery = learner_result.get("direct_mastery", 0.0)
        transferred_mastery = learner_result.get("transferred_mastery", 0.0)
        
        # Math should be consistent: total_change ≈ direct + transfer
        expected_change = direct_mastery + transferred_mastery
        if abs(mastery_change - expected_change) > 1e-6:
            logger.error(f"❌ INVARIANT VIOLATION: mastery_change={mastery_change} ≠ direct+transfer={expected_change}")
            logger.error(f"   direct={direct_mastery}, transfer={transferred_mastery}")
        else:
            logger.info(f"✅ INVARIANT PASS: mastery_change={mastery_change} = direct+transfer={expected_change}")
        
        return learner_result
    
    def get_state(self, mode: str, user_id: str, concept_id: str):
        """Convenience method to get state from specific learner"""
        learner = self.get(mode)
        return learner.get_state(user_id, concept_id)
