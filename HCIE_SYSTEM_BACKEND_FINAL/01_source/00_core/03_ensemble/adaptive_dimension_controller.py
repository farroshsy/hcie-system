"""Adaptive Dimension Controller (ADC) — observational governance instrument.

This module introduces ``AdaptiveDimensionController``, an observational
companion to ``ConstitutionalWeights`` / ``JTAttributedEnsemble`` whose
*sole* responsibility is to characterize **which governance dimensions
are conditionally active under the observed interaction ecology**.

POSITIONING
-----------

This is **not** a runtime controller. It does not adjust weights, mask
dimensions, modify ensemble composition, or alter any model behaviour.
It does not import the runtime brain. It records observations and emits
**interpretive reports** that feed:

  1. Per-dataset ecology fingerprints (paper Figure F-ADC-1)
  2. Per-dataset dimension activation profiles (paper Figure F-ADC-2)
  3. Governance entropy trajectories (paper Figure F-ADC-3)
  4. The §4.x "Conditional Governance Activation under Ecology" narrative

SCIENTIFIC FRAMING
------------------

The 6D JT governance was designed for a multi-ecology substrate
(cross-context transfer, prospective utility, ZPD alignment). External
KT replays (ASSISTments, EdNet, CSEDM, Junyi) provide signal on a
**subset** of those dimensions — most notably they emit no cross-context
transfer events and limited intervention-induced state shifts.

A naive evaluation would let the transfer- and Lyapunov-driven weights
collapse toward zero under those substrates and then report HCIE's
unfortunate AUC. The ADC reframes that finding: rather than treating
collapsed weights as a *defect* of the algorithm, we treat them as a
**measurable property of the ecology**. The contribution is then:

    "Under ecology E, governance dimensions D_active(E) are
     identified as causally informative; the remaining dimensions
     are dormant not by design choice but by absence of substrate
     signal."

That is interpretable, falsifiable, and dataset-agnostic.

USAGE
-----

Streaming::

    adc = AdaptiveDimensionController(window_size=200)
    adc.observe(
        raw_components={"delta_m": ..., "transfer_realized": ..., ...},
        normalized_components={...},
        weights={"w1": ..., ..., "w6": ...},
        jt_value=...,
        outcome=...,
        context={"dataset_id": "assistments_2009_skill", "step": 17},
    )
    fp = adc.compute_ecology_fingerprint()
    ap = adc.compute_dimension_activation_profile()
    rpt = adc.serialize_report()

Batch / offline::

    adc = AdaptiveDimensionController.from_records(jsonl_path)
    rpt = adc.serialize_report()

The controller is intentionally state-light: it remembers raw values and
recomputes summaries on demand. Reports are JSON-serializable.
"""

from __future__ import annotations

import json
import math
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np


# The six canonical governance dimensions in the order used by
# ConstitutionalWeights.weights ({w1..w6}).
GOVERNANCE_DIMENSIONS: Tuple[str, ...] = (
    "delta_m",
    "transfer_realized",
    "transfer_prospective",
    "challenge",
    "uncertainty",
    "zpd",
)

WEIGHT_KEYS: Tuple[str, ...] = ("w1", "w2", "w3", "w4", "w5", "w6")

# Public canonical dimension -> constitutional-weight-key map. The runtime records
# weights as {w1..w6} (weights_snapshot); this is the single place that says which
# weight governs which governance dimension.
DIMENSION_TO_WEIGHT_KEY: Dict[str, str] = dict(zip(GOVERNANCE_DIMENSIONS, WEIGHT_KEYS))
_DIM_TO_WEIGHT = DIMENSION_TO_WEIGHT_KEY  # backwards-compatible internal alias


