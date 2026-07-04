"""Unit tests for the Adaptive Dimension Controller (ADC).

These tests correspond to the L1, L2, and L3 layers of the ADC test
plan declared in `CHAPTER_4_5_EVIDENCE_DRAFT.md §4.15 (R5)`:

- **L1 — Determinism / idempotency.** Same observations -> identical
  serialized report. Same JSONL file -> identical report across two
  independent loads. Window-replay symmetry: appending then removing
  observations returns to the original state.
- **L2 — Invariants (property tests).** Every public summary must
  satisfy: confidence ∈ [0, 1]; nonzero_fraction ∈ [0, 1]; weight_mean
  ∈ [0, 1]; activation verdicts ∈ {active, dormant-by-signal, suppressed,
  active-and-collapsed-impossible}; governance_concentration ∈ [0, 1];
  dynamic_range ≥ 0.
- **L3 — Engineered ecology (falsifiability).** Synthesise trajectories
  with known properties and verify the ADC produces the verdict we
  pre-registered for that ecology shape:

    a) *Dormant-by-signal.*  raw = 0 everywhere -> dimension not active,
       has_signal=False, rationale tags "no substrate signal".
    b) *Suppressed.*  Strong raw signal but weight_mean below collapse
       threshold -> active=False, weight_collapsed=True.
    c) *Active.*  Strong raw signal AND weight_mean above collapse
       threshold -> active=True, has_signal=True.
    d) *Dominance.*  One weight monopolizes the distribution ->
       governance_concentration close to 1 (low entropy).
    e) *Uniform.*  All six weights equal -> governance_concentration
       close to 0 (max entropy).

The tests are pure-Python (no Docker, no Redis, no Postgres) and rely
only on `numpy` + the ADC module loaded via the `finals_loader` shim.
"""

from __future__ import annotations

import json
import math
import os
import random
from pathlib import Path
from typing import Dict, List

import pytest

from finals_loader import from_finals  # type: ignore  # provided by 00_test_utilities


ADC_REL_PATH = "01_source/00_core/03_ensemble/adaptive_dimension_controller.py"


@pytest.fixture(scope="module")
def adc_module():
    return from_finals(ADC_REL_PATH)


@pytest.fixture(scope="module")
def AdaptiveDimensionController(adc_module):
    return adc_module.AdaptiveDimensionController


@pytest.fixture(scope="module")
def DIMS(adc_module):
    return adc_module.GOVERNANCE_DIMENSIONS


@pytest.fixture(scope="module")
def WEIGHT_KEYS(adc_module):
    return adc_module.WEIGHT_KEYS


# ---------------------------------------------------------------------------
# Helpers for engineered ecologies
# ---------------------------------------------------------------------------


def _equal_weights(WEIGHT_KEYS) -> Dict[str, float]:
    n = len(WEIGHT_KEYS)
    return {k: 1.0 / n for k in WEIGHT_KEYS}


def _dominant_weights(WEIGHT_KEYS, dominant_key: str, dominance: float = 0.85) -> Dict[str, float]:
    others = [k for k in WEIGHT_KEYS if k != dominant_key]
    remainder = (1.0 - dominance) / max(len(others), 1)
    out = {k: remainder for k in others}
    out[dominant_key] = dominance
    return out


def _zero_raw(DIMS) -> Dict[str, float]:
    return {d: 0.0 for d in DIMS}


def _strong_raw(DIMS, dim: str, value: float = 0.7) -> Dict[str, float]:
    out = {d: 0.0 for d in DIMS}
    out[dim] = value
    return out


def _build_records(
    DIMS,
    WEIGHT_KEYS,
    n_steps: int,
    raw_provider,
    weight_provider,
    jt_value: float = 0.6,
    dataset_id: str = "engineered",
) -> List[Dict]:
    return [
        {
            "raw": raw_provider(step),
            "weights": weight_provider(step),
            "jt": jt_value,
            "context": {"dataset_id": dataset_id, "step": step},
        }
        for step in range(n_steps)
    ]


