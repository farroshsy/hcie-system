"""Brain state types — extracted from unified_brain.py (Stage 3 of the split).

LearningResult (the canonical return type), build_learning_result + REQUIRED_FIELDS, and the
in-memory state/repository classes. Self-contained (stdlib only). Re-imported by
unified_brain.py so external importers (e.g. production_metrics) keep working; behaviour
unchanged (golden-master gated).
"""
import logging
from datetime import datetime
from dataclasses import dataclass, fields
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


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
    # Tier 2.5 V2 dims (HCIE_REDESIGN_V2 flag); None when V1 hot path active.
    # See research_validation/TIER_2_5_DESIGN_PLAN.md and jt_v2_signals.py.
    jt_baseline_difficulty_contribution: Optional[float] = None  # rename of challenge (S-FRONTEND only)
    jt_challenge_event_contribution: Optional[float] = None  # P-MASTERY + P-SELECTION
    jt_population_prior_contribution: Optional[float] = None  # P-MASTERY (cold-start)
    jt_t_realized_v2_contribution: Optional[float] = None  # target-aware T_realized v2
    jt_v2_active: Optional[bool] = None
    jt_v2_state_snapshot: Optional[Dict[str, float]] = None
    jt_v2_challenge_event_fired: Optional[bool] = None
    jt_v2_challenge_event_reason: Optional[str] = None
    # Attribution share per dimension (normalized 0..1) and the active
    # 6D weight vector at write time. Persisted as explicit JSONB so
    # SQL analytics / replay diffs do not require JSON archaeology of
    # raw_governance_snapshot.
    jt_attribution: Optional[Dict[str, float]] = None
    weights_snapshot: Optional[Dict[str, float]] = None

    # F-024: interaction outcome for trajectory / Kafka consumers
    correct: Optional[bool] = None
    correctness: Optional[bool] = None

    # F-031: JT governance observability
    jt_volatility: Optional[float] = None
    exploration_pressure: Optional[float] = None
    stability_index: Optional[float] = None

    # Ensemble-semantics evidence (migration 019). Kept SEMANTICALLY
    # DISTINCT from the JT 6D attribution above:
    #   - jt_*_contribution / jt_attribution: governance-component shares of |J_t|
    #   - ensemble_weight_* / learner_jt_contribution_*: per-learner shares of m_ensemble
    # Mixing them would poison the math audit.
    ensemble_mastery_estimate: Optional[float] = None  # m_ensemble (pre-governance)
    canonical_mastery_after: Optional[float] = None  # m_canonical (persisted state)
    ensemble_variance_after: Optional[float] = None  # Var([m_lyapunov, m_bayesian, m_kalman])
    bayesian_mastery_after: Optional[float] = None  # alpha/(alpha+beta)
    bayesian_variance_after: Optional[float] = None  # Beta variance
    kalman_gain_after: Optional[float] = None  # K = P_pred / (P_pred + R)
    kalman_R_after: Optional[float] = None  # observation noise actually used
    ensemble_weight_lyapunov: Optional[float] = None
    ensemble_weight_bayesian: Optional[float] = None
    ensemble_weight_kalman: Optional[float] = None
    learner_jt_contribution_lyapunov: Optional[float] = None
    learner_jt_contribution_bayesian: Optional[float] = None
    learner_jt_contribution_kalman: Optional[float] = None
    ensemble_weight_method: Optional[str] = None  # 'ema_l1' (live) vs 'softmax' (doc-claim)
    ensemble_ema_alpha: Optional[float] = None
    ensemble_softmax_temperature: Optional[float] = None  # None if method != softmax
    mastery_delta_direct: Optional[float] = None
    transfer_amount_total: Optional[float] = None

