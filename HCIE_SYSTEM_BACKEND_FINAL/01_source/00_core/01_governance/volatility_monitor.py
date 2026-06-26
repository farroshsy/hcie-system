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
import threading
from typing import Dict, Any, Optional
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

Symbols extracted: VolatilityMonitor.
This file is byte-identical to the matching slice of the source.
"""

class VolatilityMonitor:
    """
    🔥 Volatility monitoring with component decomposition
    
    RESPONSIBILITIES:
    - Compute JT volatility over rolling window
    - Decompose volatility into components (exploration, reward, learner disagreement)
    - Track volatility evolution for observability
    - Compute exploration pressure from volatility
    
    VOLATILITY DECOMPOSITION:
    - Exploration volatility: volatility from exploration decisions
    - Reward volatility: volatility from reward signals
    - Learner disagreement volatility: volatility from ensemble disagreement
    """
    
    def __init__(self, window_size: int = 10, sigma_volatility: float = 0.2):
        self.window_size = window_size
        self.sigma_volatility = sigma_volatility

        # 🔥 Thread safety lock for soft-state modifications
        # Protects: jt_history, volatility_components
        self._lock = threading.RLock()

        # JT history
        self.jt_history = []

        # Component volatility tracking
        self.volatility_components = {
            "exploration": [],
            "reward": [],
            "learner_disagreement": []
        }
    
    def update(self, jt: float, context: Optional[Dict[str, float]] = None):
        """
        Update volatility monitor with new JT value

        🔥 Thread-safe with lock protecting jt_history and volatility_components

        Args:
            jt: Current JT value
            context: Optional context for component decomposition
        """
        with self._lock:
            self.jt_history.append(jt)

            # Limit history size
            max_history = self.window_size * 10
            if len(self.jt_history) > max_history:
                self.jt_history = self.jt_history[-max_history:]

            # Decompose volatility if context provided
            if context:
                self._decompose_volatility(jt, context)
    
    def _decompose_volatility(self, jt: float, context: Dict[str, float]):
        """
        Decompose volatility into components

        🔥 Thread-safe with lock protecting volatility_components
        (Called from within update() which already holds the lock)
        """
        # Exploration volatility: volatility from exploration decisions
        exploration_signal = context.get("exploration_signal", 0.5)
        self.volatility_components["exploration"].append(exploration_signal)

        # Reward volatility: volatility from reward signals
        reward_signal = context.get("reward_signal", 0.5)
        self.volatility_components["reward"].append(reward_signal)

        # Learner disagreement volatility: volatility from ensemble disagreement
        disagreement_signal = context.get("learner_disagreement", 0.5)
        self.volatility_components["learner_disagreement"].append(disagreement_signal)

        # Limit component history
        max_history = self.window_size * 10
        for key in self.volatility_components:
            if len(self.volatility_components[key]) > max_history:
                self.volatility_components[key] = self.volatility_components[key][-max_history:]
    
    def compute_volatility(self) -> float:
        """Compute JT volatility (standard deviation over window)"""
        if len(self.jt_history) < 2:
            return 0.0
        if len(self.jt_history) < self.window_size:
            return float(np.std(self.jt_history))
        recent_jt = self.jt_history[-self.window_size:]
        return float(np.std(recent_jt))
    
    def compute_exploration_pressure(self) -> float:
        """Compute exploration pressure from volatility"""
        volatility = self.compute_volatility()
        return 1 / (1 + np.exp(-volatility / self.sigma_volatility))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get volatility metrics for observability"""
        return {
            "volatility": self.compute_volatility(),
            "exploration_pressure": self.compute_exploration_pressure(),
            "volatility_components": {
                k: np.std(v[-self.window_size:]) if len(v) >= self.window_size else 0.0
                for k, v in self.volatility_components.items()
            } if all(len(v) >= self.window_size for v in self.volatility_components.values()) else {},
            "jt_history_length": len(self.jt_history)
        }


# --- traceability ---------------------------------------------------------
__sliced_from__ = 'HCIE_SYSTEM_BACKENDV2/core/learning/unified_brain.py'
__symbol_ranges__ = {
    'VolatilityMonitor': (208, 314),
}
