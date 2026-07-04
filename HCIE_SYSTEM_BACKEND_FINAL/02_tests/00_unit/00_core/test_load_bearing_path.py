"""Task 8 — targeted unit tests on the load-bearing decision path.

Covers the modules that actually carry the contribution, in isolation:
  - ContextualBandit  (Thompson sampling + representation selection)  core/07_bandit
  - classify_dimension (the ONE canonical ADC activation verdict)     core/03_ensemble
  - KalmanLearner state read/canonical (the Kalman canonical path)    core/04_learners

These are pure-ish, dependency-light entry points — no DB/Kafka required (the bandit
falls back to memory-only when redis is absent).
"""
import numpy as np
import pytest

from core.bandit.bandit import ContextualBandit
from core.ensemble.adaptive_dimension_controller import classify_dimension, DimensionSignal
from core.learners.kalman_learner import KalmanLearner


# ── ContextualBandit ──────────────────────────────────────────────────────────

def _bandit(seed=42):
    return ContextualBandit(rng_stream=np.random.default_rng(seed))


def test_sample_beta_is_deterministic_under_seeded_stream():
    a, b = _bandit(7), _bandit(7)
    xs = [a.sample_beta(2.0, 5.0) for _ in range(20)]
    ys = [b.sample_beta(2.0, 5.0) for _ in range(20)]
    assert xs == ys  # same seed -> identical Thompson draws


def test_sample_beta_invalid_params_returns_half():
    bnd = _bandit()
    assert bnd.sample_beta(0.0, 5.0) == 0.5
    assert bnd.sample_beta(2.0, -1.0) == 0.5


def test_select_representation_empty_returns_a_default():
    bnd = _bandit()
    out = bnd.select_representation("u1", "c1", [])
    assert isinstance(out, str) and out


def test_select_representation_restricts_to_available():
    bnd = _bandit()
    reps = ["text", "video_question", "mcq"]
    out = bnd.select_representation("u1", "c1", reps, representation_params={})
    assert out in reps


def test_select_representation_prefers_high_posterior_arm():
    bnd = _bandit(123)
    reps = ["good", "bad1", "bad2"]
    params = {"good": (1000.0, 1.0), "bad1": (1.0, 1000.0), "bad2": (1.0, 1000.0)}
    # 'good' samples ~1.0, the others ~0.0 -> Thompson must pick 'good'.
    picks = {bnd.select_representation("u1", "c1", reps, representation_params=params) for _ in range(10)}
    assert picks == {"good"}


def test_compute_orchestration_metrics_empty_ranking():
    bnd = _bandit()
    out = bnd.compute_orchestration_metrics([], "x")
    assert out.get("error") == "empty_ranking"


# ── ADC classify_dimension ────────────────────────────────────────────────────

def _sig(dynamic_range, nonzero_fraction, weight_collapsed, weight_mean=0.2):
    return DimensionSignal(
        dimension="d", n_observations=100, mean=0.1, std=0.05, min=0.0, max=dynamic_range,
        dynamic_range=dynamic_range, nonzero_fraction=nonzero_fraction,
        coefficient_of_variation=0.5, weight_mean=weight_mean, weight_min=0.0,
        weight_max=weight_mean * 2, weight_collapsed=weight_collapsed,
    )


def test_adc_active_when_signal_and_weight_engaged():
    a = classify_dimension(_sig(0.5, 0.5, weight_collapsed=False))
    assert a.active is True and a.has_signal is True and "active" in a.rationale


def test_adc_dormant_when_no_signal_and_collapsed():
    a = classify_dimension(_sig(0.0, 0.0, weight_collapsed=True))
    assert a.active is False and "dormant" in a.rationale


def test_adc_suppressed_when_signal_but_weight_collapsed():
    a = classify_dimension(_sig(0.5, 0.5, weight_collapsed=True))
    assert a.active is False and "suppressed" in a.rationale


def test_adc_structural_dormancy_when_weight_but_no_signal():
    a = classify_dimension(_sig(0.0, 0.0, weight_collapsed=False))
    assert a.active is False and "structural" in a.rationale


def test_adc_confidence_in_unit_interval():
    for dr, nz, col in [(0.5, 0.5, False), (0.0, 0.0, True), (0.5, 1.0, False)]:
        a = classify_dimension(_sig(dr, nz, weight_collapsed=col))
        assert 0.0 <= a.confidence <= 1.0


# ── KalmanLearner (Kalman canonical path) ─────────────────────────────────────

def test_kalman_get_state_default_without_adapter():
    k = KalmanLearner()
    assert k.get_state("u1", "c1") == (0.3, 0.1)


def test_kalman_canonical_reads_learner_specific_fields():
    k = KalmanLearner()
    m, p = k.get_state_from_canonical({"kalman_mastery": 0.72, "kalman_covariance": 0.04})
    assert (round(m, 6), round(p, 6)) == (0.72, 0.04)


def test_kalman_canonical_falls_back_to_shared_mastery():
    k = KalmanLearner()
    m, p = k.get_state_from_canonical({"mastery": 0.6, "uncertainty": 0.2})
    assert (round(m, 6), round(p, 6)) == (0.6, 0.2)


def test_kalman_canonical_handles_non_dict_and_empty():
    k = KalmanLearner()
    assert k.get_state_from_canonical(0.42) == (0.42, 0.1)
    assert k.get_state_from_canonical({}) == (0.3, 0.1)
