"""Normalize trajectory signal layer for Tier-2 mathematical identifiability.

Revision ID: 018_normalized_trajectory_signals
Revises: 017_seed_cohort_task_diversity
Create Date: 2026-05-22 12:00:00.000000

This migration completes the 6D JT decomposition in
``experiment_trajectories`` and adds explicit, stable columns for the
governance metrics, weight snapshots, selector evidence, and a
side-car ``raw_governance_snapshot`` for full archaeology.

Design contract (per math_signal_audit.md):
- Decomposition lives in **explicit FLOAT columns**, never inside an
  opaque JSON blob, so SQL analytics / attribution plots / replay
  diffs do not require JSON archaeology.
- Selector evidence is split into the scalar selector + score plus a
  JSONB ``selection_metrics`` for richer top-K data.
- ``raw_governance_snapshot`` is the opt-in JSONB for everything that
  has no stable column yet (forward-compat).

The migration is additive only; no existing column is renamed or
dropped, preserving compatibility with V2 / 013 readers.
"""

from alembic import op
import sqlalchemy as sa


revision = "018_normalized_trajectory_signals"
down_revision = "017_seed_cohort_task_diversity"


_NEW_COLUMNS = [
    # 6D JT decomposition — A3 completion (013 shipped 5/6).
    ("jt_transfer_prospective_contribution", "FLOAT"),
    # JT attribution share per dimension (% of |J_t|).
    ("jt_attribution", "JSONB"),
    # 6D weight snapshot at write time (w1..w6) for replay diffs.
    ("weights_snapshot", "JSONB"),
    # F-031 governance metrics, explicit columns for SQL aggregations.
    ("governance_volatility", "FLOAT"),
    ("governance_exploration_pressure", "FLOAT"),
    ("governance_stability_index", "FLOAT"),
    # Per-interaction learning dynamics for ablation tooling.
    ("policy_multiplier", "FLOAT"),
    ("effective_learning_rate", "FLOAT"),
    ("adaptive_rate", "FLOAT"),
    ("mastery_delta", "FLOAT"),
    # Selector evidence — stable scalar columns + JSONB top-K snapshot.
    ("policy_selector", "TEXT"),
    ("policy_score", "FLOAT"),
    ("candidates_count", "INTEGER"),
    ("selection_metrics", "JSONB"),
    # Side-car for forward-compat raw payload.
    ("raw_governance_snapshot", "JSONB"),
]


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "experiment_trajectories" not in inspector.get_table_names():
        return

    for column, ctype in _NEW_COLUMNS:
        op.execute(
            f"ALTER TABLE experiment_trajectories "
            f"ADD COLUMN IF NOT EXISTS {column} {ctype}"
        )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_experiment_trajectories_policy_selector "
        "ON experiment_trajectories(policy_selector)"
    )


def downgrade():
    op.execute(
        "DROP INDEX IF EXISTS idx_experiment_trajectories_policy_selector"
    )
    for column, _ in reversed(_NEW_COLUMNS):
        op.execute(
            f"ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS {column}"
        )