def raw_components_from_snapshot(snapshot: Mapping[str, Any]) -> Dict[str, float]:
    """Extract the six governance dimensions from a ``raw_governance_snapshot``.

    ``raw_governance_snapshot`` is the immutable per-step raw governance vector the
    brain records (keys: delta_m, transfer_realized, transfer_prospective, challenge,
    uncertainty, zpd, plus diagnostics). It is the **authoritative** ADC input — not
    the downstream ``jt_*_contribution`` columns (which fold in weight + normalization
    and so report signal even where the raw substrate is null). A missing key or a
    JSON ``null`` becomes ``0.0`` — i.e. "no substrate signal on this step", which is
    exactly the dormant interpretation we want for never-populated dimensions.
    """
    out: Dict[str, float] = {}
    for dim in GOVERNANCE_DIMENSIONS:
        val = snapshot.get(dim) if snapshot else None
        try:
            out[dim] = float(val) if val is not None else 0.0
        except (TypeError, ValueError):
            out[dim] = 0.0
    return out


@dataclass
class DimensionSignal:
    """Per-dimension signal characterization on the observed window."""

    dimension: str
    n_observations: int
    mean: float
    std: float
    min: float
    max: float
    dynamic_range: float           # max - min
    nonzero_fraction: float        # fraction with |raw| > eps
    coefficient_of_variation: float  # std / |mean|, NaN-safe
    weight_mean: float             # mean of the corresponding wi over window
    weight_min: float
    weight_max: float
    weight_collapsed: bool         # weight_mean below collapse threshold

    @property
    def has_signal(self) -> bool:
        # A dimension "has signal" when it both varies (dynamic range >
        # 0) and is observed in a non-trivial fraction of steps. We
        # intentionally do not check the weight here — that's the
        # *system's* response to the signal, not the signal itself.
        return self.dynamic_range > 1e-6 and self.nonzero_fraction > 0.05


@dataclass
class DimensionActivation:
    """Per-dimension activation verdict + confidence.

    ``active`` is the observational verdict: does this dimension carry
    enough signal AND attract enough governance weight that it is
    causally active in the observed ecology? ``confidence`` is in [0, 1]
    and combines signal density and weight magnitude.
    """

    dimension: str
    has_signal: bool
    weight_collapsed: bool
    active: bool
    confidence: float
    rationale: str  # human-readable explanation for paper / debug


# Confidence weighting: how much of the activation confidence comes from "the signal
# exists" vs. "the system gave it weight". Kept at module scope so every caller
# (streaming controller, sealer, offline profiler) classifies identically.
DEFAULT_SIGNAL_WEIGHT = 0.6
DEFAULT_WEIGHT_WEIGHT = 0.4


def classify_dimension(
    signal: DimensionSignal,
    signal_weight: float = DEFAULT_SIGNAL_WEIGHT,
    weight_weight: float = DEFAULT_WEIGHT_WEIGHT,
) -> DimensionActivation:
    """The single canonical activation verdict for one dimension.

    ``active`` iff the substrate carries signal (``has_signal``) AND governance weight
    has not collapsed. A dormant-by-design dimension (e.g. ``transfer_prospective`` in
    Phase A, or ``challenge`` where the raw snapshot never populates it) shows up as
    ``has_signal=False`` and is correctly excluded — that is the desired interpretation,
    not a bug. This is the ONE rule; the sealer, the streaming controller, and the
    offline L4 profiler all route through it so their verdicts cannot diverge.
    """
    has_signal = signal.has_signal
    collapsed = signal.weight_collapsed
    # Confidence: convex combination of normalized signal density and normalized
    # weight magnitude. Equal weights would each cap at 1/6 ≈ 0.167, so rescale by 6.
    signal_score = min(signal.nonzero_fraction * 2.0, 1.0)  # 0.5 nonzero → fully present
    weight_score = float(np.clip(signal.weight_mean * 6.0, 0.0, 1.0))
    confidence = float(signal_weight * signal_score + weight_weight * weight_score)
    active = has_signal and not collapsed
    if not has_signal and collapsed:
        rationale = "dormant: substrate provides no signal and governance weight has collapsed"
    elif not has_signal and not collapsed:
        rationale = "structural dormancy: weight retained but no substrate signal observed"
    elif has_signal and collapsed:
        rationale = "suppressed: substrate carries signal but governance weight collapsed"
    else:
        rationale = "active: substrate carries signal and governance weight is engaged"
    return DimensionActivation(
        dimension=signal.dimension,
        has_signal=has_signal,
        weight_collapsed=collapsed,
        active=active,
        confidence=confidence,
        rationale=rationale,
    )