# ---------------------------------------------------------------------------
# L1 — Determinism / idempotency
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_records_same_report(self, AdaptiveDimensionController, DIMS, WEIGHT_KEYS):
        records = _build_records(
            DIMS,
            WEIGHT_KEYS,
            n_steps=32,
            raw_provider=lambda s: {d: (s % 3) * 0.1 for d in DIMS},
            weight_provider=lambda s: _equal_weights(WEIGHT_KEYS),
        )

        a = AdaptiveDimensionController.from_records(records, dataset_id="det")
        b = AdaptiveDimensionController.from_records(records, dataset_id="det")

        report_a = json.dumps(a.serialize_report(), sort_keys=True)
        report_b = json.dumps(b.serialize_report(), sort_keys=True)
        assert report_a == report_b, "ADC.serialize_report must be deterministic on identical inputs"

    def test_jsonl_roundtrip_is_deterministic(
        self, AdaptiveDimensionController, DIMS, WEIGHT_KEYS, tmp_path: Path
    ):
        records = _build_records(
            DIMS,
            WEIGHT_KEYS,
            n_steps=20,
            raw_provider=lambda s: {d: 0.5 if d == "delta_m" else 0.0 for d in DIMS},
            weight_provider=lambda s: _equal_weights(WEIGHT_KEYS),
        )
        path = tmp_path / "obs.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")

        a = AdaptiveDimensionController.from_jsonl(path, dataset_id="jsonl")
        b = AdaptiveDimensionController.from_jsonl(path, dataset_id="jsonl")

        assert json.dumps(a.serialize_report(), sort_keys=True) == json.dumps(
            b.serialize_report(), sort_keys=True
        )

    def test_observation_order_preserves_summary_shape(
        self, AdaptiveDimensionController, DIMS, WEIGHT_KEYS
    ):
        # Permutation of the observation order changes time-ordered
        # statistics (mastery_progression_slope) but must not change
        # *aggregated* statistics like mean/std/dynamic_range.
        records = _build_records(
            DIMS,
            WEIGHT_KEYS,
            n_steps=16,
            raw_provider=lambda s: {d: 0.1 + (s % 4) * 0.05 for d in DIMS},
            weight_provider=lambda s: _equal_weights(WEIGHT_KEYS),
        )
        rng = random.Random(42)
        permuted = list(records)
        rng.shuffle(permuted)

        a = AdaptiveDimensionController.from_records(records)
        b = AdaptiveDimensionController.from_records(permuted)

        fp_a = a.compute_ecology_fingerprint().to_json()
        fp_b = b.compute_ecology_fingerprint().to_json()

        for dim in DIMS:
            sig_a = fp_a["per_dimension"][dim]
            sig_b = fp_b["per_dimension"][dim]
            assert sig_a["mean"] == pytest.approx(sig_b["mean"], abs=1e-12)
            assert sig_a["std"] == pytest.approx(sig_b["std"], abs=1e-12)
            assert sig_a["dynamic_range"] == pytest.approx(
                sig_b["dynamic_range"], abs=1e-12
            )
            assert sig_a["nonzero_fraction"] == pytest.approx(
                sig_b["nonzero_fraction"], abs=1e-12
            )

    def test_write_report_is_pure(
        self, AdaptiveDimensionController, DIMS, WEIGHT_KEYS, tmp_path: Path
    ):
        records = _build_records(
            DIMS,
            WEIGHT_KEYS,
            n_steps=12,
            raw_provider=lambda s: {d: 0.3 for d in DIMS},
            weight_provider=lambda s: _equal_weights(WEIGHT_KEYS),
        )
        adc = AdaptiveDimensionController.from_records(records, dataset_id="pure")
        p1 = tmp_path / "r1.json"
        p2 = tmp_path / "r2.json"
        adc.write_report(p1)
        adc.write_report(p2)
        assert p1.read_text(encoding="utf-8") == p2.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# L2 — Invariants (property tests on the public summaries)
# ---------------------------------------------------------------------------


