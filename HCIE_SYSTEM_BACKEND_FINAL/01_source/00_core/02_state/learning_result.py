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
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
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

Symbols extracted: LearningResult, build_learning_result.
This file is byte-identical to the matching slice of the source.
"""

@dataclass
class LearningResult:
    """Canonical result structure for all learning operations"""
    # Core learning state (no defaults)
    mastery: float
    uncertainty: float
    confidence: float
    
    # Learner-specific states (no defaults)
    lyapunov_mastery: float
    bayesian_alpha: float
    bayesian_beta: float
    kalman_mastery: float
    kalman_covariance: float
    
    # Ensemble information (no defaults)
    # CONTROL: ensemble_weights are now JT-driven (JT-attributed ensemble)
    ensemble_weights: Dict[str, float]
    ensemble_variance: float  # STATE: ensemble variance (used in adaptive η)
    
    # Policy information (no defaults)
    policy: str
    policy_multiplier: float
    
    # Transfer information (no defaults)
    transfer_amounts: Dict[str, float]
    transfer_efficiency: float
    
    # ZPD alignment (no defaults)
    zpd_target: float
    zpd_alignment_error: float
    zpd_score: float
    zpd_delta_signal: float  # 🔥 ADDED: Delta signal for optimization
    
    # Metadata (no defaults)
    timestamp: str  # 🔥 FIXED: Store as string to match isoformat()
    processing_mode: str
    processing_time: float  # 🔥 ADDED: Processing time for performance metrics
    
    # Objective function (with default)
    J_value: Optional[float] = None  # 🔥 ADDED: J_t objective function value
    
    # 🔥 CRITICAL: Additional fields for debugging and analytics (with defaults)
    confidence_adjusted_mastery: Optional[float] = None
    effective_learning_rate: Optional[float] = None
    mastery_delta: Optional[float] = None
    transfer_amount: Optional[float] = None
    event_id: Optional[str] = None
    interaction_id: Optional[str] = None
    adaptive_rate: Optional[float] = None  # 🔥 ADDED: Adaptive learning rate for research validation

    # 🔥 FIX F-030: Bandit policy and arm selection tracking
    arm_selected: Optional[str] = None  # Selected bandit arm (concept)
    policy_selected: Optional[str] = None  # Selected policy (hcie, heuristic, static, random)

    # 🔥 PHASE A: JT component decomposition (A3)
    jt_delta_m_contribution: Optional[float] = None
    jt_transfer_contribution: Optional[float] = None
    jt_transfer_prospective_contribution: Optional[float] = None  # 6D completion (Phase 2B)
    jt_challenge_contribution: Optional[float] = None
    jt_uncertainty_contribution: Optional[float] = None
    jt_zpd_contribution: Optional[float] = None
    jt_unclamped: Optional[float] = None
    jt_clamped: Optional[float] = None
    # Tier 2.5 V2 dims (HCIE_REDESIGN_V2); nullable for V1 trajectories.
    jt_baseline_difficulty_contribution: Optional[float] = None
    jt_challenge_event_contribution: Optional[float] = None
    jt_population_prior_contribution: Optional[float] = None
    jt_t_realized_v2_contribution: Optional[float] = None
    jt_v2_active: Optional[bool] = None
    jt_v2_state_snapshot: Optional[Dict[str, float]] = None
    jt_v2_challenge_event_fired: Optional[bool] = None
    jt_v2_challenge_event_reason: Optional[str] = None
    # Attribution share per dimension (normalized 0..1) + active 6D weights.
    jt_attribution: Optional[Dict[str, float]] = None
    weights_snapshot: Optional[Dict[str, float]] = None

    # F-024: interaction outcome for trajectory / Kafka consumers
    correct: Optional[bool] = None
    correctness: Optional[bool] = None

    # F-031: JT governance observability
    jt_volatility: Optional[float] = None
    exploration_pressure: Optional[float] = None
    stability_index: Optional[float] = None

    # Ensemble-semantics evidence (migration 019). Distinct semantic
    # layer from the JT 6D attribution above. See unified_brain.py for
    # the full design contract.
    ensemble_mastery_estimate: Optional[float] = None
    canonical_mastery_after: Optional[float] = None
    ensemble_variance_after: Optional[float] = None
    bayesian_mastery_after: Optional[float] = None
    bayesian_variance_after: Optional[float] = None
    kalman_gain_after: Optional[float] = None
    kalman_R_after: Optional[float] = None
    ensemble_weight_lyapunov: Optional[float] = None
    ensemble_weight_bayesian: Optional[float] = None
    ensemble_weight_kalman: Optional[float] = None
    learner_jt_contribution_lyapunov: Optional[float] = None
    learner_jt_contribution_bayesian: Optional[float] = None
    learner_jt_contribution_kalman: Optional[float] = None
    ensemble_weight_method: Optional[str] = None
    ensemble_ema_alpha: Optional[float] = None
    ensemble_softmax_temperature: Optional[float] = None
    mastery_delta_direct: Optional[float] = None
    transfer_amount_total: Optional[float] = None

def build_learning_result(data: Dict[str, Any]) -> LearningResult:
    """
    🔥 ENFORCED: Single source of truth for LearningResult construction
    Guarantees ALL required fields are present with proper defaults
    """
    # Apply defaults for missing fields
    complete_data = REQUIRED_FIELDS.copy()
    complete_data.update(data)
    
    # 🔥 DEBUG: Log what we're building
    logger.info(f"🔍 DEBUG: build_learning_result keys = {list(complete_data.keys())}")
    logger.info(f"🔍 DEBUG: build_learning_result mastery = {complete_data.get('mastery', 'MISSING')}")
    
    # 🔥 CRITICAL: For cached results, ensure required fields exist
    # Don't raise errors for legacy cached data - just fill defaults
    # This prevents system crashes when old cached data is replayed
    
    try:
        result = LearningResult(**complete_data)
        logger.info(f"🔍 DEBUG: LearningResult created successfully = {type(result)}")
        return result
    except Exception as e:
        logger.error(f"🔥 DEBUG: LearningResult construction failed: {e}")
        logger.error(f"🔥 DEBUG: complete_data = {complete_data}")
        raise


# --- traceability ---------------------------------------------------------
__sliced_from__ = 'HCIE_SYSTEM_BACKENDV2/core/learning/unified_brain.py'
__symbol_ranges__ = {
    'LearningResult': (1443, 1515),
    'build_learning_result': (1563, 1588),
}
