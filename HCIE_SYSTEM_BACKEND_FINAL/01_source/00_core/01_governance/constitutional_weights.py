"""
Unified Learning Brain - Single function that defines ALL learning logic

This replaces the scattered approach with ONE canonical function that:
- READ mode: inference only (for API calls)
- WRITE mode: full update (for consumer)
- SIMULATION mode: for experiments and validation

Everything calls THIS ONE function - no more scattered logic!

🔥 BRAIN GOVERNANCE:
- JT (Objective Function) is the TOP-LEVEL CONTROL SIGNAL
- All adaptive behavior ultimately serves to maximize JT
- CONTROL variables: η, exploration, policy, ensemble weights
- STATE variables: mastery, uncertainty, ZPD, transfer (inform CONTROL)
- OBSERVE variables: metrics, regret, traces (dashboard/research only)
- PHASE 5 JT-AWARE POLICY: Policy selection maximizes expected future ΔJT
  - Old: STATE → POLICY (heuristic selection)
  - New: expected future ΔJT → POLICY (constitutional optimization)
  - Policies become governance instruments, not teaching styles
  - This makes policy temporally self-consistent with bandit/ensemble/η
- PHASE 6 CONSTITUTIONAL PURIFICATION: Remove hidden motivational priors
  - Old: policy_multiplier = hardcoded priors (hcie=1.12, heuristic=1.05, static=1.0, random=0.97)
  - New: policy_multiplier = expected_JT (learned from governance history)
  - Removes embedded pedagogical ideology and makes policy purely JT-driven
  - All subsystems now serve JT, not independent objectives

See BRAIN_GOVERNANCE.md for the complete governance architecture
"""

import random
import time
import logging
from typing import Dict, Any
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

try:
    from core.learning.learning_loop_engine_v2 import LearningLoopEngineV2
    from core.learning.learner_factory import LearnerFactory
    from core.bandit.bandit import ContextualBandit
    from core.learning.transfer_learning_engine import TransferLearningEngine
    from core.learning.research_logger import research_logger, MathematicalLogEntry
    from core.learning.adaptive_transfer_engine import AdaptiveTransferEngine
    from core.learning.research_logger import ResearchLogger
    from core.learning.real_dag_dependencies import RealDAGDependencies
    from core.learning.confidence_weighted_learner import ConfidenceWeightedLearner
    from core.learning.learning_metrics import LearningMetricsAggregator
    from core.learning.learner_state_protocol import LearnerState, LearnerType, LyapunovState, BayesianState, KalmanState
    print("✅ Full production stack imports successful")
except ImportError as e:
    print(f"⚠️ Production imports failed: {e}")
    # Fallback for testing
    try:
        from learning_loop_engine_v2 import LearningLoopEngineV2
        from learner_factory import LearnerFactory
        from transfer_learning_engine import TransferLearningEngine
        from adaptive_transfer_engine import AdaptiveTransferEngine
        print("✅ Local imports successful")
    except ImportError as e2:
        print(f"⚠️ Local imports failed: {e2}")
        # Final fallback - create minimal components
        print("⚠️ Using minimal components for testing")
        from core.learning.transfer_learning_engine import TransferLearningEngine

"""Extracted from `HCIE_SYSTEM_BACKENDV2/core/learning/unified_brain.py` by tools/migrate/split_unified_brain.py.

Symbols extracted: ConstitutionalWeights.
This file is byte-identical to the matching slice of the source.
"""

