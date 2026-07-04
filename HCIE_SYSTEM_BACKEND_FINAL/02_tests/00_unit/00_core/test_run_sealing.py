"""B13 — unit tests for run_sealing: seal idempotency, content-hash derivation, manifest fields.

No live DB. A FakeStore returns canned rows keyed by SQL fragment, so we test the Python contract
(idempotency, manifest shape, signal_ratio = std/mean, ADC classification, RunSealedError) without
Postgres. run_sealing.py is loaded directly (clean module-level imports) to avoid the app package chain.
"""
import importlib.util
from pathlib import Path

import pytest

_RS_PATH = (
    Path(__file__).resolve().parents[3]
    / "01_source" / "01_application" / "00_api" / "00_v3" / "experiments" / "run_sealing.py"
)
_spec = importlib.util.spec_from_file_location("run_sealing_b13", _RS_PATH)
assert _spec and _spec.loader
rs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rs)


class FakeStore:
    """Routes execute_read by SQL fragment; records writes."""

    def __init__(self, sealed_row=None, agg=None):
        self._sealed_row = sealed_row
        self._agg = agg or {"n": 3, "mean": 0.0, "std": 0.0, "content_hash": "deadbeef"}
        self.writes = []

    def execute_read(self, sql, params=None, fetch_one=False):
        s = " ".join(sql.split())
        if "string_agg" in s:                 # _compute_manifest aggregate
            return dict(self._agg)
        if "raw_governance_snapshot" in s:    # _activation_profile scan -> benign (n=0)
            return {"n": 0}
        if "FROM sealed_runs" in s:           # is_sealed / seal_run existing / return
            return self._sealed_row
        return None

    def execute_write(self, sql, params=None):
        self.writes.append((sql, params))


def test_is_sealed_true_and_false():
    assert rs.is_sealed(FakeStore(sealed_row={"seal_id": "seal-x"}), "run1") is True
    assert rs.is_sealed(FakeStore(sealed_row=None), "run1") is False


def test_compute_manifest_derives_hash_counts_and_ratio():
    store = FakeStore(agg={"n": 5, "mean": 0.02, "std": 0.01, "content_hash": "abc123"})
    m = rs._compute_manifest(store, "run1")
    assert m["as_of_row_count"] == 5
    assert m["content_hash"] == "abc123"            # content hash passes through from the SQL md5
    fs = m["frozen_stats"]
    assert fs["n"] == 5
    assert fs["signal_ratio"] == pytest.approx(0.01 / 0.02)   # std/mean, NOT mean/std
    assert fs["adc_class"] in ("ACTIVE", "DORMANT")
    assert "code_provenance" in fs                  # G7: provenance stamped into the seal


def test_adc_class_active_requires_floor_and_ratio():
    # mean above floor AND ratio >= threshold -> ACTIVE
    active = rs._compute_manifest(FakeStore(agg={"n": 9, "mean": 0.5, "std": 0.5, "content_hash": "h"}), "r")
    assert active["frozen_stats"]["adc_class"] == "ACTIVE"
    # mean below the alpha floor -> DORMANT regardless of ratio
    dormant = rs._compute_manifest(FakeStore(agg={"n": 9, "mean": 0.0001, "std": 0.0001, "content_hash": "h"}), "r")
    assert dormant["frozen_stats"]["adc_class"] == "DORMANT"


def test_seal_run_is_idempotent():
    existing = {"seal_id": "seal-existing", "experiment_run_id": "run1", "content_hash": "abc"}
    store = FakeStore(sealed_row=existing)
    out = rs.seal_run(store, "run1")
    assert out == existing
    assert store.writes == []        # already sealed -> no INSERT (idempotent)


def test_run_sealed_error_carries_handoff_fields():
    e = rs.RunSealedError("run1", "seal-1", "run1-cont")
    assert e.run_id == "run1"
    assert e.seal_id == "seal-1"
    assert e.continue_with == "run1-cont"
    assert "sealed" in str(e)
