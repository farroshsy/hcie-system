"""
HCIE Tier 2.5 V2 JT signals — feature-flagged side branch (HCIE_REDESIGN_V2=1).

Implements the locked Tier 2.5 design (research_validation/TIER_2_5_DESIGN_PLAN.md):
  * BaselineDifficulty  -- rename of jt_challenge_contribution; S-FRONTEND only
  * Challenge_event     -- NEW; P-MASTERY + P-SELECTION; assessment-trigger + gamma * dM
  * PopulationPrior     -- NEW; closed-form Beta-Binomial sufficient stats per concept
  * PrereqDelta cache   -- DP accumulator powering target-aware T_realized v2
  * Welford covariance  -- online cross-dim covariance for synergy / governance

All accumulators are O(1) per interaction. No retraining, no embedding tables.
The module is intentionally side-effect-free at import time so it can be loaded
behind a feature flag without touching the V1 hot path.

Acceptance gates these signals must satisfy (Section 10 of the design plan):
  A1  -- HCIE_v2 overall AUC >= BKT - 0.005, beat all deep KT baselines
  A2  -- HCIE_v2 overall AUC >= BKT + 0.05 on >= 2/3 Bundle A datasets
  A3  -- selection ablation moves >=5% of arm choices for each P-* dim
  A4  -- Challenge_event r >= 0.30 on trigger subset
         PopulationPrior r >= 0.20 on cold-start subset
  A5  -- |corr(Kalman, Bayesian)| < 0.85; replay determinism <= 1e-6
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from threading import RLock
from typing import Dict, Mapping, Optional, Tuple


def redesign_v2_enabled() -> bool:
    """True if HCIE_REDESIGN_V2 env flag is set; default False (V1 hot path)."""
    return os.environ.get("HCIE_REDESIGN_V2", "").strip().lower() in ("1", "true", "yes")


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# 1. PopulationPrior  --  closed-form Beta-Binomial sufficient stats per concept.
#                         O(1) update, O(1) posterior mean / variance lookup.
#                         Replaces the implicit population prior that DKT/SAKT
#                         learn via embedding training.
# ---------------------------------------------------------------------------


@dataclass
class _BetaCounts:
    alpha: float = 1.0  # Jeffreys-style prior; cohort fit overrides on first warm-up
    beta: float = 1.0
    n: int = 0  # raw observation count for governance / cold-start gating

    def posterior_mean(self) -> float:
        denom = self.alpha + self.beta
        return self.alpha / denom if denom > 0 else 0.5

    def posterior_var(self) -> float:
        a, b = self.alpha, self.beta
        denom = (a + b) ** 2 * (a + b + 1.0)
        return (a * b / denom) if denom > 0 else 0.25


class PopulationPriorState:
    """
    Per-concept running Beta-Binomial sufficient stats.

    Update is O(1):  alpha += correct, beta += (1 - correct)
    Posterior mean is O(1):  alpha / (alpha + beta)

    For a learner with no observations on a concept, posterior_mean(c) is the
    cohort-derived prior P(correct | concept = c) -- exactly the cold-start
    signal that DKT learns via embedding training and BKT learns via offline
    fitting. We compute it online, embedding-free, with O(K) memory where
    K = number of distinct concepts.
    """

    def __init__(self, prior_alpha: float = 1.0, prior_beta: float = 1.0) -> None:
        self._counts: Dict[str, _BetaCounts] = {}
        self._lock = RLock()
        self._prior_alpha = float(prior_alpha)
        self._prior_beta = float(prior_beta)
        self._global = _BetaCounts(alpha=self._prior_alpha, beta=self._prior_beta)

    def warm_up(self, cohort_stats: Mapping[str, Tuple[int, int]]) -> None:
        """Seed alpha/beta from cohort sufficient statistics (correct, attempts)."""
        with self._lock:
            for concept, (correct, attempts) in cohort_stats.items():
                c = max(0, int(correct))
                a = max(c, int(attempts))
                self._counts[str(concept)] = _BetaCounts(
                    alpha=self._prior_alpha + c,
                    beta=self._prior_beta + (a - c),
                    n=a,
                )

    def update(self, concept: str, correct: bool) -> None:
        """O(1) sufficient-statistics update."""
        with self._lock:
            slot = self._counts.setdefault(
                str(concept),
                _BetaCounts(alpha=self._prior_alpha, beta=self._prior_beta),
            )
            if correct:
                slot.alpha += 1.0
            else:
                slot.beta += 1.0
            slot.n += 1
            if correct:
                self._global.alpha += 1.0
            else:
                self._global.beta += 1.0
            self._global.n += 1

    def posterior_mean(self, concept: str) -> float:
        with self._lock:
            slot = self._counts.get(str(concept))
            if slot is None:
                return self._global.posterior_mean()
            return slot.posterior_mean()

    def posterior_var(self, concept: str) -> float:
        with self._lock:
            slot = self._counts.get(str(concept))
            if slot is None:
                return self._global.posterior_var()
            return slot.posterior_var()

    def n_observations(self, concept: str) -> int:
        with self._lock:
            slot = self._counts.get(str(concept))
            return slot.n if slot is not None else 0

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        """Replay-deterministic snapshot for sealing."""
        with self._lock:
            return {
                k: {"alpha": v.alpha, "beta": v.beta, "n": v.n}
                for k, v in self._counts.items()
            } | {
                "__global__": {
                    "alpha": self._global.alpha,
                    "beta": self._global.beta,
                    "n": self._global.n,
                }
            }


# ---------------------------------------------------------------------------
# 2. PrereqDeltaAccumulator  --  exponentially-decayed running sum of recent
#                                 ΔM per concept. Powers the target-aware
#                                 T_realized v2: Σ_{p in prereqs(c)} ΔM_recent(p).
#                                 DP recurrence: s_t = lambda * s_{t-1} + dM_t
#                                 (lambda < 1 so old gains decay).
# ---------------------------------------------------------------------------


class PrereqDeltaAccumulator:
    """
    Per-(user, concept) exponentially-decayed running sum of ΔM.

    Lookup `recent_delta(user, concept)` is O(1).
    Update `record_delta(user, concept, dM)` is O(1).
    Computing T_realized v2 for target c is O(|prereqs(c)|) via lookups.
    """

    def __init__(self, decay: float = 0.85) -> None:
        if not 0.0 < decay <= 1.0:
            raise ValueError("decay must be in (0, 1]")
        self._decay = float(decay)
        self._sums: Dict[Tuple[str, str], float] = {}
        self._lock = RLock()

    def record_delta(self, user_id: str, concept_id: str, delta_m: float) -> None:
        d = _safe_float(delta_m)
        if d == 0.0:
            return
        key = (str(user_id), str(concept_id))
        with self._lock:
            prev = self._sums.get(key, 0.0)
            self._sums[key] = self._decay * prev + d

    def recent_delta(self, user_id: str, concept_id: str) -> float:
        with self._lock:
            return self._sums.get((str(user_id), str(concept_id)), 0.0)

    def realized_for(
        self,
        user_id: str,
        target_concept: str,
        prereq_weights: Mapping[str, float],
        target_mastery_before: float,
    ) -> float:
        """
        T_realized_v2(c) = (1 - M(c)) * Σ_{p in prereqs(c)} w(p,c) * recent_delta(p)

        Non-zero only when the learner has both:
          (a) gained mastery on a prereq recently (recent_delta > 0)
          (b) not yet mastered the target (M(c) < 1)
        Target-aware by construction; resolves the Tier-2 audit warning that
        the V1 T_realized was target-blind.
        """
        if not prereq_weights:
            return 0.0
        gap = max(0.0, 1.0 - _safe_float(target_mastery_before))
        if gap <= 0.0:
            return 0.0
        with self._lock:
            total = 0.0
            for prereq, weight in prereq_weights.items():
                w = _safe_float(weight)
                if w == 0.0:
                    continue
                d = self._sums.get((str(user_id), str(prereq)), 0.0)
                if d != 0.0:
                    total += w * d
        return gap * total

    def snapshot(self) -> Dict[str, float]:
        with self._lock:
            return {f"{u}::{c}": v for (u, c), v in self._sums.items()}


# ---------------------------------------------------------------------------
# 3. ChallengeEventTrigger  --  the original "midterm/exam" design. Sparse-spiky
#                                 by construction. Fires only when assessment-
#                                 flagged AND >= K practices since last
#                                 assessment AND mastery_before >= theta.
#                                 Magnitude on trigger = gamma * ΔM_observed.
# ---------------------------------------------------------------------------


@dataclass
class ChallengeEventConfig:
    K_practices: int = 4  # min practices on concept since last assessment
    theta_eligible: float = 0.6  # min mastery_before to be exam-eligible
    gamma: float = 3.0  # amplification of ΔM on triggered interactions

    @classmethod
    def from_env(cls) -> "ChallengeEventConfig":
        return cls(
            K_practices=int(os.environ.get("HCIE_V2_CHALLENGE_K", "4")),
            theta_eligible=float(os.environ.get("HCIE_V2_CHALLENGE_THETA", "0.6")),
            gamma=float(os.environ.get("HCIE_V2_CHALLENGE_GAMMA", "3.0")),
        )


@dataclass
class ChallengeEventOutcome:
    fired: bool
    contribution: float  # gamma * ΔM if fired else 0.0
    practices_since_last_assessment: int
    mastery_before: float
    reason: str  # human-readable trigger / not-trigger explanation


class ChallengeEventTrigger:
    """
    O(1) per-interaction practice counter and trigger evaluator.

    State per (user, concept): an integer practice counter that increments on
    every non-assessment interaction and resets when an assessment fires.
    """

    def __init__(self, config: Optional[ChallengeEventConfig] = None) -> None:
        self._cfg = config or ChallengeEventConfig.from_env()
        self._counter: Dict[Tuple[str, str], int] = {}
        self._lock = RLock()

    @property
    def config(self) -> ChallengeEventConfig:
        return self._cfg

    def evaluate(
        self,
        user_id: str,
        concept_id: str,
        mastery_before: float,
        delta_m: float,
        is_assessment: bool,
    ) -> ChallengeEventOutcome:
        key = (str(user_id), str(concept_id))
        m_before = _safe_float(mastery_before)
        with self._lock:
            practices = self._counter.get(key, 0)
            if not is_assessment:
                self._counter[key] = practices + 1
                return ChallengeEventOutcome(
                    fired=False,
                    contribution=0.0,
                    practices_since_last_assessment=practices + 1,
                    mastery_before=m_before,
                    reason="not_assessment",
                )
            # Assessment-flagged interaction: evaluate triggers.
            eligible_practices = practices >= self._cfg.K_practices
            eligible_mastery = m_before >= self._cfg.theta_eligible
            if not (eligible_practices and eligible_mastery):
                # Assessment fired but learner not eligible -- counter does NOT
                # reset (you have to earn the exam by practicing enough).
                self._counter[key] = practices
                reason_parts = []
                if not eligible_practices:
                    reason_parts.append(
                        f"K_practices<{self._cfg.K_practices} ({practices})"
                    )
                if not eligible_mastery:
                    reason_parts.append(
                        f"mastery<{self._cfg.theta_eligible:.2f} ({m_before:.3f})"
                    )
                return ChallengeEventOutcome(
                    fired=False,
                    contribution=0.0,
                    practices_since_last_assessment=practices,
                    mastery_before=m_before,
                    reason="not_eligible: " + ", ".join(reason_parts),
                )
            # Trigger fires. Reset counter; magnitude = gamma * ΔM.
            self._counter[key] = 0
            contribution = self._cfg.gamma * _safe_float(delta_m)
            return ChallengeEventOutcome(
                fired=True,
                contribution=contribution,
                practices_since_last_assessment=practices,
                mastery_before=m_before,
                reason=(
                    f"fired: practices={practices}>={self._cfg.K_practices}, "
                    f"mastery={m_before:.3f}>={self._cfg.theta_eligible:.2f}, "
                    f"gamma={self._cfg.gamma}"
                ),
            )

    def snapshot(self) -> Dict[str, int]:
        with self._lock:
            return {f"{u}::{c}": v for (u, c), v in self._counter.items()}


# ---------------------------------------------------------------------------
# 4. WelfordCovariance  --  online cross-dim covariance.
#                            Used by ADC live-router for governance and by
#                            tier2_5-evidence for synergy redundancy on V2.
# ---------------------------------------------------------------------------


class WelfordCovariance:
    """O(1) per-update online covariance estimator (Welford, 1962)."""

    __slots__ = ("n", "mean_x", "mean_y", "m2_x", "m2_y", "c_xy")

    def __init__(self) -> None:
        self.n = 0
        self.mean_x = 0.0
        self.mean_y = 0.0
        self.m2_x = 0.0
        self.m2_y = 0.0
        self.c_xy = 0.0

    def update(self, x: float, y: float) -> None:
        x = _safe_float(x)
        y = _safe_float(y)
        self.n += 1
        # Welford (1962) / Chan-Golub-LeVeque (1983): delta with OLD mean, then
        # m2/c update uses delta_old * (value - new_mean). m2_y was previously
        # using (y - new_mean)^2 which biases toward zero.
        dx = x - self.mean_x
        dy = y - self.mean_y
        self.mean_x += dx / self.n
        self.mean_y += dy / self.n
        self.m2_x += dx * (x - self.mean_x)
        self.m2_y += dy * (y - self.mean_y)
        self.c_xy += dx * (y - self.mean_y)

    def correlation(self) -> Optional[float]:
        if self.n < 2:
            return None
        var_x = self.m2_x / (self.n - 1)
        var_y = self.m2_y / (self.n - 1)
        if var_x <= 0 or var_y <= 0:
            return None
        cov = self.c_xy / (self.n - 1)
        return cov / math.sqrt(var_x * var_y)

    def snapshot(self) -> Dict[str, float]:
        return {
            "n": float(self.n),
            "mean_x": self.mean_x,
            "mean_y": self.mean_y,
            "m2_x": self.m2_x,
            "m2_y": self.m2_y,
            "c_xy": self.c_xy,
        }


# ---------------------------------------------------------------------------
# 5. Top-level compute helper.
#    Called from unified_brain.py only when redesign_v2_enabled() is True.
# ---------------------------------------------------------------------------


@dataclass
class V2Signals:
    """Bundle of V2 dim contributions for a single interaction."""

    baseline_difficulty: float = 0.0
    challenge_event: float = 0.0
    population_prior: float = 0.0
    challenge_event_fired: bool = False
    challenge_event_reason: str = ""
    population_prior_n: int = 0
    t_realized_v2: float = 0.0
    state_snapshot: Dict[str, float] = field(default_factory=dict)

    def as_jsonable(self) -> Dict[str, object]:
        return {
            "baseline_difficulty": float(self.baseline_difficulty),
            "challenge_event": float(self.challenge_event),
            "population_prior": float(self.population_prior),
            "challenge_event_fired": bool(self.challenge_event_fired),
            "challenge_event_reason": str(self.challenge_event_reason),
            "population_prior_n": int(self.population_prior_n),
            "t_realized_v2": float(self.t_realized_v2),
            "state_snapshot": dict(self.state_snapshot),
        }


def compute_v2_signals(
    *,
    user_id: str,
    concept_id: str,
    mastery_before: float,
    delta_m: float,
    correct: bool,
    is_assessment: bool,
    legacy_challenge_value: float,
    population_prior: PopulationPriorState,
    prereq_accumulator: PrereqDeltaAccumulator,
    challenge_trigger: ChallengeEventTrigger,
    prereq_weights: Optional[Mapping[str, float]] = None,
) -> V2Signals:
    """
    Single O(1) entry point that updates running state and returns the V2 dim
    bundle. Order of operations matters for replay determinism:

      1. Read-before-write for PrereqDeltaAccumulator (T_realized_v2 uses the
         pre-update prereq state, mirroring V1 'before' semantics).
      2. Read-before-write for PopulationPrior (so cold-start posteriors do
         not include the current observation).
      3. Evaluate Challenge_event trigger (uses pre-update mastery_before).
      4. Apply updates: prereq accumulator gets THIS concept's delta,
         population prior gets THIS observation's correctness.
    """
    pp_mean_before = population_prior.posterior_mean(concept_id)
    pp_n_before = population_prior.n_observations(concept_id)

    t_realized_v2 = 0.0
    if prereq_weights:
        t_realized_v2 = prereq_accumulator.realized_for(
            user_id=user_id,
            target_concept=concept_id,
            prereq_weights=prereq_weights,
            target_mastery_before=mastery_before,
        )

    outcome = challenge_trigger.evaluate(
        user_id=user_id,
        concept_id=concept_id,
        mastery_before=mastery_before,
        delta_m=delta_m,
        is_assessment=is_assessment,
    )

    population_prior.update(concept_id, bool(correct))
    prereq_accumulator.record_delta(user_id, concept_id, delta_m)

    return V2Signals(
        baseline_difficulty=_safe_float(legacy_challenge_value),
        challenge_event=outcome.contribution,
        population_prior=pp_mean_before,
        challenge_event_fired=outcome.fired,
        challenge_event_reason=outcome.reason,
        population_prior_n=pp_n_before,
        t_realized_v2=t_realized_v2,
        state_snapshot={
            "pp_mean_before": pp_mean_before,
            "pp_n_before": float(pp_n_before),
            "challenge_practices": float(outcome.practices_since_last_assessment),
        },
    )


# ---------------------------------------------------------------------------
# 6. Process-level singletons.
#    The V1 hot path keeps its existing learners; V2 state lives here so all
#    interactions on a single worker share population stats.
#    NB: cross-worker state will be reconciled at seal time via snapshots.
# ---------------------------------------------------------------------------


_GLOBAL_POPULATION_PRIOR: Optional[PopulationPriorState] = None
_GLOBAL_PREREQ_ACC: Optional[PrereqDeltaAccumulator] = None
_GLOBAL_CHALLENGE: Optional[ChallengeEventTrigger] = None
_GLOBAL_LOCK = RLock()


def get_population_prior() -> PopulationPriorState:
    global _GLOBAL_POPULATION_PRIOR
    with _GLOBAL_LOCK:
        if _GLOBAL_POPULATION_PRIOR is None:
            _GLOBAL_POPULATION_PRIOR = PopulationPriorState()
        return _GLOBAL_POPULATION_PRIOR


def get_prereq_accumulator() -> PrereqDeltaAccumulator:
    global _GLOBAL_PREREQ_ACC
    with _GLOBAL_LOCK:
        if _GLOBAL_PREREQ_ACC is None:
            _GLOBAL_PREREQ_ACC = PrereqDeltaAccumulator()
        return _GLOBAL_PREREQ_ACC


def get_challenge_trigger() -> ChallengeEventTrigger:
    global _GLOBAL_CHALLENGE
    with _GLOBAL_LOCK:
        if _GLOBAL_CHALLENGE is None:
            _GLOBAL_CHALLENGE = ChallengeEventTrigger()
        return _GLOBAL_CHALLENGE


def reset_singletons_for_replay() -> None:
    """Replay determinism: caller must reset state at the start of each run."""
    global _GLOBAL_POPULATION_PRIOR, _GLOBAL_PREREQ_ACC, _GLOBAL_CHALLENGE
    with _GLOBAL_LOCK:
        _GLOBAL_POPULATION_PRIOR = None
        _GLOBAL_PREREQ_ACC = None
        _GLOBAL_CHALLENGE = None


def all_state_snapshots() -> Dict[str, object]:
    """Replay-deterministic full-state snapshot for sealing manifests."""
    return {
        "population_prior": (
            _GLOBAL_POPULATION_PRIOR.snapshot() if _GLOBAL_POPULATION_PRIOR else {}
        ),
        "prereq_accumulator": (
            _GLOBAL_PREREQ_ACC.snapshot() if _GLOBAL_PREREQ_ACC else {}
        ),
        "challenge_trigger": (
            _GLOBAL_CHALLENGE.snapshot() if _GLOBAL_CHALLENGE else {}
        ),
    }


__all__ = [
    "redesign_v2_enabled",
    "PopulationPriorState",
    "PrereqDeltaAccumulator",
    "ChallengeEventConfig",
    "ChallengeEventTrigger",
    "ChallengeEventOutcome",
    "WelfordCovariance",
    "V2Signals",
    "compute_v2_signals",
    "get_population_prior",
    "get_prereq_accumulator",
    "get_challenge_trigger",
    "reset_singletons_for_replay",
    "all_state_snapshots",
]
