"""Unified Schema - Advanced Instrumentation Tables

Revision ID: 008_unified_instrumentation
Revises: 007_unified_experiments
Create Date: 2026-05-12 00:00:00.000000

This migration creates advanced instrumentation tables:
- exploration_events: Exploration behavior instrumentation
- transfer_events: Transfer propagation measurement

Design Principles:
- VARCHAR for user_id and event_id (consistent with application usage)
- JSONB for flexible signal storage
- Proper indexes for analysis queries
- Separation from transfer_learning_events (different purpose)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '008_unified_instrumentation'
down_revision = '007_unified_experiments'


def upgrade():
    # Create exploration_events table
    op.create_table(
        'exploration_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('interaction_number', sa.Integer(), nullable=False),
        
        # Action selection
        sa.Column('action_selected', sa.String(255), nullable=True),
        sa.Column('action_distribution', postgresql.JSONB(), nullable=True),
        
        # Exploration metrics
        sa.Column('exploration_pressure', sa.Float(), nullable=True),
        sa.Column('exploration_ratio', sa.Float(), nullable=True),
        sa.Column('action_coverage', sa.Integer(), nullable=True),
        
        # JT correlation
        sa.Column('jt_value', sa.Float(), nullable=True),
        sa.Column('jt_volatility', sa.Float(), nullable=True),
        sa.Column('exploration_multiplier', sa.Float(), nullable=True),
        
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Indexes
        sa.Index('idx_exploration_events_user', 'user_id'),
        sa.Index('idx_exploration_events_interaction', 'interaction_number')
    )
    
    # Create transfer_events table (separate from transfer_learning_events)
    op.create_table(
        'transfer_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('target_concept', sa.String(255), nullable=False),
        
        # Transfer sources
        sa.Column('source_concepts', postgresql.JSONB(), nullable=True),
        sa.Column('transfer_amounts', postgresql.JSONB(), nullable=True),
        sa.Column('total_transfer', sa.Float(), nullable=True),
        
        # Efficiency
        sa.Column('total_gain', sa.Float(), nullable=True),
        sa.Column('transfer_efficiency', sa.Float(), nullable=True),
        
        # DAG edge utilization
        sa.Column('dag_edges_used', postgresql.JSONB(), nullable=True),
        sa.Column('edge_weights', postgresql.JSONB(), nullable=True),
        
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Indexes
        sa.Index('idx_transfer_events_instr_user', 'user_id'),
        sa.Index('idx_transfer_events_instr_target', 'target_concept')
    )


def downgrade():
    op.drop_index('idx_transfer_events_instr_target', table_name='transfer_events')
    op.drop_index('idx_transfer_events_instr_user', table_name='transfer_events')
    op.drop_table('transfer_events')
    
    op.drop_index('idx_exploration_events_interaction', table_name='exploration_events')
    op.drop_index('idx_exploration_events_user', table_name='exploration_events')
    op.drop_table('exploration_events')