@dataclass
class EcologyFingerprint:
    """Per-dataset (or per-window) ecology fingerprint."""

    dataset_id: Optional[str]
    n_observations: int
    governance_entropy_mean: float    # H(w) averaged over window
    governance_entropy_std: float
    jt_mean: float
    jt_std: float
    outcome_correctness: Optional[float]  # mean outcome if observed
    per_dimension: Dict[str, DimensionSignal]
    transfer_density: float           # fraction of steps with transfer_realized > eps
    uncertainty_regime: str           # "low" | "moderate" | "high"
    mastery_progression_slope: float  # OLS slope of delta_m over step index

    def to_json(self) -> Dict[str, Any]:
        out = asdict(self)
        out["per_dimension"] = {k: asdict(v) for k, v in self.per_dimension.items()}
        return out


@dataclass
class ActivationProfile:
    """Per-dataset dimension activation profile."""

    dataset_id: Optional[str]
    n_observations: int
    per_dimension: Dict[str, DimensionActivation]
    active_dimensions: List[str]
    dormant_dimensions: List[str]
    collapsed_dimensions: List[str]
    governance_concentration: float  # 1 - normalized entropy in [0,1]

    def to_json(self) -> Dict[str, Any]:
        out = asdict(self)
        out["per_dimension"] = {k: asdict(v) for k, v in self.per_dimension.items()}
        return out


@dataclass
class _Observation:
    raw: Dict[str, float]
    normalized: Dict[str, float]
    weights: Dict[str, float]
    jt_value: float
    outcome: Optional[float]
    context: Dict[str, Any] = field(default_factory=dict)