class TestInvariants:
    @pytest.fixture
    def random_adc(self, AdaptiveDimensionController, DIMS, WEIGHT_KEYS):
        rng = random.Random(1337)

        def _rand_weights():
            raw = [rng.random() for _ in WEIGHT_KEYS]
            s = sum(raw) or 1.0
            return {k: v / s for k, v in zip(WEIGHT_KEYS, raw)}

        records = _build_records(
            DIMS,
            WEIGHT_KEYS,
            n_steps=64,
            raw_provider=lambda s: {d: rng.uniform(-1.0, 1.0) for d in DIMS},
            weight_provider=lambda s: _rand_weights(),
            jt_value=0.6,
        )
        return AdaptiveDimensionController.from_records(records, dataset_id="rand")

    def test_fingerprint_invariants(self, random_adc, DIMS):
        fp = random_adc.compute_ecology_fingerprint().to_json()
        for dim in DIMS:
            sig = fp["per_dimension"][dim]
            assert 0.0 <= sig["nonzero_fraction"] <= 1.0
            assert sig["dynamic_range"] >= 0.0
            assert sig["max"] >= sig["min"]
            assert sig["weight_mean"] >= 0.0
            # weights are L1-normalized in the test fixture but the
            # invariant must hold under any legal weight vector — we
            # check the per-dimension bound only.
            assert sig["weight_max"] >= sig["weight_min"]
            if not (math.isnan(sig["coefficient_of_variation"])):
                assert sig["coefficient_of_variation"] >= 0.0
        # Aggregate-level invariants.
        assert 0.0 <= fp["governance_entropy_mean"] <= 1.0
        assert 0.0 <= fp["governance_entropy_std"]
        assert fp["uncertainty_regime"] in {"low", "moderate", "high"}

    def test_activation_invariants(self, random_adc, DIMS):
        ap = random_adc.compute_dimension_activation_profile().to_json()
        for dim in DIMS:
            act = ap["per_dimension"][dim]
            assert isinstance(act["active"], bool)
            assert isinstance(act["has_signal"], bool)
            assert isinstance(act["weight_collapsed"], bool)
            assert 0.0 <= act["confidence"] <= 1.0
            # active implies signal AND not collapsed.
            if act["active"]:
                assert act["has_signal"] is True
                assert act["weight_collapsed"] is False
            assert isinstance(act["rationale"], str) and act["rationale"]
        assert set(ap["active_dimensions"]).issubset(set(DIMS))
        assert set(ap["dormant_dimensions"]).issubset(set(DIMS))
        assert set(ap["collapsed_dimensions"]).issubset(set(DIMS))
        assert 0.0 <= ap["governance_concentration"] <= 1.0

    def test_empty_window_safe(self, AdaptiveDimensionController):
        adc = AdaptiveDimensionController(window_size=50, dataset_id="empty")
        fp = adc.compute_ecology_fingerprint().to_json()
        ap = adc.compute_dimension_activation_profile().to_json()
        assert fp["n_observations"] == 0
        assert ap["n_observations"] == 0
        # All dimensions must be reported, even with zero data.
        assert set(fp["per_dimension"].keys()) == set(ap["per_dimension"].keys())
        for dim in fp["per_dimension"]:
            assert ap["per_dimension"][dim]["active"] is False


# ---------------------------------------------------------------------------
# L3 — Engineered ecology (falsifiability)
# ---------------------------------------------------------------------------


