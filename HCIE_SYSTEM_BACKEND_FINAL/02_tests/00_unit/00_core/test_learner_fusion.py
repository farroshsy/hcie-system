"""Unit tests for the V2-causal inverse-variance learner fusion.

Pure math — no infra. Locks the science contract: variance-weighted fusion, Lyapunov excluded
from the causal fuse (DISCLOSE-not-wire), fused variance no larger than either input, and a safe
fallback. These are the properties the reopened ensemble_fusion decision claims.
"""
import os
import importlib.util
import pathlib

import pytest

# Import by file path so the test runs on host too (no projection resolver needed). The module's
# only dependency is its sibling enkf_inverse_variance, which we load first under the same package.
_ENS = pathlib.Path(__file__).resolve().parents[3] / "01_source" / "00_core" / "03_ensemble"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"_lf_{name}", _ENS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def lf():
    # learner_fusion does `from .enkf_inverse_variance import inverse_variance_fuse`; satisfy that
    # relative import by registering a tiny package namespace.
    import sys, types
    pkg = types.ModuleType("_lfpkg")
    pkg.__path__ = [str(_ENS)]
    sys.modules["_lfpkg"] = pkg
    enkf = _load("enkf_inverse_variance")
    sys.modules["_lfpkg.enkf_inverse_variance"] = enkf
    spec = importlib.util.spec_from_file_location("_lfpkg.learner_fusion", _ENS / "learner_fusion.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_lfpkg.learner_fusion"] = mod   # register before exec so @dataclass can resolve cls.__module__
    spec.loader.exec_module(mod)
    return mod


def test_beta_variance_known_value(lf):
    # Beta(1,1) is uniform: variance = 1/12.
    assert lf.beta_variance(1.0, 1.0) == pytest.approx(1.0 / 12.0)
    # degenerate
    assert lf.beta_variance(0.0, 0.0) is None


def test_inverse_variance_pulls_toward_confident_learner(lf):
    f = lf.LearnerFusion()
    # kalman is far more confident (tiny variance) than bayesian -> fused should sit near kalman.
    est = f.fuse(
        masteries={"kalman": 0.8, "bayesian": 0.4},
        variances={"kalman": 0.001, "bayesian": 0.1},
    )
    assert est.method == "inverse_variance"
    assert 0.75 < est.mastery <= 0.8          # dominated by the confident learner
    assert est.weights["kalman"] > est.weights["bayesian"]
    assert est.weights["kalman"] + est.weights["bayesian"] == pytest.approx(1.0)


def test_fused_variance_not_larger_than_either_input(lf):
    f = lf.LearnerFusion()
    est = f.fuse(
        masteries={"kalman": 0.6, "bayesian": 0.5},
        variances={"kalman": 0.04, "bayesian": 0.09},
    )
    assert est.variance <= 0.04 + 1e-12       # <= min input variance: the whole point
    assert est.variance > 0


def test_lyapunov_excluded_from_causal_fuse(lf):
    f = lf.LearnerFusion()
    est = f.fuse(
        masteries={"kalman": 0.7, "bayesian": 0.5, "lyapunov": 0.99},
        variances={"kalman": 0.01, "bayesian": 0.01, "lyapunov": 0.01},
    )
    assert "lyapunov" in est.excluded
    assert "lyapunov" not in est.weights
    # lyapunov's extreme value must not drag the fused mastery up
    assert est.mastery < 0.75


def test_fallback_equal_average_when_no_usable_variance(lf):
    f = lf.LearnerFusion()
    est = f.fuse(
        masteries={"kalman": 0.8, "bayesian": 0.4},
        variances={"kalman": None, "bayesian": 0.0},
    )
    assert est.method == "equal_average_fallback"
    assert est.mastery == pytest.approx(0.6)


def test_mastery_clipped_to_unit_interval(lf):
    f = lf.LearnerFusion()
    est = f.fuse(masteries={"kalman": 1.5, "bayesian": 1.2},
                 variances={"kalman": 0.01, "bayesian": 0.02})
    assert 0.0 <= est.mastery <= 1.0


def test_env_gate_off_by_default(lf, monkeypatch):
    monkeypatch.delenv("HCIE_REDESIGN_V2_CAUSAL", raising=False)
    assert lf.v2_causal_fusion_enabled() is False
    monkeypatch.setenv("HCIE_REDESIGN_V2_CAUSAL", "1")
    assert lf.v2_causal_fusion_enabled() is True