class AdaptiveDimensionController:
    """Observational governance instrument. See module docstring."""

    # The collapse threshold is the mean weight below which a dimension
    # is considered to have lost governance influence. 0.05 is a
    # deliberately conservative bar — six dimensions with weights summing
    # to 1 would average 0.167, and the constitutional adapt() bounds
    # already clip weights to [0, 1].
    DEFAULT_WEIGHT_COLLAPSE_THRESHOLD = 0.05

    # Confidence weighting: how much of the activation confidence comes
    # from "the signal exists" vs. "the system gave it weight".
    DEFAULT_SIGNAL_WEIGHT = 0.6
    DEFAULT_WEIGHT_WEIGHT = 0.4

    def __init__(
        self,
        window_size: int = 500,
        weight_collapse_threshold: float = DEFAULT_WEIGHT_COLLAPSE_THRESHOLD,
        nonzero_epsilon: float = 1e-6,
        dataset_id: Optional[str] = None,
    ) -> None:
        self.window_size = max(int(window_size), 10)
        self.weight_collapse_threshold = float(weight_collapse_threshold)
        self.nonzero_epsilon = float(nonzero_epsilon)
        self.dataset_id = dataset_id

        self._observations: "deque[_Observation]" = deque(maxlen=self.window_size)

    # ------------------------------------------------------------------
    # Streaming API
    # ------------------------------------------------------------------

    def observe(
        self,
        raw_components: Mapping[str, float],
        weights: Mapping[str, float],
        jt_value: float,
        normalized_components: Optional[Mapping[str, float]] = None,
        outcome: Optional[float] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Record one step. All inputs are stored as floats; missing
        components default to 0.0 and missing weights default to 0.0."""

        raw = {dim: float(raw_components.get(dim, 0.0)) for dim in GOVERNANCE_DIMENSIONS}
        norm = {
            dim: float((normalized_components or {}).get(dim, 0.0))
            for dim in GOVERNANCE_DIMENSIONS
        }
        wts = {wk: float(weights.get(wk, 0.0)) for wk in WEIGHT_KEYS}
        ctx = dict(context or {})
        if self.dataset_id is not None and "dataset_id" not in ctx:
            ctx["dataset_id"] = self.dataset_id

        self._observations.append(
            _Observation(
                raw=raw,
                normalized=norm,
                weights=wts,
                jt_value=float(jt_value),
                outcome=None if outcome is None else float(outcome),
                context=ctx,
            )
        )

    # ------------------------------------------------------------------
    # Batch / offline API
    # ------------------------------------------------------------------

    @classmethod
    def from_records(
        cls,
        records: Iterable[Mapping[str, Any]],
        window_size: Optional[int] = None,
        dataset_id: Optional[str] = None,
    ) -> "AdaptiveDimensionController":
        """Build a controller from an iterable of dict-like records.

        Each record may contain keys:
          - ``raw``: mapping of dimension → float
          - ``normalized``: mapping of dimension → float (optional)
          - ``weights``: mapping of {w1..w6} → float
          - ``jt``: float
          - ``outcome``: float (optional)
          - ``context``: mapping (optional)
        """

        records_list = list(records)
        ws = window_size or max(len(records_list), 10)
        adc = cls(window_size=ws, dataset_id=dataset_id)
        for rec in records_list:
            adc.observe(
                raw_components=rec.get("raw") or {},
                normalized_components=rec.get("normalized"),
                weights=rec.get("weights") or {},
                jt_value=float(rec.get("jt", 0.0)),
                outcome=rec.get("outcome"),
                context=rec.get("context"),
            )
        return adc

    @classmethod
    def from_jsonl(
        cls,
        path: str | Path,
        window_size: Optional[int] = None,
        dataset_id: Optional[str] = None,
    ) -> "AdaptiveDimensionController":
        """Build a controller from a JSONL file of observation records."""

        path = Path(path)
        records: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return cls.from_records(
            records,
            window_size=window_size,
            dataset_id=dataset_id,
        )

    @classmethod
    def from_trajectory_snapshots(
        cls,
        rows: Iterable[Mapping[str, Any]],
        window_size: Optional[int] = None,
        dataset_id: Optional[str] = None,
    ) -> "AdaptiveDimensionController":
        """Build a controller from ``experiment_trajectories`` rows using the
        AUTHORITATIVE ``raw_governance_snapshot`` + ``weights_snapshot``.

        This is the canonical DB -> ADC path; the sealer and the offline L4 profiler
        both go through it, so neither can drift onto a different input column. Each row
        needs ``raw_governance_snapshot`` (dict or JSON str), ``weights_snapshot``
        (dict or JSON str of {w1..w6}), and ``jt_value``. Missing/invalid -> 0.0.
        """

        def _as_dict(v: Any) -> Dict[str, Any]:
            if isinstance(v, Mapping):
                return dict(v)
            if isinstance(v, str):
                try:
                    parsed = json.loads(v)
                    return parsed if isinstance(parsed, dict) else {}
                except (json.JSONDecodeError, ValueError):
                    return {}
            return {}

        rows_list = list(rows)
        ws = window_size or max(len(rows_list), 10)
        adc = cls(window_size=ws, dataset_id=dataset_id)
        for row in rows_list:
            snap = _as_dict(row.get("raw_governance_snapshot"))
            wts = _as_dict(row.get("weights_snapshot"))
            try:
                jt = float(row.get("jt_value") or 0.0)
            except (TypeError, ValueError):
                jt = 0.0
            adc.observe(
                raw_components=raw_components_from_snapshot(snap),
                weights={wk: float(wts.get(wk, 0.0) or 0.0) for wk in WEIGHT_KEYS},
                jt_value=jt,
            )
        return adc

    # ------------------------------------------------------------------
    # Summaries
    # ------------------------------------------------------------------

    @property
    def n_observations(self) -> int:
        return len(self._observations)

    def _raw_series(self, dimension: str) -> np.ndarray:
        return np.asarray([o.raw.get(dimension, 0.0) for o in self._observations], dtype=float)

    def _weight_series(self, dimension: str) -> np.ndarray:
        wk = _DIM_TO_WEIGHT[dimension]
        return np.asarray([o.weights.get(wk, 0.0) for o in self._observations], dtype=float)

    def _jt_series(self) -> np.ndarray:
        return np.asarray([o.jt_value for o in self._observations], dtype=float)

    def _outcome_series(self) -> Optional[np.ndarray]:
        outs = [o.outcome for o in self._observations if o.outcome is not None]
        if not outs:
            return None
        return np.asarray(outs, dtype=float)

    def _governance_entropy_series(self) -> np.ndarray:
        # Shannon entropy of the weight distribution per step, in bits,
        # normalized by log2(6) so it lives in [0, 1]. We treat negative
        # or NaN weights as 0 for safety; in practice they should not
        # occur because enforce_bounds() clips and renormalizes.
        ents: List[float] = []
        log2_six = math.log2(len(WEIGHT_KEYS))
        for o in self._observations:
            w = np.asarray([max(o.weights.get(k, 0.0), 0.0) for k in WEIGHT_KEYS], dtype=float)
            s = w.sum()
            if s <= 0 or not np.isfinite(s):
                ents.append(0.0)
                continue
            p = w / s
            # Drop zero entries to avoid 0 * log(0); 0*log(0) := 0.
            p_nz = p[p > 0]
            h = float(-(p_nz * np.log2(p_nz)).sum() / log2_six) if p_nz.size else 0.0
            ents.append(h)
        return np.asarray(ents, dtype=float)

    def _per_dimension_signal(self, dimension: str) -> DimensionSignal:
        raw = self._raw_series(dimension)
        w = self._weight_series(dimension)
        n = int(raw.size)
        if n == 0:
            return DimensionSignal(
                dimension=dimension,
                n_observations=0,
                mean=0.0,
                std=0.0,
                min=0.0,
                max=0.0,
                dynamic_range=0.0,
                nonzero_fraction=0.0,
                coefficient_of_variation=float("nan"),
                weight_mean=0.0,
                weight_min=0.0,
                weight_max=0.0,
                weight_collapsed=True,
            )
        mean = float(raw.mean())
        std = float(raw.std(ddof=0))
        lo, hi = float(raw.min()), float(raw.max())
        nonzero_fraction = float(np.mean(np.abs(raw) > self.nonzero_epsilon))
        cv = float(std / abs(mean)) if abs(mean) > 1e-9 else float("nan")
        wmean = float(w.mean())
        return DimensionSignal(
            dimension=dimension,
            n_observations=n,
            mean=mean,
            std=std,
            min=lo,
            max=hi,
            dynamic_range=hi - lo,
            nonzero_fraction=nonzero_fraction,
            coefficient_of_variation=cv,
            weight_mean=wmean,
            weight_min=float(w.min()),
            weight_max=float(w.max()),
            weight_collapsed=wmean < self.weight_collapse_threshold,
        )

    def compute_ecology_fingerprint(self) -> EcologyFingerprint:
        per_dim = {dim: self._per_dimension_signal(dim) for dim in GOVERNANCE_DIMENSIONS}
        jt = self._jt_series()
        ents = self._governance_entropy_series()
        outcomes = self._outcome_series()

        transfer_density = per_dim["transfer_realized"].nonzero_fraction

        u_mean = per_dim["uncertainty"].mean
        if u_mean < 0.25:
            regime = "low"
        elif u_mean < 0.65:
            regime = "moderate"
        else:
            regime = "high"

        # OLS slope of delta_m over step index.
        dm = self._raw_series("delta_m")
        if dm.size >= 2:
            x = np.arange(dm.size, dtype=float)
            xm, ym = x.mean(), dm.mean()
            denom = ((x - xm) ** 2).sum()
            slope = float(((x - xm) * (dm - ym)).sum() / denom) if denom > 0 else 0.0
        else:
            slope = 0.0

        return EcologyFingerprint(
            dataset_id=self.dataset_id,
            n_observations=self.n_observations,
            governance_entropy_mean=float(ents.mean()) if ents.size else 0.0,
            governance_entropy_std=float(ents.std(ddof=0)) if ents.size else 0.0,
            jt_mean=float(jt.mean()) if jt.size else 0.0,
            jt_std=float(jt.std(ddof=0)) if jt.size else 0.0,
            outcome_correctness=float(outcomes.mean()) if outcomes is not None else None,
            per_dimension=per_dim,
            transfer_density=transfer_density,
            uncertainty_regime=regime,
            mastery_progression_slope=slope,
        )

    def compute_dimension_activation_profile(self) -> ActivationProfile:
        per_dim_signal = {dim: self._per_dimension_signal(dim) for dim in GOVERNANCE_DIMENSIONS}
        # One canonical verdict per dimension — see module-level classify_dimension.
        activations: Dict[str, DimensionActivation] = {
            dim: classify_dimension(sig, self.DEFAULT_SIGNAL_WEIGHT, self.DEFAULT_WEIGHT_WEIGHT)
            for dim, sig in per_dim_signal.items()
        }

        active = [d for d, a in activations.items() if a.active]
        dormant = [d for d, a in activations.items() if not a.has_signal]
        collapsed = [d for d, a in activations.items() if a.weight_collapsed]

        ent_mean = float(self._governance_entropy_series().mean()) if self.n_observations else 0.0
        concentration = float(np.clip(1.0 - ent_mean, 0.0, 1.0))

        return ActivationProfile(
            dataset_id=self.dataset_id,
            n_observations=self.n_observations,
            per_dimension=activations,
            active_dimensions=active,
            dormant_dimensions=dormant,
            collapsed_dimensions=collapsed,
            governance_concentration=concentration,
        )

    # ------------------------------------------------------------------
    # Report serialization
    # ------------------------------------------------------------------

    def serialize_report(self) -> Dict[str, Any]:
        fp = self.compute_ecology_fingerprint()
        ap = self.compute_dimension_activation_profile()
        return {
            "schema_version": "adc-1.0",
            "controller": {
                "window_size": self.window_size,
                "weight_collapse_threshold": self.weight_collapse_threshold,
                "nonzero_epsilon": self.nonzero_epsilon,
                "dataset_id": self.dataset_id,
                "n_observations": self.n_observations,
            },
            "ecology_fingerprint": fp.to_json(),
            "activation_profile": ap.to_json(),
        }

    def write_report(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(self.serialize_report(), fh, indent=2, sort_keys=True)
        return path

    # ------------------------------------------------------------------
    # Sequence views — useful for plotting trajectories in the paper
    # ------------------------------------------------------------------

    def weight_trajectory(self) -> Dict[str, List[float]]:
        return {
            wk: [o.weights.get(wk, 0.0) for o in self._observations]
            for wk in WEIGHT_KEYS
        }

    def raw_trajectory(self) -> Dict[str, List[float]]:
        return {
            dim: [o.raw.get(dim, 0.0) for o in self._observations]
            for dim in GOVERNANCE_DIMENSIONS
        }

    def governance_entropy_trajectory(self) -> List[float]:
        return self._governance_entropy_series().tolist()

    def jt_trajectory(self) -> List[float]:
        return self._jt_series().tolist()


__all__ = [
    "GOVERNANCE_DIMENSIONS",
    "WEIGHT_KEYS",
    "DIMENSION_TO_WEIGHT_KEY",
    "raw_components_from_snapshot",
    "classify_dimension",
    "DimensionSignal",
    "DimensionActivation",
    "EcologyFingerprint",
    "ActivationProfile",
    "AdaptiveDimensionController",
]
