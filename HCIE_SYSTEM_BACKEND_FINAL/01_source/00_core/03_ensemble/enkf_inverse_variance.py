"""
Inverse-variance (EnKF-style) mastery fusion — feature-flagged side branch.

Enabled when HCIE_ENKF_FUSION=1. Default off; production uses JTAttributedEnsemble
weighted sum. Trial path for Tier-3 evidence only.
"""

from __future__ import annotations

import os
from typing import Dict, Optional, Tuple


def enkf_fusion_enabled() -> bool:
    return os.environ.get("HCIE_ENKF_FUSION", "").strip().lower() in ("1", "true", "yes")


def inverse_variance_fuse(
    masteries: Dict[str, Optional[float]],
    variances: Dict[str, Optional[float]],
) -> Tuple[Optional[float], Dict[str, float]]:
    """
    Fuse learner posteriors by inverse-variance weights.

    Args:
        masteries: keys lyapunov, bayesian, kalman (optional global_ability)
        variances: same keys; missing/zero variance → skip that learner

    Returns:
        (fused_mastery, normalized_weights)
    """
    num = 0.0
    den = 0.0
    weights: Dict[str, float] = {}
    for key, m in masteries.items():
        if m is None:
            continue
        v = variances.get(key)
        if v is None or v <= 1e-12:
            continue
        w = 1.0 / float(v)
        weights[key] = w
        num += w * float(m)
        den += w
    if den <= 0:
        return None, {}
    norm = {k: w / den for k, w in weights.items()}
    return num / den, norm
