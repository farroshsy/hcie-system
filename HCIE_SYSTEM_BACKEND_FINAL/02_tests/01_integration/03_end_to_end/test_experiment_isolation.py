"""Tests for experiment isolation and namespaced user UUIDs."""

import pytest

import pytest
pytest.skip(
    "experiments.* experiment-orchestration package was retired (BACKENDV2-era); this test targets removed code.",
    allow_module_level=True,
)

from experiments.experiment_utils import generate_user_uuid
from experiments.experiment_isolation import ExperimentRunContext, run_namespace


def test_generate_user_uuid_prefix_isolates_users():
    a = generate_user_uuid(0, 42, prefix="run_a")
    b = generate_user_uuid(0, 42, prefix="run_b")
    c = generate_user_uuid(0, 42, prefix="run_a")
    assert a != b
    assert a == c


def test_experiment_run_context_user_ids_unique_per_learner():
    run_id = "phase2_cold_start_real_20260516_120000"
    ctx = ExperimentRunContext(
        experiment_run_id=run_id,
        num_learners=3,
        run_baselines=True,
    )
    ids = ctx.user_ids_for_run()
    assert len(ids) == 3 + 3 * 3  # hci + 3 baselines * 3 learners
    assert len(set(ids)) == len(ids)


def test_run_namespace_stable():
    ns1 = run_namespace("phase2_cold_start_real_20260516_120000")
    ns2 = run_namespace("phase2_cold_start_real_20260516_120000")
    ns3 = run_namespace("other_run")
    assert ns1 == ns2
    assert ns1 != ns3
    assert len(ns1) == 12
