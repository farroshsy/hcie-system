"""Unified Schema - Policy Infrastructure Tables

Revision ID: 005_unified_policy
Revises: 004_unified_transfer
Create Date: 2026-05-12 00:00:00.000000

This migration creates the policy infrastructure:
- policy_snapshots: Immutable policy snapshots for replay validity

Design Principles:
- VARCHAR for snapshot_id and policy_version (consistent with application usage)
- JSONB for flexible policy configuration storage
- Immutable snapshots (frozen) to guarantee replay safety
- Schema versioning for future compatibility
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005_unified_policy'
down_revision = '004_unified_transfer'


def upgrade():
    # Create policy_snapshots table
    op.create_table(
        'policy_snapshots',
        sa.Column('snapshot_id', sa.String(255), nullable=False, primary_key=True),
        sa.Column('policy_version', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('experiment_id', sa.String(255), nullable=True),
        
        # Strategy snapshots (JSON)
        sa.Column('pacing_strategy', postgresql.JSONB(), nullable=False),
        sa.Column('remediation_strategy', postgresql.JSONB(), nullable=False),
        sa.Column('difficulty_strategy', postgresql.JSONB(), nullable=False),
        sa.Column('ux_transformer', postgresql.JSONB(), nullable=False),
        
        # Policy configuration (JSON)
        sa.Column('adaptation_parameters', postgresql.JSONB(), nullable=False),
        sa.Column('thresholds', postgresql.JSONB(), nullable=False),
        
        # Snapshot metadata
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('schema_version', sa.String(50), nullable=False, server_default='1.0.0'),
        sa.Column('snapshot_hash', sa.String(64), nullable=True, unique=True),
        
        # Timestamps
        sa.Column('created_at_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Indexes
        sa.Index('idx_policy_snapshots_policy_version', 'policy_version'),
        sa.Index('idx_policy_snapshots_experiment_id', 'experiment_id'),
        sa.Index('idx_policy_snapshots_status', 'status')
    )


def downgrade():
    op.drop_index('idx_policy_snapshots_status', table_name='policy_snapshots')
    op.drop_index('idx_policy_snapshots_experiment_id', table_name='policy_snapshots')
    op.drop_index('idx_policy_snapshots_policy_version', table_name='policy_snapshots')
    op.drop_table('policy_snapshots')
