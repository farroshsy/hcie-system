"""K-12 transfer engine: real DAG loads and transfer amounts are bounded and positive.

Converted from a print-only docker smoke script into assertion-based tests against the
real TransferLearningEngine (static K-12 DAG fallback applies when no dependency_store).
"""
from core.learning.transfer_learning_engine import TransferLearningEngine


def test_k12_dag_loads():
    te = TransferLearningEngine()
    # The real K-12 DAG loads via the static fallback; the engine warns if it sees < 10.
    assert len(te.dependencies) >= 10
    assert "k2_computing_systems_devices" in te.dependencies
    deps = te.dependencies["k2_computing_systems_devices"]
    assert len(deps) == 2
    assert {d.target_concept for d in deps} == {
        "k5_computing_systems_devices",
        "k2_computing_systems_hardware_software",
    }


def test_k12_transfer_amounts_bounded_and_positive():
    te = TransferLearningEngine()
    mastery_change = 0.05
    transfer1 = te.calculate_transfer_amount(
        source_concept="k2_computing_systems_devices",
        target_concept="k5_computing_systems_devices",
        mastery_change=mastery_change, confidence=0.8, learning_gain=mastery_change,
    )
    assert transfer1 > 0.0
    assert transfer1 >= te.min_transfer_threshold
    assert transfer1 <= 0.5 * abs(mastery_change)  # capped relative to mastery change

    transfer2 = te.calculate_transfer_amount(
        source_concept="k5_computing_systems_devices",
        target_concept="k8_computing_systems_devices",
        mastery_change=0.08, confidence=0.85, learning_gain=0.08,
    )
    assert transfer2 > 0.0
    assert transfer2 >= te.min_transfer_threshold

    assert transfer1 + transfer2 > 0.0


def test_k12_chain_reaches_k12():
    te = TransferLearningEngine()
    assert "k8_computing_systems_devices" in te.dependencies
    assert any(
        d.target_concept == "k12_computing_systems_devices"
        for d in te.dependencies["k8_computing_systems_devices"]
    )
