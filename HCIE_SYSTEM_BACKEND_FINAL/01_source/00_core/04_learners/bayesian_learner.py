"""
Bayesian Learner - Preserved Baseline Model
Implements: Alpha/Beta Bayesian updating
"""

import logging
from typing import Dict, Any, Tuple
from .base_learner import BaseLearner
from ..state.state import LearnerState
from ..mastery.mastery_model import MasteryModel

logger = logging.getLogger(__name__)


class BayesianLearner(BaseLearner):
    """Bayesian conjugate update learner with proper Beta distribution handling"""
    
    def __init__(self, state_adapter=None, mastery_model=None):
        super().__init__()
        self.state_adapter = state_adapter
        self.mastery_model = mastery_model or MasteryModel()
    
    def update(self, user_id: str, concept_id: str, interaction: Dict[str, Any], canonical_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update alpha/beta using Bayesian conjugate update"""
        if canonical_state is not None:
            # Write mode: use canonical state (no external reads)
            alpha = canonical_state.get("bayesian_alpha", 3.0)
            beta = canonical_state.get("bayesian_beta", 7.0)
            logger.info(f" BAYESIAN WRITE MODE: {user_id}/{concept_id} α={alpha:.4f}, β={beta:.4f} (sum={alpha+beta:.4f})")
        else:
            # Read mode: use state adapter (no external reads)
            state = self.state_adapter.get("bayesian", user_id, concept_id, allow_create=False)
            alpha = state.alpha
            beta = state.beta
            logger.info(f" BAYESIAN READ MODE: {user_id}/{concept_id} α={alpha:.4f}, β={beta:.4f} (sum={alpha+beta:.4f})")
        
        # Extract interaction data
        is_correct = interaction.get("correct", False)
        difficulty = interaction.get("difficulty", 0.5)
        response_time = interaction.get("response_time", 10.0)
        
        # Bayesian update using mastery model
        new_alpha, new_beta = self.mastery_model.calculate_step(
            alpha, beta, is_correct, difficulty, response_time
        )
        
        # 🔥 BULLETPROOF: Compute state delta instead of writing immediately
        learner_state = LearnerState.create_bayesian(new_alpha, new_beta)
        
        # Calculate mastery for reporting
        mastery = new_alpha / (new_alpha + new_beta) if (new_alpha + new_beta) > 0 else 0.3
        
        # Calculate change
        old_mastery = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.3
        mastery_change = mastery - old_mastery
        
        logger.debug(f"� BAYESIAN COMPUTED: {user_id}/{concept_id}")
        logger.debug(f"  alpha/beta: ({alpha:.2f}, {beta:.2f}) → ({new_alpha:.2f}, {new_beta:.2f})")
        logger.debug(f"  mastery: {old_mastery:.3f} → {mastery:.3f}")
        
        # 🔥 PURE FUNCTION: Return state delta for batch writing
        return {
            "mastery_before": old_mastery,
            "mastery_after": mastery,
            "mastery_change": mastery_change,
            "alpha": new_alpha,
            "beta": new_beta,
            "learner": "bayesian",
            # 🔥 BULLETPROOF: Include state for batch writing
            "state_delta": {
                "learner_type": "bayesian",
                "user_id": user_id,
                "concept_id": concept_id,
                "state": learner_state
            }
        }
    
    def get_state(self, user_id: str, concept_id: str) -> Tuple[float, float]:
        """Get current alpha/beta from StateAdapter"""
        if not self.state_adapter:
            return (3.0, 7.0)  # Novice prior (0.3 mastery)
        
        try:
            state = self.state_adapter.get("bayesian", user_id, concept_id)
            return state.alpha, state.beta
        except Exception as e:
            logger.error(f"❌ BAYESIAN READ FAILED: {user_id}/{concept_id} - {e}")
            return (3.0, 7.0)  # Novice prior (0.3 mastery)
    
    def get_state_from_canonical(self, canonical_state: dict) -> Tuple[float, float]:
        """Get alpha/beta from canonical state (WRITE mode - no reads)"""
        # 🔥 PRODUCTION SAFETY: Ensure canonical_state is a dict
        if not isinstance(canonical_state, dict):
            canonical_state = {"mastery": canonical_state}
        
        # 🔥 FIX F-027: Preserve actual Bayesian alpha/beta if available, don't reconstruct from mastery
        if canonical_state and "bayesian_alpha" in canonical_state and "bayesian_beta" in canonical_state:
            alpha = canonical_state["bayesian_alpha"]
            beta = canonical_state["bayesian_beta"]
            return (alpha, beta)
        
        # F-027: cold-start prior only — never reconstruct α/β from mastery (sum would stay fixed)
        return (3.0, 7.0)
    
    def set_state(self, user_id: str, concept_id: str, state: Tuple[float, float]):
        """Store alpha/beta via StateAdapter"""
        if not self.state_adapter:
            return
        
        try:
            alpha, beta = state
            learner_state = LearnerState.create_bayesian(alpha, beta)
            self.state_adapter.set("bayesian", user_id, concept_id, learner_state)
            logger.info(f"✅ BAYESIAN WRITE: {user_id}/{concept_id} = ({alpha:.2f}, {beta:.2f})")
        except Exception as e:
            logger.error(f"❌ BAYESIAN WRITE FAILED: {user_id}/{concept_id} - {e}")
