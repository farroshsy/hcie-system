"""Unit tests for the core `interaction_keys` helper.

Covers the byte-identity-extracted helper at
`01_source/00_core/02_state/interaction_keys.py`. The helper is pure and
load-safe through the `finals_loader`.
"""

from __future__ import annotations

import pytest

from finals_loader import from_finals


@pytest.fixture(scope="module")
def keys():
    return from_finals("01_source/00_core/02_state/interaction_keys.py")


class TestInteractionIsCorrect:
    def test_returns_default_when_interaction_is_none(self, keys):
        assert keys.interaction_is_correct(None) is False
        assert keys.interaction_is_correct(None, default=True) is True

    def test_returns_default_when_interaction_is_empty(self, keys):
        assert keys.interaction_is_correct({}) is False
        assert keys.interaction_is_correct({}, default=True) is True

    def test_reads_correct_field(self, keys):
        assert keys.interaction_is_correct({"correct": True}) is True
        assert keys.interaction_is_correct({"correct": False}) is False

    def test_reads_correctness_field_when_correct_missing(self, keys):
        assert keys.interaction_is_correct({"correctness": True}) is True
        assert keys.interaction_is_correct({"correctness": False}) is False

    def test_correct_overrides_correctness(self, keys):
        # ``correct`` is checked first, so a True there wins even if
        # ``correctness`` disagrees.
        assert keys.interaction_is_correct({"correct": True, "correctness": False}) is True

    def test_coerces_truthy_values(self, keys):
        assert keys.interaction_is_correct({"correct": 1}) is True
        assert keys.interaction_is_correct({"correct": 0}) is False
        assert keys.interaction_is_correct({"correctness": "yes"}) is True


class TestNormalizeInteractionForBrain:
    def test_propagates_correct_to_correctness(self, keys):
        out = keys.normalize_interaction_for_brain({"correct": True})
        assert out["correct"] is True
        assert out["correctness"] is True

    def test_propagates_correctness_to_correct(self, keys):
        out = keys.normalize_interaction_for_brain({"correctness": False})
        assert out["correct"] is False
        assert out["correctness"] is False

    def test_preserves_other_fields(self, keys):
        src = {"user_id": "u1", "concept": "c1", "correct": True}
        out = keys.normalize_interaction_for_brain(src)
        assert out["user_id"] == "u1"
        assert out["concept"] == "c1"

    def test_does_not_mutate_input(self, keys):
        src = {"correct": True}
        _ = keys.normalize_interaction_for_brain(src)
        assert "correctness" not in src

    def test_neither_field_set_passes_through(self, keys):
        out = keys.normalize_interaction_for_brain({"foo": "bar"})
        assert out == {"foo": "bar"}
