"""JT-attributed ensemble fusion — extracted from unified_brain.py (Stage 2 of the split).

Self-contained (stdlib + numpy; no unified_brain module globals). Re-imported by
unified_brain.py; behaviour unchanged (golden-master gated).
"""
import os
import json
import threading
import logging
from typing import Dict
import numpy as np

logger = logging.getLogger(__name__)


class JTAttributedEnsemble:
    """
    🔥 JT-attributed learner contribution accounting

    CONTROL: Computes ensemble weights based on each learner's JT contribution
    - Tracks JT contribution per learner over rolling window
    - Uses EMA smoothing for slow weight updates (temporal separation)
    - Normalizes weights to sum to 1
    - Provides governance metrics for ensemble adaptation

    This transforms ensemble from static (0.33, 0.33, 0.34) to JT-driven adaptive.
    """

    def __init__(self, window_size: int = 100, ema_alpha: float = 0.1):
        """
        Initialize JT-attributed ensemble

        Args:
            window_size: Rolling window size for contribution tracking
            ema_alpha: EMA smoothing factor (smaller = slower adaptation)
        """
        self.window_size = window_size
        self.ema_alpha = ema_alpha

        # 🔥 ENSEMBLE-ABLATION DECISION (ENSEMBLE_ABLATION_2026-06-05.md):
        # Lyapunov is dead weight (worst predictor at every window, degrades
        # with depth) and drags the ensemble below pure Kalman. Canonical
        # mastery := 2-learner Kalman+Bayesian fusion. We CUT Lyapunov from the
        # FUSION by zeroing its weight and renormalizing Kalman+Bayesian, applied
        # at the weight-output boundary so EVERY consumer (the metrics-block
        # synthesis and the m_ensemble = Σ w·m synthesis) sees the 2-learner
        # fusion and it is robust to stale EMA weights persisted in Redis. The
        # Lyapunov learner still RUNS and its lyapunov_* columns are still
        # written (frontend/projections read them) — only its fusion weight is 0.
        # Reversible via HCIE_FUSION_CUT_LYAPUNOV=0.
        self._cut_lyapunov = (
            os.environ.get("HCIE_FUSION_CUT_LYAPUNOV", "1").strip().lower()
            not in ("0", "false", "no")
        )

        # 🔥 PHASE 2B: Thread safety lock for replay-critical ensemble state
        # Protects: jt_contributions, ema_weights modifications
        self._lock = threading.RLock()

        # Track JT contributions per learner (rolling window)
        self.jt_contributions = {
            "lyapunov": [],
            "bayesian": [],
            "kalman": []
        }

        # EMA-smoothed weights (CONTROL variable)
        self.ema_weights = {
            "lyapunov": 0.33,
            "bayesian": 0.33,
            "kalman": 0.34
        }

        # Governance metrics
        self.weight_update_count = 0
        self.last_J_t = None

        # 🔥 PHASE 3B: Redis persistence for replay-critical ensemble state
        try:
            import redis
            self.redis_client = redis.Redis(
                host='redis',
                port=6379,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("🔥 PHASE 3B: JTAttributedEnsemble Redis connected for ensemble persistence")
            # Load persisted state on startup
            self._load_ensemble_state()
        except Exception as e:
            logger.warning(f"🔥 PHASE 3B: Redis connection failed for ensemble persistence: {e}")
            self.redis_client = None

    def _save_ensemble_state(self):
        """
        🔥 PHASE 3B: Save replay-critical ensemble state to Redis for persistence
        
        Saves:
        - ema_weights (EMA-smoothed ensemble weights affecting future decisions)
        """
        if not self.redis_client:
            return

        with self._lock:
            try:
                # Save EMA weights
                weights_key = "governance:ensemble:ema_weights"
                weights_data = json.dumps(self.ema_weights)
                self.redis_client.setex(weights_key, 86400, weights_data)  # 24-hour TTL
                logger.debug("🔥 PHASE 3B: Saved ensemble EMA weights to Redis")
            except Exception as e:
                logger.warning(f"🔥 PHASE 3B: Failed to save ensemble state to Redis: {e}")

    def _load_ensemble_state(self):
        """
        🔥 PHASE 3B: Load replay-critical ensemble state from Redis for replay determinism
        
        Restores:
        - ema_weights (EMA-smoothed ensemble weights)
        """
        if not self.redis_client:
            return

        with self._lock:
            try:
                # Load EMA weights
                weights_key = "governance:ensemble:ema_weights"
                weights_data = self.redis_client.get(weights_key)
                if weights_data:
                    loaded_weights = json.loads(weights_data)
                    # Validate structure
                    if all(k in loaded_weights for k in self.ema_weights.keys()):
                        self.ema_weights = loaded_weights
                        logger.info(f"🔥 PHASE 3B: Loaded ensemble EMA weights from Redis: {loaded_weights}")
                    else:
                        logger.warning("🔥 PHASE 3B: Ensemble weights schema mismatch, using defaults")
            except Exception as e:
                logger.warning(f"🔥 PHASE 3B: Failed to load ensemble state from Redis: {e}")

    def record_learner_contribution(self, learner_name: str, J_t: float, learner_mastery: float):
        """
        Record a learner's contribution to JT
        
        🔥 PHASE 2B: Thread-safe with lock protecting jt_contributions and last_J_t

        Args:
            learner_name: Name of the learner (lyapunov, bayesian, kalman)
            J_t: Current JT value
            learner_mastery: This learner's mastery contribution
        """
        with self._lock:
            if learner_name not in self.jt_contributions:
                return

            # Contribution = learner's mastery * J_t (JT-attributed contribution)
            contribution = learner_mastery * abs(J_t)

            # Add to rolling window
            self.jt_contributions[learner_name].append(contribution)

            # Maintain window size
            if len(self.jt_contributions[learner_name]) > self.window_size:
                self.jt_contributions[learner_name].pop(0)

            self.last_J_t = J_t

    def update_weights(self) -> Dict[str, float]:
        """
        Update ensemble weights based on JT contributions
        
        🔥 PHASE 2B: Thread-safe with lock protecting ema_weights and weight_update_count

        Uses EMA smoothing for slow adaptation (temporal separation)

        Returns:
            Updated ensemble weights
        """
        with self._lock:
            # Calculate mean contribution per learner from rolling window
            mean_contributions = {}
            for learner_name in self.jt_contributions:
                contributions = self.jt_contributions[learner_name]
                if len(contributions) > 0:
                    mean_contributions[learner_name] = np.mean(contributions)
                else:
                    mean_contributions[learner_name] = 0.01  # Minimum contribution

            # Normalize to get raw weights
            total_contribution = sum(mean_contributions.values())
            if total_contribution > 0:
                raw_weights = {
                    learner_name: contrib / total_contribution
                    for learner_name, contrib in mean_contributions.items()
                }
            else:
                raw_weights = {
                    "lyapunov": 0.33,
                    "bayesian": 0.33,
                    "kalman": 0.34
                }

            # Apply EMA smoothing (slow adaptation)
            for learner_name in raw_weights:
                self.ema_weights[learner_name] = (
                    self.ema_alpha * raw_weights[learner_name] +
                    (1 - self.ema_alpha) * self.ema_weights[learner_name]
                )

            # Renormalize to ensure sum = 1
            total_weight = sum(self.ema_weights.values())
            if total_weight > 0:
                self.ema_weights = {
                    k: v / total_weight for k, v in self.ema_weights.items()
                }

            self.weight_update_count += 1

            # 🔥 PHASE 3B: Save ensemble state after weight update
            self._save_ensemble_state()

            # Record governance metrics
            try:
                from core.learning.metrics_governance import record_jt_dependency, record_control_path_entropy
                # Record JT dependency ratio (how much weights depend on JT)
                jt_dependency = self._calculate_jt_dependency()
                record_jt_dependency("ensemble", jt_dependency)

                # Record control path entropy (diversity of weight distribution)
                entropy = self._calculate_weight_entropy()
                record_control_path_entropy("ensemble", entropy)
            except ImportError:
                pass

            # Apply the canonical fusion policy (2-learner Kalman+Bayesian) to
            # the returned weights. The internal self.ema_weights still tracks
            # all three learners (so EMA adaptation + Redis persistence are
            # unchanged and reversible); only the consumed/synthesized weights
            # drop Lyapunov.
            return self._apply_fusion_policy(self.ema_weights.copy())

    def reset(self):
        """
        Reset ensemble to initial state (for deterministic replay across learners)
        
        🔥 PHASE 2B: Thread-safe with lock protecting jt_contributions, ema_weights
        """
        with self._lock:
            self.jt_contributions = {
                "lyapunov": [],
                "bayesian": [],
                "kalman": []
            }
            self.ema_weights = {
                "lyapunov": 0.33,
                "bayesian": 0.33,
                "kalman": 0.34
            }
            self.weight_update_count = 0
            self.last_J_t = None

    def _calculate_jt_dependency(self) -> float:
        """Calculate how much ensemble weights depend on JT (0-1)"""
        # If we have enough samples, JT dependency is high
        total_samples = sum(len(contribs) for contribs in self.jt_contributions.values())
        if total_samples >= self.window_size:
            return 0.9  # High JT dependency when window is full
        elif total_samples >= self.window_size // 2:
            return 0.5  # Medium JT dependency
        else:
            return 0.1  # Low JT dependency during warm-up

    def _calculate_weight_entropy(self) -> float:
        """Calculate entropy of weight distribution (higher = more diverse)"""
        weights = list(self.ema_weights.values())
        # Avoid log(0)
        weights = [w if w > 0 else 1e-10 for w in weights]
        entropy = -sum(w * np.log(w) for w in weights)
        return entropy

    def _apply_fusion_policy(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Apply the canonical fusion policy to a weight vector.

        2-learner decision (ENSEMBLE_ABLATION_2026-06-05.md): zero the Lyapunov
        fusion weight and renormalize Kalman+Bayesian to sum to 1. Returned to
        every consumer so the canonical/ensemble mastery becomes the 2-learner
        Kalman+Bayesian fusion. Robust to whatever the EMA/Redis state holds.
        If Kalman+Bayesian are both ~0 (degenerate), fall back to the input so
        we never emit an all-zero weight vector. No-op when HCIE_FUSION_CUT_
        LYAPUNOV=0.
        """
        if not getattr(self, "_cut_lyapunov", False):
            return weights
        w = dict(weights)
        kb = float(w.get("kalman", 0.0)) + float(w.get("bayesian", 0.0))
        if kb <= 1e-12:
            # degenerate (e.g. fresh state before any update): split evenly
            return {"lyapunov": 0.0, "bayesian": 0.5, "kalman": 0.5}
        return {
            "lyapunov": 0.0,
            "bayesian": float(w.get("bayesian", 0.0)) / kb,
            "kalman": float(w.get("kalman", 0.0)) / kb,
        }

    def get_weights(self) -> Dict[str, float]:
        """Get current ensemble weights (fusion policy applied)."""
        return self._apply_fusion_policy(self.ema_weights.copy())