class ConstitutionalWeights:
    """
    🔥 Constitutional weight management with stability guards
    
    RESPONSIBILITIES:
    - Store and manage constitutional weights
    - Adapt weights with momentum smoothing (prevents oscillation)
    - Enforce constitutional bounds (sum=1, 0≤w≤1)
    - Track weight evolution for observability
    
    STABILITY GUARDS:
    - Momentum smoothing (prevents rapid oscillation)
    - Adaptive learning rate decay (prevents pathological collapse)
    - Bounds enforcement (prevents invalid weights)
    """
    
    def __init__(self, default_weights: Dict[str, float]):
        self.default_weights = default_weights.copy()
        self.weights = default_weights.copy()
        
        # Stability parameters
        self.momentum = 0.7  # Momentum for smoothing (prevents oscillation)
        self.weight_momentum = {k: 0.0 for k in default_weights}  # Track momentum per weight
        self.adaptation_rate = 0.1
        self.adaptation_rate_decay = 0.995  # Decay rate to prevent pathological collapse
        self.min_adaptation_rate = 0.01  # Minimum adaptation rate
        self.stability_threshold = 0.7
        
        # Weight evolution tracking
        self.weight_history = {k: [] for k in default_weights}
        self.adaptation_count = 0
    
    def adapt(self, stability_index: float, context: Dict[str, float]):
        """
        Adapt weights with momentum smoothing and stability guards

        STABILITY GUARDS:
        1. Momentum smoothing: w_new = momentum * w_old + (1-momentum) * w_target
        2. Adaptive rate decay: reduces adaptation over time to prevent collapse
        3. Stability constraint: reduces adaptation when unstable
        4. Bounds enforcement: ensures weights stay valid

        OPERATIONAL DEFINITIONS (Context Signals):
        - transfer_utilization: ratio of transfer score > 0.5 in recent window [0, 1]
        - challenge_mismatch_rate: ratio of |challenge - optimal| > threshold [0, 1]
        - exploration_need: ratio of uncertainty > threshold in recent window [0, 1]
        - zpd_alignment_rate: ratio of zpd_score > 0.5 in recent window [0, 1]

        Args:
            stability_index: Current stability index [0, 1]
            context: Context metrics for adaptation signals
        """
        self.adaptation_count += 1

        # Adaptive rate decay (prevents pathological weight collapse)
        current_adaptation_rate = max(
            self.adaptation_rate * (self.adaptation_rate_decay ** self.adaptation_count),
            self.min_adaptation_rate
        )

        # Stability constraint (reduce adaptation when unstable)
        if stability_index < self.stability_threshold:
            current_adaptation_rate *= 0.5  # Further reduce when unstable

        # Extract context signals with operational definitions
        transfer_utilization = context.get("transfer_utilization", 0.5)  # Ratio of transfer > 0.5
        challenge_mismatch_rate = context.get("challenge_mismatch_rate", 0.5)  # Ratio of mismatched challenges
        exploration_need = context.get("exploration_need", 0.5)  # Ratio of high uncertainty
        zpd_alignment_rate = context.get("zpd_alignment_rate", 0.5)  # Ratio of zpd > 0.5
        
        # Compute target weight updates (raw signals)
        # 🔥 FIX: Ensure w1 (ΔM - mastery gain) gets meaningful baseline signal
        # Previously w1 only increased when unstable, causing it to be suppressed
        # Now w1 gets a baseline signal + stability signal to ensure learning gain is primary
        target_updates = {
            "w1": current_adaptation_rate * (0.3 + 0.7 * (1 - stability_index)),  # Mastery: baseline + stability
            "w2": current_adaptation_rate * transfer_utilization,  # T_realized: increase when transfer utilized
            "w3": current_adaptation_rate * challenge_mismatch_rate,  # T_prospective: increase when challenge mismatched
            "w4": current_adaptation_rate * exploration_need,  # Challenge: increase when exploration needed
            "w5": current_adaptation_rate * exploration_need,  # Uncertainty: same signal as challenge
            "w6": current_adaptation_rate * zpd_alignment_rate  # ZPD: increase when aligned
        }
        
        # Apply momentum smoothing (prevents oscillation)
        for key in self.weights:
            self.weight_momentum[key] = (
                self.momentum * self.weight_momentum[key] + 
                (1 - self.momentum) * target_updates[key]
            )
            self.weights[key] += self.weight_momentum[key]
        
        # Enforce constitutional bounds
        self.enforce_bounds()
        
        # Track evolution
        for key in self.weights:
            self.weight_history[key].append(self.weights[key])
            if len(self.weight_history[key]) > 100:  # Keep last 100 updates
                self.weight_history[key] = self.weight_history[key][-100:]
    
    def enforce_bounds(self):
        """Enforce constitutional bounds: sum=1, 0≤w≤1"""
        # Normalize to sum to unity
        total = sum(self.weights.values())
        if total > 0:
            for key in self.weights:
                self.weights[key] /= total
        
        # Clip to [0, 1]
        for key in self.weights:
            self.weights[key] = np.clip(self.weights[key], 0, 1)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get weight metrics for observability"""
        return {
            "current_weights": self.weights.copy(),
            "default_weights": self.default_weights.copy(),
            "weight_changes": {k: self.weights[k] - self.default_weights[k] for k in self.weights},
            "adaptation_count": self.adaptation_count,
            "constitutional_bounds_verified": (
                abs(sum(self.weights.values()) - 1.0) < 0.01 and
                all(0 <= w <= 1 for w in self.weights.values())
            )
        }


# --- traceability ---------------------------------------------------------
__sliced_from__ = 'HCIE_SYSTEM_BACKENDV2/core/learning/unified_brain.py'
__symbol_ranges__ = {
    'ConstitutionalWeights': (82, 206),
}
