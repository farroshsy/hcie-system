"""Unified Schema - Exploration Events Table

Revision ID: 011_exploration_events
Revises: 010_trajectory_events
Create Date: 2026-05-14 00:00:00.000000

This migration creates the exploration_events table for exploration behavior analysis:
- Track action selection distribution over time
- Track exploration vs exploitation ratio
- Track JT volatility and exploration pressure correlation
- Track action coverage (unique actions selected)
- Track exploration decay over time

Design Principles:
- Time-series optimized with timestamp indexes
- Supports exploration behavior analysis
- Enables correlation analysis between JT and exploration
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '011_exploration_events'
down_revision = '010_trajectory_events'


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "exploration_events" in inspector.get_table_names():
        return

    # Create exploration_events table
    op.create_table(
        'exploration_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('event_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('interaction_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Action selection
        sa.Column('action_selected', sa.String(255), nullable=True),
        sa.Column('action_distribution', postgresql.JSONB(), nullable=True),  # probability distribution
        
        # Exploration metrics
        sa.Column('exploration_pressure', sa.Float(), nullable=True),
        sa.Column('exploration_ratio', sa.Float(), nullable=True),  # exploration vs exploitation
        sa.Column('action_coverage', sa.Integer(), nullable=True),  # unique actions selected so far
        
        # JT correlation
        sa.Column('jt_value', sa.Float(), nullable=True),
        sa.Column('jt_volatility', sa.Float(), nullable=True),
        sa.Column('exploration_multiplier', sa.Float(), nullable=True),  # from JT volatility
        
        # Metadata
        sa.Column('experiment_run_id', sa.String(255), nullable=True),
        
        # Indexes for time-series queries
        sa.Index('idx_exploration_events_timestamp', 'timestamp'),
        sa.Index('idx_exploration_events_user', 'user_id', 'timestamp'),
        sa.Index('idx_exploration_events_run', 'experiment_run_id', 'timestamp')
    )


def downgrade():
    op.drop_index('idx_exploration_events_run', table_name='exploration_events')
    op.drop_index('idx_exploration_events_user', table_name='exploration_events')
    op.drop_index('idx_exploration_events_timestamp', table_name='exploration_events')
    op.drop_table('exploration_events')
