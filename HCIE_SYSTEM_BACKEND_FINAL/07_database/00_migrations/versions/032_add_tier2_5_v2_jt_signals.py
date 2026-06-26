"""Add Tier 2.5 V2 JT signal columns to experiment trajectories.

Revision ID: 032_add_tier2_5_v2_jt_signals
Revises: 031_seed_learning_materials
Create Date: 2026-06-02 00:00:00.000000

These columns persist the feature-flagged HCIE_REDESIGN_V2 side branch:
BaselineDifficulty, Challenge_event, PopulationPrior, target-aware
T_realized_v2, and V2 trigger/debug metadata. They are nullable so V1 sealed
rows remain valid and directly comparable.
"""

from alembic import op


revision = "032_add_tier2_5_v2_jt_signals"
down_revision = "031_seed_learning_materials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE experiment_trajectories
        ADD COLUMN IF NOT EXISTS jt_baseline_difficulty_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_challenge_event_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_population_prior_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_t_realized_v2_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_v2_active BOOLEAN,
        ADD COLUMN IF NOT EXISTS jt_v2_state_snapshot JSONB,
        ADD COLUMN IF NOT EXISTS jt_v2_challenge_event_fired BOOLEAN,
        ADD COLUMN IF NOT EXISTS jt_v2_challenge_event_reason TEXT
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_v2_challenge_event_reason")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_v2_challenge_event_fired")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_v2_state_snapshot")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_v2_active")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_t_realized_v2_contribution")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_population_prior_contribution")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_challenge_event_contribution")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_baseline_difficulty_contribution")
