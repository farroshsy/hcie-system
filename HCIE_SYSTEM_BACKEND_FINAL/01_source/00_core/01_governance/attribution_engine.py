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

Symbols extracted: AttributionEngine.
This file is byte-identical to the matching slice of the source.
"""

class AttributionEngine:
    """
    🔥 Attribution computation with counterfactual decomposition
    
    RESPONSIBILITIES:
    - Compute JT attribution per component
    - Support both proportional and counterfactual attribution
    - Track attribution evolution for observability
    
    ATTRIBUTION METHODS:
    1. Proportional: attribution_i = w_i · N(component_i) / JT
    2. Counterfactual: attribution_i = JT - JT_without_component_i
    """
    
    def __init__(self, method: str = "proportional"):
        """
        Initialize attribution engine
        
        Args:
            method: Attribution method ("proportional" or "counterfactual")
        """
        self.method = method
        # 🔥 6D Governance: Attribution history for all six dimensions
        self.attribution_history = {
            "delta_m": [],
            "transfer_realized": [],
            "transfer_prospective": [],
            "challenge": [],
            "uncertainty": [],
            "zpd": []
        }
    
    def compute_attribution(
        self, 
        jt: float, 
        contributions: Dict[str, float],
        weights: Dict[str, float],
        normalized_components: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Compute JT attribution per component
        
        Args:
            jt: JT value
            contributions: Component contributions (w_i * N(component_i))
            weights: Current weights
            normalized_components: Normalized component values (for counterfactual)
        
        Returns:
            Attribution dictionary
        """
        if self.method == "proportional":
            return self._proportional_attribution(jt, contributions)
        elif self.method == "counterfactual":
            if normalized_components is None:
                raise ValueError("Counterfactual attribution requires normalized_components")
            return self._counterfactual_attribution(jt, weights, normalized_components)
        else:
            raise ValueError(f"Unknown attribution method: {self.method}")
    
    def _proportional_attribution(self, jt: float, contributions: Dict[str, float]) -> Dict[str, float]:
        """Proportional attribution: attribution_i = contribution_i / JT"""
        if jt == 0:
            return {key: 0.0 for key in contributions.keys()}
        
        attribution = {}
        for key, value in contributions.items():
            attribution[key] = value / jt
        
        self._track_attribution(attribution)
        return attribution
    
    def _counterfactual_attribution(
        self,
        jt: float,
        weights: Dict[str, float],
        normalized_components: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Counterfactual attribution: attribution_i = JT - JT_without_component_i

        This measures how much JT would change if the component were removed.
        """
        # Map weight keys to component names (6D governance)
        weight_to_component = {
            "w1": "delta_m",
            "w2": "transfer_realized",
            "w3": "transfer_prospective",
            "w4": "challenge",
            "w5": "uncertainty",
            "w6": "zpd"
        }

        attribution = {}

        for weight_key, component_name in weight_to_component.items():
            if weight_key not in weights:
                continue

            # Compute JT without this component
            weighted_sum_without = 0.0
            for other_weight_key, other_component_name in weight_to_component.items():
                if other_weight_key != weight_key and other_weight_key in weights:
                    weighted_sum_without += weights[other_weight_key] * normalized_components.get(other_component_name, 0.0)

            jt_without = 1 / (1 + np.exp(-weighted_sum_without))
            attribution[component_name] = jt - jt_without  # Attribution = difference

        # Normalize to sum to 1
        total = sum(abs(v) for v in attribution.values())
        if total > 0:
            for key in attribution:
                attribution[key] = abs(attribution[key]) / total

        self._track_attribution(attribution)
        return attribution
    
    def _track_attribution(self, attribution: Dict[str, float]):
        """Track attribution history"""
        for key, value in attribution.items():
            # Skip keys not in history (backward compatibility with old 5D data)
            if key in self.attribution_history:
                self.attribution_history[key].append(value)
                if len(self.attribution_history[key]) > 100:
                    self.attribution_history[key] = self.attribution_history[key][-100:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get attribution metrics for observability"""
        return {
            "attribution_method": self.method,
            "recent_attribution": {
                k: v[-10:] if v else [] 
                for k, v in self.attribution_history.items()
            }
        }


# --- traceability ---------------------------------------------------------
__sliced_from__ = 'HCIE_SYSTEM_BACKENDV2/core/learning/unified_brain.py'
__symbol_ranges__ = {
    'AttributionEngine': (386, 521),
}