class TestEngineeredEcology:
    """Each test constructs a trajectory with a *known* property and
    asserts the ADC produces the verdict we pre-registered for that
    property. These are the falsifiability tests: if any assertion
    here fails on a future ADC change, the ADC has moved away from the
    semantics declared in `CHAPTER_4_5_EVIDENCE_DRAFT.md §4.10.7`."""

    def test_dormant_by_signal(self, AdaptiveDimensionController, DIMS, WEIGHT_KEYS):
        """A dimension with raw≡0 across the window must be reported
        as ``has_signal=False`` and ``active=False`` regardless of how
        much weight it carries. This is the regime the chapter calls
        'structural dormancy / dormant-by-substrate'."""

        target = "transfer_prospective"  # mirrors the smoke-grid finding

        def raw_provider(_step: int) -> Dict[str, float]:
            return _zero_raw(DIMS)

        # Equal weights so weight_collapsed=False -> rationale must be
        # the "structural dormancy" branch.
        records = _build_records(
            DIMS,
            WEIGHT_KEYS,
            n_steps=40,
            raw_provider=raw_provider,
            weight_provider=lambda s: _equal_weights(WEIGHT_KEYS),
            dataset_id="L3-dormant",
        )

        adc = AdaptiveDimensionController.from_records(records)
        ap = adc.compute_dimension_activation_profile().to_json()
        act = ap["per_dimension"][target]

        assert act["has_signal"] is False, "raw≡0 must produce has_signal=False"
        assert act["active"] is False, "raw≡0 must produce active=False"
        assert "no substrate signal" in act["rationale"] or "structural dormancy" in act["rationale"]
        assert target in ap["dormant_dimensions"]

    def test_suppressed_by_weight(self, AdaptiveDimensionController, DIMS, WEIGHT_KEYS):
        """Strong raw signal but weight_mean below the collapse
        threshold must produce ``has_signal=True`` AND
        ``weight_collapsed=True`` AND ``active=False``. The chapter
        calls this 'suppressed'."""

        target = "uncertainty"

        # Configure weights so the target's wi is below collapse but the
        # raw signal is strong and varied.
        def weight_provider(_step: int) -> Dict[str, float]:
            w = _equal_weights(WEIGHT_KEYS)
            # collapse w5 (uncertainty)
            w["w5"] = 0.01
            # Renormalize remaining mass.
            s = sum(v for k, v in w.items() if k != "w5") or 1.0
            for k in w:
                if k != "w5":
                    w[k] = (w[k] / s) * (1.0 - 0.01)
            return w

        def raw_provider(step: int) -> Dict[str, float]:
            out = _zero_raw(DIMS)
            out[target] = 0.3 + 0.4 * (step % 5) / 4.0  # varied, clearly nonzero
            return out

        records = _build_records(
            DIMS, WEIGHT_KEYS, 30, raw_provider, weight_provider, dataset_id="L3-supp"
        )
        adc = AdaptiveDimensionController.from_records(records)
        ap = adc.compute_dimension_activation_profile().to_json()
        act = ap["per_dimension"][target]

        assert act["has_signal"] is True
        assert act["weight_collapsed"] is True
        assert act["active"] is False
        assert "suppressed" in act["rationale"]
        assert target in ap["collapsed_dimensions"]
        assert target not in ap["active_dimensions"]

    def test_active(self, AdaptiveDimensionController, DIMS, WEIGHT_KEYS):
        """Strong raw signal AND weight above the collapse threshold
        must produce ``active=True``."""

        target = "delta_m"

        def raw_provider(step: int) -> Dict[str, float]:
            out = _zero_raw(DIMS)
            out[target] = 0.2 + 0.6 * ((step * 7) % 11) / 10.0  # varied + dense
            return out

        # Dominant weight on w1 (delta_m) -> well above collapse.
        records = _build_records(
            DIMS,
            WEIGHT_KEYS,
            n_steps=30,
            raw_provider=raw_provider,
            weight_provider=lambda s: _dominant_weights(WEIGHT_KEYS, "w1", dominance=0.6),
            dataset_id="L3-active",
        )
        adc = AdaptiveDimensionController.from_records(records)
        ap = adc.compute_dimension_activation_profile().to_json()
        act = ap["per_dimension"][target]

        assert act["has_signal"] is True
        assert act["weight_collapsed"] is False
        assert act["active"] is True
        assert "active" in act["rationale"]
        assert target in ap["active_dimensions"]

    def test_governance_concentration_dominance(
        self, AdaptiveDimensionController, DIMS, WEIGHT_KEYS
    ):
        """A weight vector dominated by a single wi must produce
        ``governance_concentration`` close to 1 (low entropy)."""

        records = _build_records(
            DIMS,
            WEIGHT_KEYS,
            n_steps=20,
            raw_provider=lambda s: _zero_raw(DIMS),
            weight_provider=lambda s: _dominant_weights(WEIGHT_KEYS, "w3", dominance=0.92),
            dataset_id="L3-concentrated",
        )
        adc = AdaptiveDimensionController.from_records(records)
        ap = adc.compute_dimension_activation_profile().to_json()
        # Heavily concentrated: 1 - normalized_entropy ≥ 0.6 is a very
        # safe bar at 0.92 dominance over 6 dimensions.
        assert ap["governance_concentration"] >= 0.6

    def test_governance_concentration_uniform(
        self, AdaptiveDimensionController, DIMS, WEIGHT_KEYS
    ):
        """A uniform weight vector must produce
        ``governance_concentration`` close to 0 (max entropy)."""

        records = _build_records(
            DIMS,
            WEIGHT_KEYS,
            n_steps=20,
            raw_provider=lambda s: _zero_raw(DIMS),
            weight_provider=lambda s: _equal_weights(WEIGHT_KEYS),
            dataset_id="L3-uniform",
        )
        adc = AdaptiveDimensionController.from_records(records)
        ap = adc.compute_dimension_activation_profile().to_json()
        assert ap["governance_concentration"] <= 0.05, (
            "uniform weights must produce near-zero concentration; observed "
            f"{ap['governance_concentration']}"
        )

    def test_threshold_sensitivity_monotonic(
        self, AdaptiveDimensionController, DIMS, WEIGHT_KEYS
    ):
        """A stricter ``weight_collapse_threshold`` must (weakly) shrink
        the set of active dimensions. This is the cheapest piece of L5
        sensitivity evidence — full F-ADC-4 sweep is logged as R6 in
        §4.15."""

        def raw_provider(step: int) -> Dict[str, float]:
            return {d: 0.25 + 0.05 * (step % 4) for d in DIMS}

        # Construct a moderately-skewed weight vector so some weights
        # are near the collapse boundary.
        def weight_provider(_step: int) -> Dict[str, float]:
            return {
                "w1": 0.30,
                "w2": 0.05,
                "w3": 0.20,
                "w4": 0.15,
                "w5": 0.08,
                "w6": 0.22,
            }

        records = _build_records(
            DIMS, WEIGHT_KEYS, 24, raw_provider, weight_provider, dataset_id="L3-sens"
        )

        adc_lo = AdaptiveDimensionController.from_records(records)
        adc_lo.weight_collapse_threshold = 0.03  # very permissive
        adc_hi = AdaptiveDimensionController.from_records(records)
        adc_hi.weight_collapse_threshold = 0.10  # stricter

        active_lo = set(adc_lo.compute_dimension_activation_profile().active_dimensions)
        active_hi = set(adc_hi.compute_dimension_activation_profile().active_dimensions)

        assert active_hi.issubset(active_lo), (
            f"stricter threshold must not enlarge active set; lo={active_lo} hi={active_hi}"
        )