# 🔥 SINGLE SOURCE OF TRUTH: Enforced schema contract
# STATE variables describe cognitive state (mastery, uncertainty, ZPD, transfer)
# CONTROL variables affect behavior (ensemble_weights, policy)
# OBSERVE variables are for dashboard/research only (J_value, adaptive_rate)
REQUIRED_FIELDS = {
    # STATE: Core learning state
    "mastery": 0.3,
    "uncertainty": 0.2,
    "confidence": 0.8,
    # STATE: Learner-specific states
    "lyapunov_mastery": 0.3,
    "bayesian_alpha": 1.5,
    "bayesian_beta": 3.5,
    "kalman_mastery": 0.3,
    "kalman_covariance": 0.1,
    # CONTROL: ensemble_weights are now JT-driven (JT-attributed ensemble)
    "ensemble_weights": {"lyapunov": 0.33, "bayesian": 0.33, "kalman": 0.34},  # Initial weights, will adapt
    # STATE: ensemble variance (used in adaptive η)
    "ensemble_variance": 0.02,
    # CONTROL: policy (should be JT-aware)
    "policy": "default",
    "policy_multiplier": 1.0,
    # STATE: Transfer information
    "transfer_amounts": {},
    "transfer_efficiency": 0.0,
    # STATE: ZPD alignment
    "zpd_target": 0.3,
    "zpd_alignment_error": 0.0,
    "zpd_score": 0.8,
    "zpd_delta_signal": 0.0,
    # Metadata
    "timestamp": datetime.now().isoformat(),
    "processing_mode": "read",
    "processing_time": 0.0,
    # OBSERVE: Objective function (for dashboard/research)
    "J_value": None,
    "adaptive_rate": None,
    # 🔥 PHASE A: JT component decomposition (A3) — 6D + attribution + weights
    "jt_delta_m_contribution": None,
    "jt_transfer_contribution": None,
    "jt_transfer_prospective_contribution": None,
    "jt_challenge_contribution": None,
    "jt_uncertainty_contribution": None,
    "jt_zpd_contribution": None,
    "jt_unclamped": None,
    "jt_clamped": None,
    "jt_attribution": None,
    "weights_snapshot": None,
    # Ensemble-semantics evidence (migration 019)
    "ensemble_mastery_estimate": None,
    "canonical_mastery_after": None,
    "ensemble_variance_after": None,
    "bayesian_mastery_after": None,
    "bayesian_variance_after": None,
    "kalman_gain_after": None,
    "kalman_R_after": None,
    "ensemble_weight_lyapunov": None,
    "ensemble_weight_bayesian": None,
    "ensemble_weight_kalman": None,
    "learner_jt_contribution_lyapunov": None,
    "learner_jt_contribution_bayesian": None,
    "learner_jt_contribution_kalman": None,
    "ensemble_weight_method": None,
    "ensemble_ema_alpha": None,
    "ensemble_softmax_temperature": None,
    "mastery_delta_direct": None,
    "transfer_amount_total": None,
}

def build_learning_result(data: Dict[str, Any]) -> LearningResult:
    """
    🔥 ENFORCED: Single source of truth for LearningResult construction
    Guarantees ALL required fields are present with proper defaults
    """
    # Apply defaults for missing fields
    complete_data = REQUIRED_FIELDS.copy()
    complete_data.update(data)

    # Drop keys that aren't LearningResult fields. Read-mode result dicts carry extra
    # diagnostic keys (e.g. "state_source") that are not dataclass fields; passing them to
    # the constructor raises TypeError. Filter rather than crash (write path uses only valid
    # fields, so it is unaffected).
    _valid = {f.name for f in fields(LearningResult)}
    _dropped = [k for k in complete_data if k not in _valid]
    if _dropped:
        logger.debug(f"build_learning_result: dropping non-field keys {_dropped}")
        complete_data = {k: v for k, v in complete_data.items() if k in _valid}

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


class InMemoryState:
    """
    🔥 BULLETPROOF: Per-event state container for atomic writes
    Eliminates DB reads during write mode
    """
    def __init__(self, canonical_state: Dict[str, Any]):
        self.state = canonical_state.copy() if canonical_state else {}
    
    def get(self, key: str, default=None):
        """Get value from in-memory state"""
        return self.state.get(key, default)
    
    def set(self, key: str, value):
        """Set value in in-memory state"""
        self.state[key] = value
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple values"""
        self.state.update(updates)
    
    def to_dict(self) -> Dict[str, Any]:
        """Get full state as dict"""
        return self.state.copy()


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


class InMemoryLearningStateRepository:
    """
    🔥 BULLETPROOF: In-memory repository for research mode
    Same interface as Postgres repository but no infrastructure dependencies
    """
    def __init__(self):
        self.store = {}
    
    def get_state(self, user_id: str, concept: str) -> Optional[Dict[str, Any]]:
        """Get state from in-memory store"""
        return self.store.get((user_id, concept))
    
    def save_state(self, user_id: str, concept: str, state_data: Dict[str, Any]) -> bool:
        """Save state to in-memory store"""
        self.store[(user_id, concept)] = state_data
        return True
    
    def batch_save_states(self, batch_writes: List[Dict[str, Any]]) -> bool:
        """Batch save states atomically"""
        for write in batch_writes:
            key = (write['user_id'], write['concept'])
            self.store[key] = write['state_data']
        return True


