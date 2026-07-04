"""Phase A Observability Recovery - Add Phase A columns to experiment_trajectories

Revision ID: 013_phase_a_observability
Revises: 012_transfer_events
Create Date: 2026-05-15 00:00:00.000000

This migration adds Phase A observability recovery columns to the experiment_trajectories table:
- A1: Raw estimator states BEFORE aggregation (lyapunov, bayesian, kalman)
- A2: Ensemble attribution state (weights, attribution_scores, softmax_inputs, normalized_weight_vector)
- A3: JT decomposition (ΔM, transfer, challenge, uncertainty, ZPD contributions, unclamped/clamped JT)
- A4: Exploration governance state (CV window, regime, uncertainty_weight, volatility, selected_arm, candidate_scores)

Design Principles:
- Enables evidence-driven recovery by persisting raw estimator dynamics
- Separates raw estimator states from aggregated canonical state
- Provides full JT component decomposition for semantic validation
- Captures exploration governance for auditability
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '013_phase_a_observability'
down_revision = '010_seed_k12_tasks'


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "experiment_trajectories" not in inspector.get_table_names():
        return

    # Add Phase A: Ensemble attribution state (A2)
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS ensemble_weights JSONB")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS attribution_scores JSONB")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS softmax_inputs JSONB")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS normalized_weight_vector JSONB")

    # Add Phase A: JT decomposition (A3)
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS jt_delta_m_contribution FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS jt_transfer_contribution FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS jt_challenge_contribution FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS jt_uncertainty_contribution FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS jt_zpd_contribution FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS jt_unclamped FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS jt_clamped FLOAT")

    # Add Phase A: Exploration governance state (A4)
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS cv_window FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS exploration_regime TEXT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS uncertainty_weight FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS volatility_scaling_factor FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS selected_arm TEXT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS candidate_arm_scores JSONB")

    # Add Phase A: Raw estimator states BEFORE aggregation (A1)
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS raw_lyapunov_mastery_before FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS raw_bayesian_alpha_before FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS raw_bayesian_beta_before FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS raw_kalman_mastery_before FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS raw_kalman_covariance_before FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS raw_lyapunov_mastery_after FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS raw_bayesian_alpha_after FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS raw_bayesian_beta_after FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS raw_kalman_mastery_after FLOAT")
    op.execute("ALTER TABLE experiment_trajectories ADD COLUMN IF NOT EXISTS raw_kalman_covariance_after FLOAT")


def downgrade():
    # Remove Phase A columns in reverse order of addition
    # A1: Raw estimator states
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS raw_kalman_covariance_after")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS raw_kalman_mastery_after")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS raw_bayesian_beta_after")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS raw_bayesian_alpha_after")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS raw_lyapunov_mastery_after")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS raw_kalman_covariance_before")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS raw_kalman_mastery_before")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS raw_bayesian_beta_before")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS raw_bayesian_alpha_before")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS raw_lyapunov_mastery_before")

    # A4: Exploration governance state
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS candidate_arm_scores")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS selected_arm")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS volatility_scaling_factor")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS uncertainty_weight")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS exploration_regime")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS cv_window")

    # A3: JT decomposition
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_clamped")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_unclamped")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_zpd_contribution")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_uncertainty_contribution")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_challenge_contribution")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_transfer_contribution")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS jt_delta_m_contribution")

    # A2: Ensemble attribution state
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS normalized_weight_vector")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS softmax_inputs")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS attribution_scores")
    op.execute("ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS ensemble_weights")
