"""F-024: correctness must bind from interaction_data correct | correctness keys."""

import importlib.util
from pathlib import Path

# Load trajectory_recorder directly (avoids root package __init__ → app import during pytest)
_TR_PATH = (
    Path(__file__).resolve().parents[1]
    / "infrastructure"
    / "experiment"
    / "trajectory_recorder.py"
)
_spec = importlib.util.spec_from_file_location("trajectory_recorder_f024", _TR_PATH)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
TrajectoryRecorder = _mod.TrajectoryRecorder
extract_correctness = _mod.extract_correctness


class _FakeDb:
    def __init__(self):
        self.rows = []

    def insert(self, table, record):
        self.rows.append(record)


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


def test_record_interaction_persists_correct_key():
    db = _FakeDb()
    recorder = TrajectoryRecorder(db)
    recorder.record_interaction(
        experiment_run_id="run_f024",
        user_id="u1",
        concept="c1",
        interaction_id="i1",
        event_id="e1",
        interaction_number=1,
        state_before={"mastery": 0.3},
        state_after={"mastery": 0.35},
        interaction_data={"correct": 1, "response_time": 12.0, "difficulty": 0.5},
    )
    assert len(db.rows) == 1
    assert db.rows[0]["correctness"] is True


def test_record_interaction_persists_correctness_key():
    db = _FakeDb()
    recorder = TrajectoryRecorder(db)
    recorder.record_interaction(
        experiment_run_id="run_f024",
        user_id="u1",
        concept="c1",
        interaction_id="i2",
        event_id="e2",
        interaction_number=2,
        state_before={"mastery": 0.3},
        state_after={"mastery": 0.32},
        interaction_data={"correctness": False, "response_time": 8.0},
    )
    assert db.rows[0]["correctness"] is False


def test_record_trajectory_forwards_interaction_data():
    db = _FakeDb()
    recorder = TrajectoryRecorder(db)
    recorder.record_trajectory(
        experiment_run_id="run_f024",
        user_id="u1",
        concept="c1",
        interaction_id="i3",
        event_id="e3",
        state_before={"mastery": 0.3},
        state_after={"mastery": 0.4},
        interaction_data={"correct": 0},
    )
    assert db.rows[0]["correctness"] is False


if __name__ == "__main__":
    test_extract_correctness_from_correct_int()
    test_extract_correctness_from_correctness_bool()
    test_extract_correctness_prefers_correctness_key()
    test_extract_correctness_missing()
    test_record_interaction_persists_correct_key()
    test_record_interaction_persists_correctness_key()
    test_record_trajectory_forwards_interaction_data()
    print("All F-024 tests passed")