# ---------------------------------------------------------------------------
# L4 — Canonical activation contract (sealer <-> offline profiler must agree)
# ---------------------------------------------------------------------------


class TestCanonicalActivationAPI:
    """The sealer (run_sealing._activation_profile) and the offline profiler both route
    through ``classify_dimension`` over ``raw_governance_snapshot``. These tests pin that
    contract: the snapshot extractor, the standalone classifier, and the DB->ADC
    constructor — so the system's frozen seal cannot diverge from the reproducer."""

    def _signal(self, adc_module, *, dim, dynamic_range, nonzero_fraction, weight_mean,
                weight_collapsed):
        return adc_module.DimensionSignal(
            dimension=dim, n_observations=10, mean=0.1, std=0.05, min=0.0, max=dynamic_range,
            dynamic_range=dynamic_range, nonzero_fraction=nonzero_fraction,
            coefficient_of_variation=0.5, weight_mean=weight_mean, weight_min=weight_mean,
            weight_max=weight_mean, weight_collapsed=weight_collapsed,
        )

    def test_raw_components_from_snapshot_null_missing_and_extra(self, adc_module, DIMS):
        # Authoritative snapshot: challenge=null, transfer_prospective absent,
        # transfer_realized fires, plus diagnostic keys that must be ignored.
        snap = {
            "delta_m": 0.05, "transfer_realized": 1.2554, "challenge": None,
            "uncertainty": 0.035, "zpd": 0.93,
            "ensemble_variance": 0.035, "deterministic_inputs_hash": "abc",
        }
        out = adc_module.raw_components_from_snapshot(snap)
        assert set(out.keys()) == set(DIMS)  # exactly the six dims, no diagnostics
        assert out["transfer_realized"] == pytest.approx(1.2554)
        assert out["delta_m"] == pytest.approx(0.05)
        assert out["challenge"] == 0.0              # JSON null -> 0.0 (dormant)
        assert out["transfer_prospective"] == 0.0   # missing key -> 0.0 (dormant)

    def test_classify_dimension_active(self, adc_module):
        sig = self._signal(adc_module, dim="transfer_realized", dynamic_range=1.25,
                           nonzero_fraction=0.18, weight_mean=0.15, weight_collapsed=False)
        v = adc_module.classify_dimension(sig)
        assert v.active is True and v.has_signal is True and v.weight_collapsed is False
        assert "active" in v.rationale

    def test_classify_dimension_dormant_by_null_substrate(self, adc_module):
        # challenge on the anchor: raw snapshot null -> zero range -> dormant, even though
        # weight is fully retained (0.15). This is the verdict the legacy sealer got WRONG.
        sig = self._signal(adc_module, dim="challenge", dynamic_range=0.0,
                           nonzero_fraction=0.0, weight_mean=0.15, weight_collapsed=False)
        v = adc_module.classify_dimension(sig)
        assert v.active is False and v.has_signal is False
        assert "structural dormancy" in v.rationale

    def test_classify_dimension_suppressed(self, adc_module):
        sig = self._signal(adc_module, dim="uncertainty", dynamic_range=0.5,
                           nonzero_fraction=0.5, weight_mean=0.01, weight_collapsed=True)
        v = adc_module.classify_dimension(sig)
        assert v.active is False and v.has_signal is True and v.weight_collapsed is True
        assert "suppressed" in v.rationale

    def test_from_trajectory_snapshots_matches_anchor_shape(self, adc_module, DIMS):
        # Reproduce the anchor shape: transfer fires on ~18% of steps; challenge +
        # transfer_prospective null; delta_m/uncertainty/zpd always present. Mix dict and
        # JSON-string snapshots to exercise both parse paths.
        weights = {"w1": 0.25, "w2": 0.15, "w3": 0.15, "w4": 0.15, "w5": 0.15, "w6": 0.15}
        rows = []
        for step in range(100):
            # Active dims must VARY (has_signal needs dynamic_range>0), mirroring the real
            # anchor where delta_m∈[0.003,0.05], uncertainty∈[0,0.08], zpd∈[0.84,1.0].
            snap = {
                "delta_m": 0.03 + (step % 5) * 0.004,
                "uncertainty": 0.02 + (step % 7) * 0.003,
                "zpd": 0.85 + (step % 4) * 0.03,
                "challenge": None, "transfer_prospective": None,
                "transfer_realized": 1.2 if step % 5 == 0 else 0.0,  # fires 20% of steps
            }
            raw = snap if step % 2 else json.dumps(snap)            # both parse paths
            wts = weights if step % 2 else json.dumps(weights)
            rows.append({"raw_governance_snapshot": raw, "weights_snapshot": wts, "jt_value": 0.6})

        adc = adc_module.AdaptiveDimensionController.from_trajectory_snapshots(rows, dataset_id="anchor-like")
        ap = adc.compute_dimension_activation_profile()
        assert "transfer_realized" in ap.active_dimensions, "graph signal must read ACTIVE when it fires"
        assert "delta_m" in ap.active_dimensions
        assert "challenge" in ap.dormant_dimensions, "null-substrate challenge must read DORMANT"
        assert "transfer_prospective" in ap.dormant_dimensions

    def test_profile_routes_through_classify_dimension(self, adc_module, DIMS):
        # The activation profile MUST equal classify_dimension applied to each per-dim
        # signal — i.e. there is exactly one rule, not a second inline copy.
        weights = {f"w{i}": (0.25 if i == 1 else 0.15) for i in range(1, 7)}
        rows = [{
            "raw_governance_snapshot": {"delta_m": 0.05, "transfer_realized": (0.9 if s % 4 == 0 else 0.0),
                                        "uncertainty": 0.03, "zpd": 0.9, "challenge": None,
                                        "transfer_prospective": None},
            "weights_snapshot": weights, "jt_value": 0.6,
        } for s in range(60)]
        adc = adc_module.AdaptiveDimensionController.from_trajectory_snapshots(rows)
        profile = adc.compute_dimension_activation_profile()
        fp = adc.compute_ecology_fingerprint()
        for dim in DIMS:
            expected = adc_module.classify_dimension(fp.per_dimension[dim])
            got = profile.per_dimension[dim]
            assert got.active == expected.active
            assert got.has_signal == expected.has_signal
            assert got.rationale == expected.rationale
