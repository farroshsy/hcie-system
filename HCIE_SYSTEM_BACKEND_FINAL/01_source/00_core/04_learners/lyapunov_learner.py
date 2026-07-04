"""
Bounded Stability Learner  (legacy name: "Lyapunov Learner").

HONEST NAMING (2026-05-31): this is a *bounded stability heuristic*, NOT a Lyapunov-stable
estimator — there is no Lyapunov function or stability proof here. The actual update is the
bounded, mastery-dependent rule in ``update()``:
    correct:  gain =  α·(1 − m)·difficulty
    miss:     gain = −α·m·(1 − difficulty),      α = 0.2·(1 − m)
which keeps mastery bounded with diminishing returns. The earlier docstring formula
``m + η(y − m) + βT − λm + ε`` was aspirational and is NOT what the code computes.
Empirically this learner tracks the Bayesian learner closely (~0.92 corr) — it is the
least-independent ensemble member. The ``lyapunov*`` identifiers (DB columns, state keys, the
class alias below) are retained as legacy labels to avoid a data migration.
"""

import numpy as np
import logging
from typing import Dict, Any, Optional
from .base_learner import BaseLearner
from ..transfer.transfer_learning_engine import TransferLearningEngine
from ..state.state import LearnerState
from ..determinism.rng_stream_manager import RNGStreamManager
from ..determinism.entropy_instrumentation import get_entropy_instrumentation

logger = logging.getLogger(__name__)


