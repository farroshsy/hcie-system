"""Unified Schema - Trajectory Events Table (Time-Series)

Revision ID: 010_trajectory_events
Revises: 009_deterministic_runtime
Create Date: 2026-05-14 00:00:00.000000

This migration creates the trajectory_events table for time-series governance data:
- Stores temporal evolution of governance signals (JT, learner contributions, mastery delta)
- Time-indexed for temporal analysis
- Separate from trajectory_records (which stores per-interaction snapshots)
- Optimized for time-series queries

Design Principles:
- Time-series optimized with timestamp indexes
- Stores governance trajectory evolution over time
- Supports temporal analysis and trend detection
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '010_trajectory_events'
down_revision = '009_deterministic_runtime'


def upgrade():
    # Create trajectory_events table (time-series data)
    op.create_table(
        'trajectory_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('event_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('concept', sa.String(255), nullable=False),
        sa.Column('interaction_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # JT governance trajectory
        sa.Column('jt_value', sa.Float(), nullable=True),
        sa.Column('jt_weights', postgresql.JSONB(), nullable=True),  # w1, w2, w3, w4, w5
        sa.Column('jt_components', postgresql.JSONB(), nullable=True),  # ΔM, T, C, U, Z
        
        # Learner contribution evolution
        sa.Column('lyapunov_weight', sa.Float(), nullable=True),
        sa.Column('bayesian_weight', sa.Float(), nullable=True),
        sa.Column('kalman_weight', sa.Float(), nullable=True),
        sa.Column('learner_contributions', postgresql.JSONB(), nullable=True),
        
        # State evolution
        sa.Column('mastery_delta', sa.Float(), nullable=True),
        sa.Column('uncertainty_delta', sa.Float(), nullable=True),
        sa.Column('zpd_delta', sa.Float(), nullable=True),
        
        # Transfer propagation
        sa.Column('transfer_sources', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('transfer_amounts', postgresql.JSONB(), nullable=True),
        sa.Column('transfer_efficiency', sa.Float(), nullable=True),
        
        # Exploration
        sa.Column('exploration_pressure', sa.Float(), nullable=True),
        sa.Column('action_selected', sa.String(255), nullable=True),
        sa.Column('action_distribution', postgresql.JSONB(), nullable=True),
        
        # Metadata
        sa.Column('experiment_run_id', sa.String(255), nullable=True),
        
        # Indexes for time-series queries
        sa.Index('idx_trajectory_events_timestamp', 'timestamp'),
        sa.Index('idx_trajectory_events_user', 'user_id', 'timestamp'),
        sa.Index('idx_trajectory_events_concept', 'concept', 'timestamp'),
        sa.Index('idx_trajectory_events_run', 'experiment_run_id', 'timestamp')
    )


def downgrade():
    op.drop_index('idx_trajectory_events_run', table_name='trajectory_events')
    op.drop_index('idx_trajectory_events_concept', table_name='trajectory_events')
    op.drop_index('idx_trajectory_events_user', table_name='trajectory_events')
    op.drop_index('idx_trajectory_events_timestamp', table_name='trajectory_events')
    op.drop_table('trajectory_events')
