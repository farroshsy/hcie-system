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
import logging
from typing import Dict, Any, List
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

Symbols extracted: StabilityMonitor.
This file is byte-identical to the matching slice of the source.
"""

class StabilityMonitor:
    """
    🔥 Stability monitoring for governance
    
    RESPONSIBILITIES:
    - Compute stability index from JT history
    - Track stability evolution
    - Provide stability signals for adaptation
    
    STABILITY INDEX:
    - Formula: stability_index = 1 - (σ_JT / μ_JT)
    - Interpretation: 1 = perfectly stable, 0 = highly unstable
    """
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.stability_history = []
    
    def compute_stability_index(self, jt_history: List[float]) -> float:
        """
        Compute stability index from JT history with robust edge case handling

        ROBUST FORMULA (handles edge cases):
        - If mean near 0: Use absolute variance instead of coefficient of variation
        - If variance compression (sigmoid bounds): Use log-scale variance
        - Clamp to [0, 1] with smooth transition

        Args:
            jt_history: JT history list

        Returns:
            Stability index in [0, 1] (1 = perfectly stable)
        """
        if len(jt_history) < self.window_size:
            return 1.0  # Assume stable during warm-up

        recent_jt = jt_history[-self.window_size:]
        jt_mean = np.mean(recent_jt)
        jt_std = np.std(recent_jt)

        # Edge case 1: Mean near 0 (avoid division by zero and explosion)
        if jt_mean < 0.01:
            # Use absolute variance instead of coefficient of variation
            stability_index = 1.0 - jt_std
        else:
            # Edge case 2: Variance compression from sigmoid bounds (JT ∈ [0.5, 1.0])
            # Use log-scale to amplify small differences
            log_variance = np.log1p(jt_std / jt_mean)
            stability_index = 1.0 - log_variance

        self.stability_history.append(stability_index)

        # Limit history
        if len(self.stability_history) > 100:
            self.stability_history = self.stability_history[-100:]

        # Clamp to [0, 1] with smooth transition
        return max(0.0, min(1.0, stability_index))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get stability metrics for observability"""
        if not self.stability_history:
            return {"stability_index": 1.0, "stability_history": []}
        return {
            "stability_index": self.stability_history[-1],
            "stability_history": self.stability_history[-10:],  # Last 10 values
            "stability_trend": self.stability_history[-1] - self.stability_history[0] if len(self.stability_history) > 1 else 0.0
        }


# --- traceability ---------------------------------------------------------
__sliced_from__ = 'HCIE_SYSTEM_BACKENDV2/core/learning/unified_brain.py'
__symbol_ranges__ = {
    'StabilityMonitor': (316, 384),
}
