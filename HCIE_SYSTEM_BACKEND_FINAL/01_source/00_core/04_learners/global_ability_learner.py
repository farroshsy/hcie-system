"""
Global Ability Learner  (Path C, latent L1 — global macro capability).

Tracks the learner's CROSS-CONCEPT ability as a slow online estimate — distinct from the
per-concept Bayesian (L2) and the fatigue/drift Kalman (L3). This is the genuinely independent
third latent the ensemble was missing: in the de-risk probe it adds the strongest predictive signal
beyond per-concept Kalman, lifting the fused estimate above the single-learner ceiling.

De-risk evidence (REPRODUCIBLE, adversarially re-validated — `research_validation/scripts/probe_pathc_latents.py`,
report `research_validation/reports/pathc_revalidated.json`; Junyi 6.59M interactions, leak-free
pre-update horse race + out-of-sample user split, 2026-05-31): global-ability adds a **modest** signal
beyond per-concept Kalman — partial +0.154 | Kalman, but only **+0.100 | Kalman+base-rate** (it is largely
a per-user base rate); the net OOS R gain of adding it to Kalman is ≈ **+0.028** (a 2-latent change: Kalman
mastery + global ability). ⚠ The first pass also claimed a "+0.119 fatigue" latent — that was a label
leak (clean fatigue ≈ 0) and is CUT. ⚠ The edge rides on Junyi exercise-level sparsity; the live system
uses coarser concepts, so it is likely smaller in production. The robust, reproducible finding is that the
old 3-learner ensemble was redundant because the Bayesian learner is a *stiff Kalman* (a Kalman-matched
weak-prior+decay Beta recovers 94% of the Kalman gap, then adds +0.000). This learner is still a principled
per-user ability latent (IRT θ), but its empirical edge over Kalman is small — treat as future-work, not a
re-seal-grade rebuild.

Grounded in Item-Response-Theory global ability (Lord 1980): a learner has an overall proficiency
θ that shifts performance across ALL concepts, independent of any single concept's mastery. Here θ
is a robust online estimate of P(correct) across concepts — O(1) per interaction, no training, no
embedding (preserves the thesis's embedding-free / constant-time constraints).

State model: per-USER (cross-concept), NOT per-(user, concept) — that is exactly what makes it
independent of the per-concept learners. Persisted as canonical_state["global_ability"].
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .base_learner import BaseLearner

logger = logging.getLogger(__name__)

_PRIOR = 0.5          # uninformative global-ability prior (chance)
_ALPHA = 0.05         # EMA rate — SLOW (global ability is a slow-moving latent; cf. per-concept learners adapt fast)
_WARMUP_ALPHA = 0.20  # faster adaptation for the first few interactions (cold-start: move off the prior quickly)
_WARMUP_N = 10


class GlobalAbilityLearner(BaseLearner):
    """Cross-concept global ability latent (Path C L1). EMA estimate of P(correct) over all concepts."""

    def __init__(self, alpha: float = _ALPHA, prior: float = _PRIOR) -> None:
        super().__init__()
        self.alpha = alpha
        self.prior = prior
        # Per-user cross-concept state (read-mode fallback; write-mode uses canonical_state).
        self._theta: Dict[str, float] = {}
        self._n: Dict[str, int] = {}

    def _read(self, user_id: str, canonical_state: Optional[Dict[str, Any]]) -> tuple[float, int]:
        if canonical_state is not None and isinstance(canonical_state, dict) and "global_ability" in canonical_state:
            theta = float(canonical_state.get("global_ability", self.prior))
            n = int(canonical_state.get("global_ability_n", self._n.get(user_id, 0)))
            return theta, n
        return self._theta.get(user_id, self.prior), self._n.get(user_id, 0)

    def update(self, user_id: str, concept_id: str, interaction: Dict[str, Any],
               canonical_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """O(1) EMA update of the learner's GLOBAL (cross-concept) ability."""
        theta, n = self._read(user_id, canonical_state)
        y = 1.0 if interaction.get("correct", False) else 0.0

        # Cold-start: adapt faster for the first few interactions, then settle to the slow rate.
        alpha = _WARMUP_ALPHA if n < _WARMUP_N else self.alpha
        theta_new = alpha * y + (1.0 - alpha) * theta
        theta_new = min(1.0, max(0.0, theta_new))
        n_new = n + 1

        # Persist to internal fallback (read-mode); write-mode persistence flows via the return dict
        # into canonical_state, same contract as the other learners.
        self._theta[user_id] = theta_new
        self._n[user_id] = n_new

        return {
            "global_ability": theta_new,      # the L1 latent (cross-concept P(correct))
            "global_ability_n": n_new,
            "learner_type": "global_ability",
        }

    def get_ability(self, user_id: str, canonical_state: Optional[Dict[str, Any]] = None) -> float:
        """Read the current global ability without updating (for the fusion to consume)."""
        theta, _ = self._read(user_id, canonical_state)
        return theta

    def reset(self) -> None:
        """For deterministic replay across learners."""
        self._theta.clear()
        self._n.clear()
