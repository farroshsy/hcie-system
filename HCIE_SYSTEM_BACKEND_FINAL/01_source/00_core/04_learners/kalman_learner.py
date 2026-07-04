"""
Kalman Learner - Baseline Model
Implements: scalar Kalman filter with FIXED process/observation noise
(Q=0.01, R=0.1 are constants below; the covariance is updated each step but the
noise model is NOT adaptive — do not describe this as "adaptive covariance").
"""

import numpy as np
import logging
from typing import Dict, Any, Tuple
from .base_learner import BaseLearner
from ..state.state import LearnerState

logger = logging.getLogger(__name__)


class KalmanLearner(BaseLearner):
    """Kalman filter-based learner with uncertainty tracking"""
    
    def __init__(self, state_adapter=None, transfer_engine=None):
        super().__init__()
        self.state_adapter = state_adapter
        self.transfer_engine = transfer_engine
    
    def update(self, user_id: str, concept_id: str, interaction: Dict[str, Any], canonical_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update learner state with new interaction"""
        # 🔥 BULLETPROOF: Use canonical_state in write mode, adapter in read mode
        if canonical_state is not None:
            # Write mode: use canonical state (no external reads)
            mastery = canonical_state.get("kalman_mastery", 0.3)
            P = canonical_state.get("kalman_covariance", 0.1)
        else:
            # Read mode: use adapter (legacy behavior)
            mastery, P = self.get_state(user_id, concept_id)
        
        # Extract interaction data
        is_correct = interaction.get("correct", False)
        
        # --- Kalman Parameters ---
        y = 1.0 if is_correct else 0.0  # Observation
        Q = 0.01  # Process noise covariance
        R = 0.1   # Observation noise covariance
        
        # --- Kalman Update ---
        # Prediction step (already have current state)
        m_pred = mastery
        P_pred = P + Q
        
        # Update step
        K = P_pred / (P_pred + R)  # Kalman gain
        mastery_new = m_pred + K * (y - m_pred)
        P_new = (1 - K) * P_pred
        
        # Bound to [0,1]
        final_mastery = max(0.05, min(0.95, mastery_new))
        
        # 🔥 BULLETPROOF: Compute state delta instead of writing immediately
        learner_state = LearnerState.create_kalman(final_mastery, P_new)
        
        # Calculate metrics
        mastery_change = final_mastery - mastery
        
        # Calculate learning gain for transfer engine
        learning_gain = K * (y - m_pred)
        
        logger.debug(f"� KALMAN COMPUTED: {user_id}/{concept_id}")
        logger.debug(f"  mastery: {mastery:.3f} → {final_mastery:.3f}")
        logger.debug(f"  gain: K={K:.3f}, change: {mastery_change:.3f}")
        
        # 🔥 PURE FUNCTION: Return state delta for batch writing
        return {
            "mastery_before": mastery,
            "mastery_after": final_mastery,
            "mastery_change": mastery_change,
            "kalman_gain": K,
            "covariance": P_new,
            "learning_gain": learning_gain,
            "learner": "kalman",
            # 🔥 BULLETPROOF: Include state for batch writing
            "state_delta": {
                "learner_type": "kalman",
                "user_id": user_id,
                "concept_id": concept_id,
                "state": learner_state
            }
        }
    
    def get_state(self, user_id: str, concept_id: str) -> Tuple[float, float]:
        """Get current (mastery, covariance) from StateAdapter"""
        if not self.state_adapter:
            return (0.3, 0.1)  # Default: moderate mastery, high uncertainty
        
        try:
            state = self.state_adapter.get("kalman", user_id, concept_id)
            return state.mastery, state.covariance
        except Exception as e:
            logger.error(f" KALMAN READ FAILED: {user_id}/{concept_id} - {e}")
            return (0.3, 0.1)  # Default: moderate mastery, high uncertainty
    
    def get_state_from_canonical(self, canonical_state: dict) -> Tuple[float, float]:
        """Get mastery/covariance from canonical state (WRITE mode - no reads)"""
        # 🔥 PRODUCTION SAFETY: Ensure canonical_state is a dict
        if not isinstance(canonical_state, dict):
            canonical_state = {"kalman_mastery": canonical_state, "kalman_covariance": 0.1}
        
        # 🔥 FIX F-016: Read from learner-specific fields to ensure ensemble independence
        if canonical_state and "kalman_mastery" in canonical_state and "kalman_covariance" in canonical_state:
            mastery = canonical_state["kalman_mastery"]
            covariance = canonical_state["kalman_covariance"]
            return (mastery, covariance)
        
        # Fallback to shared mastery only if learner-specific fields missing (for backward compatibility)
        if canonical_state and "mastery" in canonical_state:
            mastery = canonical_state["mastery"]
            covariance = canonical_state.get("uncertainty", 0.1)  # Use uncertainty as covariance proxy (fallback)
            return (mastery, covariance)
        return (0.3, 0.1)  # Default
    
    def set_state(self, user_id: str, concept_id: str, state: Tuple[float, float]):
        """Store (mastery, covariance) via StateAdapter"""
        if not self.state_adapter:
            return
        
        try:
            mastery, P = state
            learner_state = LearnerState.create_kalman(mastery, P)
            self.state_adapter.set("kalman", user_id, concept_id, learner_state)
            logger.info(f"✅ KALMAN WRITE: {user_id}/{concept_id} = ({mastery:.3f}, {P:.3f})")
        except Exception as e:
            logger.error(f"❌ KALMAN WRITE FAILED: {user_id}/{concept_id} - {e}")
