"""Unified Schema - Transfer Events Table

Revision ID: 012_transfer_events
Revises: 011_exploration_events
Create Date: 2026-05-14 00:00:00.000000

This migration creates the transfer_events table for transfer propagation measurement:
- Track transfer from source → target concepts
- Measure transfer efficiency (transfer_amount / total_gain)
- Track DAG edge utilization
- Measure cross-concept learning gain
- Compare with vs without transfer (ablation)

Design Principles:
- Time-series optimized with timestamp indexes
- Supports transfer propagation analysis
- Enables DAG edge utilization tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '012_transfer_events'
down_revision = '011_exploration_events'


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "transfer_events" in inspector.get_table_names():
        return

    # Create transfer_events table
    op.create_table(
        'transfer_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('event_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('target_concept', sa.String(255), nullable=False),
        sa.Column('interaction_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Transfer sources
        sa.Column('source_concepts', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('transfer_amounts', postgresql.JSONB(), nullable=True),
        sa.Column('total_transfer', sa.Float(), nullable=True),
        
        # Efficiency
        sa.Column('total_gain', sa.Float(), nullable=True),
        sa.Column('transfer_efficiency', sa.Float(), nullable=True),  # total_transfer / total_gain
        
        # DAG edge utilization
        sa.Column('dag_edges_used', postgresql.JSONB(), nullable=True),  # List of [source, target] tuples
        sa.Column('edge_weights', postgresql.JSONB(), nullable=True),  # Dict of edge tuples to weights
        
        # Metadata
        sa.Column('experiment_run_id', sa.String(255), nullable=True),
        
        # Indexes for time-series queries
        sa.Index('idx_transfer_events_timestamp', 'timestamp'),
        sa.Index('idx_transfer_events_user', 'user_id', 'timestamp'),
        sa.Index('idx_transfer_events_target', 'target_concept', 'timestamp'),
        sa.Index('idx_transfer_events_run', 'experiment_run_id', 'timestamp')
    )


def downgrade():
    op.drop_index('idx_transfer_events_run', table_name='transfer_events')
    op.drop_index('idx_transfer_events_target', table_name='transfer_events')
    op.drop_index('idx_transfer_events_user', table_name='transfer_events')
    op.drop_index('idx_transfer_events_timestamp', table_name='transfer_events')
    op.drop_table('transfer_events')
