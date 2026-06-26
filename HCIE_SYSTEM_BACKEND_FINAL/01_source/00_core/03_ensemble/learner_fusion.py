"""Causal inverse-variance fusion of learner posteriors (HCIE_REDESIGN_V2 causal path).

Why this exists
---------------
V1 (the sealed run-94a3b8ba) fuses three learners by a fixed ~equal average
(`(lyapunov + bayesian + kalman) / 3`). Two facts make that fusion the weakest link:
  * the equal-weight ensemble underperforms Kalman alone (ensemble r=0.3113 < kalman r=0.3322),
  * Lyapunov correlates 0.92 with Bayesian — a near-redundant third vote.

This module replaces the average with **inverse-variance fusion** of the two *grounded,
distinct* learners (Kalman, Bayesian). Inverse-variance weighting is the minimum-variance
linear combination of independent estimators, so the fused posterior variance is no larger
than either input — the principled way to be "not worse than Kalman". Lyapunov is **disclosed
and recorded but excluded from the causal fuse** (it stays a passive redundancy signal), which
is the reopened `ensemble_fusion` decision: causal 2-learner fusion, not the audit-only overlay.

Sealed-safety: this only runs when the caller is on the V2 causal path. With the flag off the
brain keeps its legacy average untouched, so V1 outputs are byte-identical (golden-gated).

The actual weighting is delegated to `enkf_inverse_variance.inverse_variance_fuse`; this module
adds the Beta-posterior variance, the causal-subset policy, a robust fallback, and a typed
result so callers don't re-implement any of it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional, Tuple

from .enkf_inverse_variance import inverse_variance_fuse

# Learners that vote in the causal fuse. Lyapunov is intentionally absent (DISCLOSE, not wired).
CAUSAL_LEARNERS: Tuple[str, ...] = ("kalman", "bayesian")


def v2_causal_fusion_enabled() -> bool:
    """True when the V2 causal fusion should drive canonical mastery.

    Gated by HCIE_REDESIGN_V2_CAUSAL so it is independent of the audit-only HCIE_REDESIGN_V2
    overlay: turning on extra recorded signals must NOT silently change the fusion math.
    """
    return os.environ.get("HCIE_REDESIGN_V2_CAUSAL", "").strip().lower() in ("1", "true", "yes")


def beta_variance(alpha: float, beta: float) -> Optional[float]:
    """Variance of a Beta(alpha, beta) posterior; None if the params are degenerate."""
    s = float(alpha) + float(beta)
    if s <= 0:
        return None
    var = (float(alpha) * float(beta)) / (s * s * (s + 1.0))
    return var if var > 0 else None


@dataclass
class FusedEstimate:
    """Result of fusing learner posteriors into one canonical mastery."""

    mastery: float
    variance: float
    weights: Dict[str, float] = field(default_factory=dict)  # normalized, causal learners only
    method: str = "inverse_variance"  # or "equal_average_fallback"
    excluded: Tuple[str, ...] = ()    # learners present but kept out of the causal fuse


class LearnerFusion:
    """Fuse already-computed learner masteries+variances by inverse variance.

    Stateless and pure: callers pass the masteries/variances they already hold (from canonical
    state) and get back a single estimate. It does NOT update the learners — that stays the
    caller's job — so it is safe to drop in at the point where V1 computes its average.
    """

    def __init__(self, causal_learners: Tuple[str, ...] = CAUSAL_LEARNERS):
        self._causal = tuple(causal_learners)

    def fuse(
        self,
        masteries: Mapping[str, Optional[float]],
        variances: Mapping[str, Optional[float]],
    ) -> FusedEstimate:
        """Fuse the causal-subset learners; fall back to an equal average if variances are unusable.

        masteries / variances are keyed by learner id (kalman, bayesian, lyapunov, ...). Only the
        causal subset is fused; non-causal keys present in `masteries` are reported in `excluded`.
        """
        causal_m = {k: masteries.get(k) for k in self._causal if masteries.get(k) is not None}
        causal_v = {k: variances.get(k) for k in self._causal}
        excluded = tuple(k for k in masteries if k not in self._causal and masteries.get(k) is not None)

        fused, weights = inverse_variance_fuse(causal_m, causal_v)
        if fused is not None and weights:
            inv_total = sum(1.0 / variances[k] for k in weights if variances.get(k))
            fused_var = 1.0 / inv_total if inv_total > 0 else 0.0
            return FusedEstimate(
                mastery=_clip01(fused),
                variance=fused_var,
                weights=weights,
                method="inverse_variance",
                excluded=excluded,
            )

        # Fallback: no usable variances -> plain average of available causal masteries (never worse
        # than V1's behaviour, and keeps the path total so a degenerate cold start still returns).
        vals = [m for m in causal_m.values() if m is not None]
        if not vals:
            return FusedEstimate(mastery=0.3, variance=0.1, weights={}, method="equal_average_fallback",
                                 excluded=excluded)
        avg = sum(vals) / len(vals)
        n = len(vals)
        return FusedEstimate(
            mastery=_clip01(avg),
            variance=0.1,
            weights={k: 1.0 / n for k in causal_m},
            method="equal_average_fallback",
            excluded=excluded,
        )


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))