class BoundedStabilityLearner(BaseLearner):
    """Bounded stability heuristic (legacy name 'Lyapunov'): a mastery-dependent bounded update with
    diminishing returns — NOT a Lyapunov-stable estimator (no Lyapunov function). See module docstring."""
    
    def __init__(self, state_adapter=None, transfer_engine=None, seed: Optional[int] = 42):
        super().__init__()
        self.state_adapter = state_adapter
        self.transfer_engine = transfer_engine
        self.min_transfer_threshold = 0.0  # No threshold - keep all signals
        self.seed = seed
        # Use deterministic RNG stream for noise
        self.rng_manager = RNGStreamManager(seed=seed)
        self.noise_stream = self.rng_manager.get_noise_stream()
    
    def update(self, user_id: str, concept_id: str, interaction: Dict[str, Any], canonical_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update mastery with stable Lyapunov dynamics"""
        # 🔥 BULLETPROOF: Use canonical_state in write mode, adapter in read mode
        if canonical_state is not None:
            # Write mode: use canonical state (no external reads)
            current_mastery = canonical_state.get("lyapunov_mastery", 0.3)
        else:
            # Read mode: use adapter (legacy behavior)
            current_mastery = self.get_state(user_id, concept_id)
        
        # Extract interaction data
        correct = interaction.get("correct", False)
        difficulty = interaction.get("difficulty", 0.5)  # Default medium difficulty
        
        # --- Lyapunov Learning Gain Calculation ---
        # Learning rate depends on current mastery (adaptive learning)
        alpha = 0.2 * (1.0 - current_mastery)  # Increased learning rate
        
        # Lyapunov function-based update
        if correct:
            # Success: increase mastery, but with diminishing returns
            learning_gain = alpha * (1.0 - current_mastery) * difficulty
        else:
            # Failure: decrease mastery, but with floor effect
            learning_gain = -alpha * current_mastery * (1.0 - difficulty)
        
        # 🔥 CLEAN ARCHITECTURE: Learner = pure learning only
        # Transfer handled by Factory (single source of truth)
        transfer_gain = 0.0  # Factory will compute transfer
        
        # Noise (prevents flatline, but smaller than signal)
        # 🔥 FIX: Use deterministic RNG stream for reproducibility
        # 🔥 ENTROPY INSTRUMENTATION: Log noise draw
        noise = self.noise_stream.normal(0, 0.0005)  # Reduced noise to prevent overwhelming learning gains
        get_entropy_instrumentation().log_draw(
            rng_stream="lyapunov_noise",
            seed=self.seed,
            value=noise,
            user_id=user_id,
            concept=concept_id,
            context={"current_mastery": current_mastery, "learning_gain": learning_gain}
        )
        
        # --- Lyapunov Update Equation ---
        new_mastery = (
            current_mastery
            + learning_gain
            + transfer_gain
            + noise
        )
        
        # Bound to [0,1]
        final_mastery = max(0.05, min(0.95, new_mastery))
        
        # 🔥 BULLETPROOF: Compute state delta instead of writing immediately
        learner_state = LearnerState.create_lyapunov(final_mastery)
        
        # Calculate metrics
        effective_gain = final_mastery - current_mastery
        
        logger.debug(f"📝 LYAPUNOV COMPUTED: {user_id}/{concept_id}")
        logger.debug(f"  mastery: {current_mastery:.3f} → {final_mastery:.3f}")
        
        # 🔥 PURE FUNCTION: Return state delta for batch writing
        return {
            "mastery_before": current_mastery,
            "mastery_after": final_mastery,
            "effective_gain": effective_gain,
            "learning_gain": learning_gain,
            "transfer_gain": transfer_gain,
            "noise": noise,
            "transfer_sources": [],  # Factory handles transfer
            # 🔥 BULLETPROOF: Include state for batch writing
            "state_delta": {
                "learner_type": "lyapunov",
                "user_id": user_id,
                "concept_id": concept_id,
                "state": learner_state
            }
        }
    
    def _get_transfer_updates(self, user_id: str, concept_id: str, current_mastery: float, learning_gain: float) -> Dict[str, float]:
        """🔥 DEPRECATED: Transfer handled by Factory (single source of truth)"""
        return {}
    
    def get_state(self, user_id: str, concept_id: str, context: str = "READ") -> float:
        """Get current mastery from StateAdapter"""
        # 🔥 CRITICAL: Reduce noise in WRITE mode - only log failures in READ mode
        if context == "READ":
            logger.error(f"🔥 STATE_ADAPTER CHECK: {self.state_adapter is not None}")
            if not self.state_adapter:
                logger.error("🔥 STATE_ADAPTER IS None - returning 0.3")
                return 0.3  # Default
        
        try:
            state = self.state_adapter.get("lyapunov", user_id, concept_id)
            if context == "READ":
                logger.error(f"🔥 LYAPUNOV INITIAL STATE: {state.to_dict()}")
            return state.mastery
        except Exception as e:
            if context == "READ":
                logger.error(f"❌ LYAPUNOV READ FAILED: {user_id}/{concept_id} - {e}")
            return 0.3
    
    def get_state_from_canonical(self, canonical_state: dict) -> float:
        """Get mastery from canonical state (WRITE mode - no reads)"""
        # 🔥 PRODUCTION SAFETY: Ensure canonical_state is a dict
        if not isinstance(canonical_state, dict):
            canonical_state = {"lyapunov_mastery": canonical_state}
        
        # 🔥 FIX F-016: Read from learner-specific field to ensure ensemble independence
        if canonical_state and "lyapunov_mastery" in canonical_state:
            return canonical_state["lyapunov_mastery"]
        # Fallback to shared mastery only if learner-specific field missing (for backward compatibility)
        if canonical_state and "mastery" in canonical_state:
            return canonical_state["mastery"]
        return 0.3  # Default
    
    def set_state(self, user_id: str, concept_id: str, mastery: float):
        """Store mastery via StateAdapter"""
        if not self.state_adapter:
            return
        
        try:
            state = LearnerState.create_lyapunov(mastery)
            
            # 🔥 BULLETPROOF: Return state delta instead of writing immediately
            state_delta = {
                "learner_type": "lyapunov",
                "user_id": user_id,
                "concept_id": concept_id,
                "state": state
            }
            logger.debug(f"📝 LYAPUNOV COMPUTED: {user_id}/{concept_id} = {mastery:.3f}")
            return state_delta
        except Exception as e:
            logger.error(f"❌ LYAPUNOV COMPUTE FAILED: {user_id}/{concept_id} - {e}")
            return None


# 🔥 Legacy alias — 14 modules + DB columns + state keys still reference "LyapunovLearner".
# The honest name is BoundedStabilityLearner (see module docstring); this keeps all imports working
# with zero behavior change and no redundant second implementation.
LyapunovLearner = BoundedStabilityLearner
