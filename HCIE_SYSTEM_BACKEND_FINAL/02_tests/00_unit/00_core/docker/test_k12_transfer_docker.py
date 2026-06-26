"""K-12 transfer engine: process_mastery_update returns well-formed transfers over the real DAG.

Converted from a print-only docker smoke script. Asserts structural/contract facts that hold
regardless of exact transfer magnitudes (which depend on accumulated shared-skill mastery).
"""
from core.learning.transfer_learning_engine import TransferLearningEngine


def test_dag_and_transfer_amount_contract():
    te = TransferLearningEngine()
    assert isinstance(te.dependencies, dict)
    assert len(te.dependencies) >= 10
    for c in (
        "k2_computing_systems_devices",
        "k5_computing_systems_devices",
        "k8_computing_systems_devices",
    ):
        assert c in te.dependencies
    amount = te.calculate_transfer_amount(
        source_concept="k2_computing_systems_devices",
        target_concept="k5_computing_systems_devices",
        mastery_change=0.05, confidence=0.8, learning_gain=0.05,
    )
    assert isinstance(amount, float)
    assert 0.0 <= amount <= 0.5 * 0.05  # capped relative to mastery change


def test_process_mastery_update_returns_wellformed():
    te = TransferLearningEngine()
    transfers, events = te.process_mastery_update(
        user_id="test_user", concept="k2_computing_systems_devices",
        mastery_before=0.30, mastery_after=0.35, confidence=0.8, learning_gain=0.05,
    )
    assert isinstance(transfers, dict)
    assert isinstance(events, list)
    # Any emitted transfer is keyed "source→target" and meets the apply threshold.
    for key, amount in transfers.items():
        assert "→" in key
        assert amount >= te.min_transfer_threshold
