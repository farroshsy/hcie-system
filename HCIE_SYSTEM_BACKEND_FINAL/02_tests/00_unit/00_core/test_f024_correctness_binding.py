"""F-024: correctness must bind from interaction_data `correct` | `correctness` keys.

Pins the pure binding rule via `extract_correctness`. The persistence path (`record_interaction`)
is integration-tested — it needs a real store (`.query` + `execute_write`), not a unit fake — so it
is not exercised here. trajectory_recorder is loaded directly (clean module-level imports) to avoid
the app package chain during pytest.
"""
import importlib.util
from pathlib import Path

_TR_PATH = (
    Path(__file__).resolve().parents[3]
    / "01_source" / "02_infrastructure" / "02_experiment" / "trajectory_recorder.py"
)
_spec = importlib.util.spec_from_file_location("trajectory_recorder_f024", _TR_PATH)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
extract_correctness = _mod.extract_correctness


def test_extract_correctness_from_correct_int():
    assert extract_correctness({"correct": 1}) is True
    assert extract_correctness({"correct": 0}) is False


def test_extract_correctness_from_correctness_bool():
    assert extract_correctness({"correctness": True}) is True
    assert extract_correctness({"correctness": False}) is False


def test_extract_correctness_prefers_correctness_key():
    assert extract_correctness({"correctness": True, "correct": 0}) is True


def test_extract_correctness_missing():
    assert extract_correctness({}) is None
    assert extract_correctness(None) is None
