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
from typing import Dict, Any
from datetime import datetime
import numpy as np

from .in_memory_state import InMemoryState

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

Symbols extracted: MultiConceptWorkingState.
This file is byte-identical to the matching slice of the source.
"""

class MultiConceptWorkingState:
    """
    BULLETPROOF: Multi-concept state container for transfer and bandit operations
    Eliminates DB reads for all concepts during write mode
    """
    def __init__(self, main_concept: str, canonical_state: Dict[str, Any], redis_client=None, metrics_aggregator=None, policy_engine=None, signal_extractor=None, confidence_learner=None, transfer_engine=None, bandit=None, idempotency_manager=None, environment="production"):
        self.main_concept = main_concept
        self.states = {}
        self.states[main_concept] = InMemoryState(canonical_state or {})
        self.redis_client = redis_client
        self.metrics_aggregator = metrics_aggregator
        self.policy_engine = policy_engine
        self.signal_extractor = signal_extractor
        self.confidence_learner = confidence_learner
        self.transfer_engine = transfer_engine
        self.bandit = bandit
        self.idempotency_manager = idempotency_manager
        self.environment = environment
    
    def get_concept(self, concept_id: str, default_state: Dict[str, Any] = None) -> InMemoryState:
        """Get working state for a concept, creating default if needed"""
        if concept_id not in self.states:
            default = default_state or {
                "mastery": 0.3,
                "uncertainty": 0.2,
                "lyapunov_mastery": 0.3,
                "bayesian_alpha": 1.5,
                "bayesian_beta": 3.5,
                "kalman_mastery": 0.3,
                "kalman_covariance": 0.1,
            }
            self.states[concept_id] = InMemoryState(default)
        return self.states[concept_id]
    
    def get(self, concept_id: str, key: str, default=None):
        """Get value from specific concept's working state"""
        return self.get_concept(concept_id).get(key, default)
    
    def set(self, concept_id: str, key: str, value):
        """Set value in specific concept's working state"""
        self.get_concept(concept_id).set(key, value)
    
    def get_main_state(self) -> InMemoryState:
        """Get the main concept's working state"""
        return self.states[self.main_concept]
    
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Get all states as dict"""
        return {concept: state.to_dict() for concept, state in self.states.items()}


# --- traceability ---------------------------------------------------------
__sliced_from__ = 'HCIE_SYSTEM_BACKENDV2/core/learning/unified_brain.py'
__symbol_ranges__ = {
    'MultiConceptWorkingState': (1615, 1664),
}
