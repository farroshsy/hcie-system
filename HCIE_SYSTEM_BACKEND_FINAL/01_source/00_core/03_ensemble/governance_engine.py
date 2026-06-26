"""Constitutional JT governance — extracted from unified_brain.py (Stage 1 of the split).

Self-contained: depends only on stdlib + numpy (no unified_brain module globals). Holds the
governance cluster (ConstitutionalWeights, VolatilityMonitor, StabilityMonitor,
AttributionEngine, ConstitutionalJTGovernance). Re-imported by unified_brain.py so every
existing reference keeps working; behaviour unchanged (golden-master gated).
"""
import os
import json
import threading
import logging
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

logger = logging.getLogger(__name__)


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


class ConstitutionalJTGovernance:
    """
    🔥 Constitutional JT Governance - Principled decomposition, not heuristic aggregation

    CONSTITUTIONAL PRINCIPLES:
    1. Multi-Objective Governance: JT synthesizes six learning objectives through principled decomposition
    2. Scale Consistency: All components normalized to [0, 1] for scale-invariant governance
    3. Interpretability: Each component has clear semantic interpretation aligned with learning science
    4. Temporal Stability: JT exhibits bounded temporal variation for stable governance
    5. Adaptivity: Weights adapt to context while maintaining constitutional bounds
    6. Adaptive Normalization: Each component is normalized from its own rolling value history
       (min-max sigmoid); expected (prospective) vs realized transfer are kept as distinct upstream
       components, not as separate normalization reservoirs. (A dual-reservoir "epistemic separation"
       was designed in Phase 2A but never wired; removed 2026-06-16 as dead code.)

    MATHEMATICAL GROUNDING (from JT_GOVERNANCE_CONSTITUTION.md):
    - ΔM (Mastery Gain): Bayesian knowledge tracing (Corbett & Anderson, 1995)
    - T_realized (Transfer Score): Analogical transfer theory (Singley & Anderson, 1989)
    - T_prospective (Prospective Transfer): Predicted structural utility from DAG topology
    - C (Challenge Score): Zone of proximal development (Vygotsky, 1978)
    - U (Uncertainty Score): Information theory (Shannon, 1948)
    - Z (ZPD Score): Zone of proximal development (Vygotsky, 1978)

    ARCHITECTURE (Composed Classes):
    - ConstitutionalWeights: Weight management with stability guards (momentum, decay, bounds)
    - VolatilityMonitor: Volatility computation with component decomposition
    - StabilityMonitor: Stability index computation
    - AttributionEngine: Attribution computation (proportional/counterfactual)

    EXECUTION ORDER (Explicit):
    1. Normalize components → 2. Compute weighted sum → 3. Apply sigmoid → 4. Update volatility monitor → 5. Compute stability index → 6. Adapt weights → 7. Compute attribution

    OPERATIONAL MEASURABILITY:
    - All governance components are measurable and logged
    - Governance distinguishable from weighted heuristics
    - Stability constraints enforced
    - Constitutional bounds enforced
    """

    def __init__(self, window_size: int = 10, attribution_method: str = "proportional"):
        """
        Initialize constitutional JT governance with composed classes

        Args:
            window_size: Rolling window size for volatility and stability computation
            attribution_method: Attribution method ("proportional" or "counterfactual")
        """
        self.window_size = window_size
        
        # 🔥 PHASE 2A: Thread safety lock for replay-critical governance state
        # Protects: component_history, normalization_state, weights_manager modifications
        self._lock = threading.RLock()

        # 🔥 PHASE 2A: 6D Constitutional Governance Space
        # Constitutional weights (default: principled decomposition)
        default_weights = {
            "w1": 0.25,  # ΔM: Mastery gain (primary)
            "w2": 0.15,  # T_realized: Realized transfer
            "w3": 0.15,  # T_prospective: Prospective structural utility
            "w4": 0.15,  # C: Challenge
            "w5": 0.15,  # U: Uncertainty
            "w6": 0.15   # Z: ZPD
        }

        # 🔥 PHASE 2A: Governance dimensionality versioning
        self.jt_dimension_labels = [
            "delta_m",
            "transfer_realized",
            "transfer_prospective",
            "challenge",
            "uncertainty",
            "zpd"
        ]
        self.jt_schema_version = "6D.1.0"  # 6D governance space, version 1.0

        # Initialize composed classes
        self.weights_manager = ConstitutionalWeights(default_weights)
        self.volatility_monitor = VolatilityMonitor(window_size, sigma_volatility=0.2)
        self.stability_monitor = StabilityMonitor(window_size)
        self.attribution_engine = AttributionEngine(method=attribution_method)

        # 🔥 PHASE 2A: Component history for attribution tracking (6D)
        self.component_history = {
            "delta_m": [],
            "transfer_realized": [],
            "transfer_prospective": [],  # Dormant initially (value = 0)
            "challenge": [],
            "uncertainty": [],
            "zpd": []
        }

        # 🔥 PHASE 2A: Normalization state with expected/realized namespace isolation
        # Expected: pre-selection governance signals (challenge, uncertainty, zpd, prospective)
        # Realized: post-interaction governance signals (delta_m, transfer_realized)
        self.normalization_state = {
            "expected": {
                "challenge": {"mean": 0.0, "std": 1.0, "count": 0},
                "uncertainty": {"mean": 0.0, "std": 1.0, "count": 0},
                "zpd": {"mean": 0.0, "std": 1.0, "count": 0},
                "transfer_prospective": {"mean": 0.0, "std": 1.0, "count": 0},
            },
            "realized": {
                "delta_m": {"mean": 0.0, "std": 1.0, "count": 0},
                "transfer_realized": {"mean": 0.0, "std": 1.0, "count": 0},
            },
            "bootstrap_distribution_generated": False,
            "normalization_warmup_complete": False,
            "warmup_count": 0
        }

        # Scale parameters for normalization
        # 🔥 INCREASED JT DISCRIMINATIVE POWER: Wider sigma values to reduce sigmoid compression
        self.scale_params = {
            "sigma_delta_m": 0.5,  # Increased from 0.1 to reduce compression
            "sigma_challenge": 0.5,  # Increased from 0.2 to reduce compression
            "sigma_zpd": 0.5,  # Increased from 0.2 to reduce compression
            "u_max": 0.1,  # Maximum ensemble variance (per formal specification)
            "use_final_sigmoid": True  # 🔥 FINAL: Re-enabled sigmoid. Phase C evaluation showed sigmoid provides necessary nonlinearity to balance governance signals (uncertainty elasticity 0.120 → 0.510 without sigmoid). Normalization fix (Phase A+B) is the critical improvement.
        }

        # 🔥 PHASE 3A: Redis persistence for replay-critical governance state
        try:
            import redis
            self.redis_client = redis.Redis(
                host='redis',
                port=6379,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("🔥 PHASE 3A: ConstitutionalJTGovernance Redis connected for governance persistence")
            # Load persisted state on startup
            self._load_governance_state()
        except Exception as e:
            logger.warning(f"🔥 PHASE 3A: Redis connection failed for governance persistence: {e}")
            self.redis_client = None

    def _save_governance_state(self):
        """
        🔥 PHASE 3A: Save replay-critical governance state to Redis for persistence
        
        Saves:
        - weights_manager.weights (adaptive weights affecting future decisions)
        - normalization_state (normalization reservoirs affecting future normalization)
        """
        if not self.redis_client:
            return

        with self._lock:
            try:
                # Save adaptive weights
                weights_key = "governance:constitutional:weights"
                weights_data = json.dumps(self.weights_manager.weights)
                self.redis_client.setex(weights_key, 86400, weights_data)  # 24-hour TTL
                logger.debug("🔥 PHASE 3A: Saved governance weights to Redis")

                # Save normalization state
                norm_key = "governance:constitutional:normalization"
                norm_data = json.dumps(self.normalization_state)
                self.redis_client.setex(norm_key, 86400, norm_data)  # 24-hour TTL
                logger.debug("🔥 PHASE 3A: Saved normalization state to Redis")
            except Exception as e:
                logger.warning(f"🔥 PHASE 3A: Failed to save governance state to Redis: {e}")

    def _load_governance_state(self):
        """
        🔥 PHASE 3A: Load replay-critical governance state from Redis for replay determinism
        
        Restores:
        - weights_manager.weights (adaptive weights)
        - normalization_state (normalization reservoirs)
        """
        if not self.redis_client:
            return

        with self._lock:
            try:
                # Load adaptive weights
                weights_key = "governance:constitutional:weights"
                weights_data = self.redis_client.get(weights_key)
                if weights_data:
                    loaded_weights = json.loads(weights_data)
                    # Validate schema version compatibility
                    if all(k in loaded_weights for k in self.weights_manager.weights.keys()):
                        self.weights_manager.weights = loaded_weights
                        logger.info(f"🔥 PHASE 3A: Loaded governance weights from Redis: {loaded_weights}")
                    else:
                        logger.warning("🔥 PHASE 3A: Governance weights schema mismatch, using defaults")

                # Load normalization state
                norm_key = "governance:constitutional:normalization"
                norm_data = self.redis_client.get(norm_key)
                if norm_data:
                    loaded_norm = json.loads(norm_data)
                    # Validate structure
                    if "expected" in loaded_norm and "realized" in loaded_norm:
                        self.normalization_state = loaded_norm
                        logger.info("🔥 PHASE 3A: Loaded normalization state from Redis")
                    else:
                        logger.warning("🔥 PHASE 3A: Normalization state schema mismatch, using defaults")
            except Exception as e:
                logger.warning(f"🔥 PHASE 3A: Failed to load governance state from Redis: {e}")

    def normalize_component(self, component: str, value: float) -> float:
        """
        Normalize component to [0, 1] for scale consistency

        🔥 FIX F-033: Adaptive normalization using actual data range from history
        This ensures components respond to per-step state changes instead of being constant

        Args:
            component: Component name (delta_m, transfer_realized, transfer_prospective, challenge, uncertainty, zpd)
            value: Raw component value

        Returns:
            Normalized value in [0, 1]

        Note (clamp / magnitude-discard): each branch clips (value - min)/range to [0, 1] before the
        sigmoid, so a value outside the observed historical range SATURATES — its excess magnitude is
        intentionally discarded to keep every JT contribution bounded and comparable. The F4 zero-guard
        below maps a genuinely-zero raw signal to exactly 0 (not the centered-sigmoid floor σ(−2.5)≈0.076)
        for the sigmoid-normalized components.
        """
        # 🔥 FIX F-033: Use adaptive normalization based on component history
        history = self.component_history.get(component, [])

        # 🔥 FIX F4 (zero-guard): a genuinely-zero raw signal must contribute 0, not the centered-sigmoid
        # floor σ(−2.5) ≈ 0.076. Scoped to the SIGMOID-normalized components only — challenge uses a
        # Gaussian and uncertainty an inversion, where value≈0 legitimately maps high, so they are excluded.
        # (transfer_prospective already guards itself below.) Requires a Phase-2 re-seal to take effect.
        if component in ("delta_m", "transfer_realized", "zpd") and abs(value) <= 1e-9:
            return 0.0

        if component == "delta_m":
            # Adaptive sigmoid: use actual range from history
            if len(history) > 10:
                min_val, max_val = min(history), max(history)
                range_val = max_val - min_val if max_val != min_val else 0.1
                # 🔥 PASS 1 FIX (Phase B): Clip to [0,1] before sigmoid to enforce boundedness
                normalized = np.clip((value - min_val) / max(range_val, 1e-6), 0.0, 1.0)
                return 1 / (1 + np.exp(-(normalized - 0.5) * 5))  # Sigmoid centered at 0.5
            else:
                # Fallback to fixed sigma during warm-up
                return 1 / (1 + np.exp(-value / self.scale_params["sigma_delta_m"]))
        elif component == "transfer_realized":
            # 🔥 PHASE 2A: Adaptive sigmoid normalization for realized transfer
            if len(history) > 10:
                min_val, max_val = min(history), max(history)
                range_val = max_val - min_val if max_val != min_val else 0.1
                # 🔥 PASS 1 FIX (Phase B): Clip to [0,1] before sigmoid to enforce boundedness
                normalized = np.clip((value - min_val) / max(range_val, 1e-6), 0.0, 1.0)
                return 1 / (1 + np.exp(-(normalized - 0.5) * 5))  # Sigmoid centered at 0.5
            else:
                # Fallback to fixed normalization during warm-up
                return min(value / 1.0, 1.0)
        elif component == "transfer_prospective":
            # 🔥 PHASE 2A: Dormant normalization for prospective transfer (returns 0 during Phase A)
            # This ensures 6D pipeline works with 5D active governance during infrastructure phase
            if value == 0.0:
                return 0.0  # Dormant: no prospective contribution yet
            if len(history) > 10:
                min_val, max_val = min(history), max(history)
                range_val = max_val - min_val if max_val != min_val else 0.1
                normalized = np.clip((value - min_val) / max(range_val, 1e-6), 0.0, 1.0)
                return 1 / (1 + np.exp(-(normalized - 0.5) * 5))
            else:
                return min(value / 1.0, 1.0)
        elif component == "challenge":
            # 🔥 FIX F-033: Adaptive Gaussian decay using actual range
            if len(history) > 10:
                min_val, max_val = min(history), max(history)
                range_val = max_val - min_val if max_val != min_val else 0.1
                # 🔥 PASS 1 FIX (Phase B): Clip to [0,1] before Gaussian to enforce boundedness
                normalized = np.clip((value - min_val) / max(range_val, 1e-6), 0.0, 1.0)
                return np.exp(-normalized**2 / 2)  # Gaussian centered at 0
            else:
                # Fallback to fixed sigma during warm-up
                return np.exp(-value**2 / (2 * self.scale_params["sigma_challenge"]**2))
        elif component == "uncertainty":
            # 🔥 FIX F-033: Adaptive inverted normalization
            if len(history) > 10:
                min_val, max_val = min(history), max(history)
                range_val = max_val - min_val if max_val != min_val else 0.01
                # 🔥 PASS 1 FIX (Phase B): Clip to [0,1] before inversion — critical.
                # Without this, range→ε causes normalized→huge, and 1.0-normalized→massively negative,
                # which previously caused jt_uncertainty_norm max=191.88.
                normalized = np.clip((value - min_val) / max(range_val, 1e-6), 0.0, 1.0)
                return 1.0 - normalized  # Inverted: lower uncertainty = higher contribution; now guaranteed ∈ [0,1]
            else:
                # Fallback to fixed u_max during warm-up
                return max(0.0, 1.0 - (value / self.scale_params["u_max"]))
        elif component == "zpd":
            # 🔥 FIX F-033: Adaptive sigmoid for ZPD
            if len(history) > 10:
                min_val, max_val = min(history), max(history)
                range_val = max_val - min_val if max_val != min_val else 0.1
                # 🔥 PASS 1 FIX (Phase B): Clip to [0,1] before sigmoid to enforce boundedness
                normalized = np.clip((value - min_val) / max(range_val, 1e-6), 0.0, 1.0)
                return 1 / (1 + np.exp(-(normalized - 0.5) * 5))  # Sigmoid centered at 0.5
            else:
                # Fallback to fixed sigma during warm-up
                return 1 / (1 + np.exp(-value / self.scale_params["sigma_zpd"]))
        else:
            # Default: sigmoid normalization
            return 1 / (1 + np.exp(-value / 0.1))

    def compute_jt(
        self,
        delta_m: float,
        transfer_realized: float,
        transfer_prospective: float,
        challenge: float,
        uncertainty: float,
        zpd: float,
        context: Optional[Dict[str, float]] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute JT with constitutional semantics using composed classes (6D Governance)
        
        🔥 PHASE 2A: Thread-safe with lock protecting all shared state modifications

        EXECUTION ORDER (Explicit):
        1. Normalize components → 2. Compute weighted sum → 3. Apply sigmoid →
        4. Update volatility monitor → 5. Compute stability index → 6. Adapt weights → 7. Compute attribution

        Formula: JT = σ(w₁·N(ΔM) + w₂·N(T_realized) + w₃·N(T_prospective) + w₄·N(C) + w₅·N(U) + w₆·N(Z))

        Args:
            delta_m: Mastery gain
            transfer_realized: Realized transfer score (post-interaction)
            transfer_prospective: Prospective transfer score (pre-selection, structural utility)
            challenge: Challenge score
            uncertainty: Uncertainty score
            zpd: ZPD score
            context: Optional context for volatility decomposition and weight adaptation

        Returns:
            JT value and component contributions
        """
        with self._lock:
            # Step 1: Normalize components to [0, 1] for scale consistency (6D)
            n_delta_m = self.normalize_component("delta_m", delta_m)
            n_transfer_realized = self.normalize_component("transfer_realized", transfer_realized)
            n_transfer_prospective = self.normalize_component("transfer_prospective", transfer_prospective)
            n_challenge = self.normalize_component("challenge", challenge)
            n_uncertainty = self.normalize_component("uncertainty", uncertainty)
            n_zpd = self.normalize_component("zpd", zpd)

            # Research-only counterfactual JT ablation hook.
            #
            # HCIE_JT_DISABLED_COMPONENTS is set by the Step-4 validation
            # harness while launching one container per ablation condition.
            # It zeros the normalized contribution inside the real runtime
            # governance path, instead of editing persisted rows post-hoc.
            # Raw component histories are still recorded below so the audit
            # can see the signal was present but causally removed.
            disabled_components = {
                part.strip()
                for part in os.getenv("HCIE_JT_DISABLED_COMPONENTS", "").split(",")
                if part.strip()
            }
            if disabled_components:
                if "delta_m" in disabled_components:
                    n_delta_m = 0.0
                if "transfer_realized" in disabled_components:
                    n_transfer_realized = 0.0
                if "transfer_prospective" in disabled_components:
                    n_transfer_prospective = 0.0
                if "challenge" in disabled_components:
                    n_challenge = 0.0
                if "uncertainty" in disabled_components:
                    n_uncertainty = 0.0
                if "zpd" in disabled_components:
                    n_zpd = 0.0

            # 🔥 PASS 1 FIX (Phase A): Store RAW values for correct adaptive normalization reference.
            # Previously stored normalized values, creating a double-normalization feedback loop:
            #   raw_t → normalize(using raw history) → store normalized_t
            #   raw_{t+1} → normalize(using normalized history!) → unbounded explosion
            # This caused jt_uncertainty_norm max=191.88 (physically impossible if bounded [0,1]).
            self.component_history["delta_m"].append(delta_m)
            self.component_history["transfer_realized"].append(transfer_realized)
            self.component_history["transfer_prospective"].append(transfer_prospective)  # Dormant: 0 during Phase A
            self.component_history["challenge"].append(challenge)
            self.component_history["uncertainty"].append(uncertainty)
            self.component_history["zpd"].append(zpd)

            # Limit history size
            max_history = self.window_size * 10
            for key in self.component_history:
                if len(self.component_history[key]) > max_history:
                    self.component_history[key] = self.component_history[key][-max_history:]

            # Step 2: Compute weighted sum using weights from composed class (6D)
            weights = self.weights_manager.weights
            weighted_sum = (
                weights["w1"] * n_delta_m +
                weights["w2"] * n_transfer_realized +
                weights["w3"] * n_transfer_prospective +
                weights["w4"] * n_challenge +
                weights["w5"] * n_uncertainty +
                weights["w6"] * n_zpd
            )

            # 🔥 FIX F-026: Log JT computation details for verification
            print("🔥 JT COMPUTATION (F-026 FIX) - 6D Governance:")
            print(f"   Raw inputs: delta_m={delta_m:.6f}, transfer_realized={transfer_realized:.6f}, transfer_prospective={transfer_prospective:.6f}, challenge={challenge:.6f}, uncertainty={uncertainty:.6f}, zpd={zpd:.6f}")
            print(f"   Normalized: n_delta_m={n_delta_m:.6f}, n_transfer_realized={n_transfer_realized:.6f}, n_transfer_prospective={n_transfer_prospective:.6f}, n_challenge={n_challenge:.6f}, n_uncertainty={n_uncertainty:.6f}, n_zpd={n_zpd:.6f}")
            print(f"   Weights: w1={weights['w1']:.6f}, w2={weights['w2']:.6f}, w3={weights['w3']:.6f}, w4={weights['w4']:.6f}, w5={weights['w5']:.6f}, w6={weights['w6']:.6f}")
            print(f"   Weighted sum: {weighted_sum:.6f}")
            print(f"   Schema version: {self.jt_schema_version}")
            print(f"   Scale params: {self.scale_params}")

            # Step 3: Sigmoid normalization for bounded governance (OPTIONAL)
            # 🔥 INCREASED JT DISCRIMINATIVE POWER: Optional sigmoid compression
            if self.scale_params.get("use_final_sigmoid", True):
                jt = 1 / (1 + np.exp(-weighted_sum))
                print(f"   Final sigmoid applied: JT={jt:.6f}")
            else:
                # Use raw weighted sum for higher discriminative power
                jt = weighted_sum
                print(f"   Raw weighted sum used: JT={jt:.6f}")

            # Step 4: Update volatility monitor (with context for decomposition)
            self.volatility_monitor.update(jt, context)

            # Step 5: Compute stability index
            stability_index = self.stability_monitor.compute_stability_index(
                self.volatility_monitor.jt_history
            )

            # Step 6: Adapt weights (if context provided)
            if context:
                self.weights_manager.adapt(stability_index, context)
                # 🔥 PHASE 3A: Save governance state after weight adaptation
                self._save_governance_state()

            # Step 7: Compute component contributions for attribution (6D)
            contributions = {
                "delta_m": weights["w1"] * n_delta_m,
                "transfer_realized": weights["w2"] * n_transfer_realized,
                "transfer_prospective": weights["w3"] * n_transfer_prospective,  # Dormant: 0 during Phase A
                "challenge": weights["w4"] * n_challenge,
                "uncertainty": weights["w5"] * n_uncertainty,
                "zpd": weights["w6"] * n_zpd
            }

            return jt, contributions

    # ============================================================================
    # PHASE 2A: NORMALIZATION STATE MANAGEMENT
    # ============================================================================

    def reset_normalization_state(self, seed: Optional[int] = None):
        """
        🔥 PHASE 2E: Reset normalization state per seed to prevent cold-start leakage
        
        🔥 PHASE 2A: Thread-safe with lock protecting normalization_state and component_history

        This ensures that each experimental run starts with fresh normalization
        reservoirs, preventing cross-run contamination.

        Args:
            seed: Random seed for this experimental run
        """
        with self._lock:
            # Reset normalization state to initial values
            self.normalization_state = {
                "expected": {
                    "challenge": {"mean": 0.0, "std": 1.0, "count": 0},
                    "uncertainty": {"mean": 0.0, "std": 1.0, "count": 0},
                    "zpd": {"mean": 0.0, "std": 1.0, "count": 0},
                    "transfer_prospective": {"mean": 0.0, "std": 1.0, "count": 0},
                },
                "realized": {
                    "delta_m": {"mean": 0.0, "std": 1.0, "count": 0},
                    "transfer_realized": {"mean": 0.0, "std": 1.0, "count": 0},
                },
                "bootstrap_distribution_generated": False,
                "normalization_warmup_complete": False,
                "warmup_count": 0,
                "seed": seed  # Track seed for reproducibility
            }

            # Clear component history
            for key in self.component_history:
                self.component_history[key] = []

            logger.info(f"🔥 PHASE 2E: Normalization state reset for seed {seed}")

    # ============================================================================
    # BACKWARD COMPATIBILITY PROPERTIES (For debug endpoints)
    # ============================================================================
    
    @property
    def jt_history(self) -> List[float]:
        """Backward compatibility: Access JT history from volatility monitor"""
        return self.volatility_monitor.jt_history
    
    @property
    def weights(self) -> Dict[str, float]:
        """Backward compatibility: Access weights from weights manager"""
        return self.weights_manager.weights
    
    @property
    def default_weights(self) -> Dict[str, float]:
        """Backward compatibility: Access default weights from weights manager"""
        return self.weights_manager.default_weights

    # ============================================================================
    # DELEGATED METHODS (Forward to composed classes)
    # ============================================================================

    def compute_volatility(self) -> float:
        """
        Compute JT volatility (delegated to VolatilityMonitor)

        Returns:
            JT volatility (standard deviation over window)
        """
        return self.volatility_monitor.compute_volatility()

    def compute_exploration_pressure(self) -> float:
        """
        Compute exploration pressure (delegated to VolatilityMonitor)

        Returns:
            Exploration pressure in [0, 1]
        """
        return self.volatility_monitor.compute_exploration_pressure()

    def compute_stability_index(self) -> float:
        """
        Compute stability index (delegated to StabilityMonitor)

        Returns:
            Stability index in [0, 1] (1 = perfectly stable)
        """
        return self.stability_monitor.compute_stability_index(self.jt_history)

    def compute_attribution(self, jt: float, contributions: Dict[str, float]) -> Dict[str, float]:
        """
        Compute JT attribution (delegated to AttributionEngine)

        Args:
            jt: JT value
            contributions: Component contributions

        Returns:
            Attribution dictionary
        """
        # Get normalized components for counterfactual attribution (6D governance)
        normalized_components = {
            "delta_m": self.component_history["delta_m"][-1] if self.component_history["delta_m"] else 0,
            "transfer_realized": self.component_history["transfer_realized"][-1] if self.component_history["transfer_realized"] else 0,
            "transfer_prospective": self.component_history["transfer_prospective"][-1] if self.component_history["transfer_prospective"] else 0,
            "challenge": self.component_history["challenge"][-1] if self.component_history["challenge"] else 0,
            "uncertainty": self.component_history["uncertainty"][-1] if self.component_history["uncertainty"] else 0,
            "zpd": self.component_history["zpd"][-1] if self.component_history["zpd"] else 0,
        }
        
        return self.attribution_engine.compute_attribution(
            jt, contributions, self.weights, normalized_components
        )

    def adapt_weights(self, stability_index: float, context: Dict[str, float]):
        """
        Adapt weights (delegated to ConstitutionalWeights)

        Args:
            stability_index: Current stability index
            context: Context metrics for adaptation signals
        """
        self.weights_manager.adapt(stability_index, context)

    def enforce_constitutional_bounds(self):
        """
        Enforce constitutional bounds (delegated to ConstitutionalWeights)
        """
        self.weights_manager.enforce_bounds()

    def get_governance_metrics(self) -> Dict[str, Any]:
        """
        Get governance metrics (aggregated from composed classes)

        Returns:
            Dictionary of governance metrics from all composed classes
        """
        return {
            **self.weights_manager.get_metrics(),
            **self.volatility_monitor.get_metrics(),
            **self.stability_monitor.get_metrics(),
            **self.attribution_engine.get_metrics(),
            "component_history": {
                key: values[-50:] if values else []  # Last 50 values
                for key, values in self.component_history.items()
            }
        }


