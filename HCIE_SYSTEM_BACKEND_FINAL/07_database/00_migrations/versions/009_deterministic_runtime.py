"""
Deterministic Runtime Migration

Revision ID: 009_deterministic_runtime
Revises: 008_unified_instrumentation
Create Date: 2026-05-13 00:00:00.000000

Adds deterministic metadata columns to outbox_event_envelopes table for
automatic deterministic replay from Kafka event logs.

Deterministic metadata:
- deterministic_mode: Whether event was generated in deterministic mode
- deterministic_seed: Seed used for deterministic generation

This enables:
- Automatic deterministic replay from Kafka
- Event log-based reconstruction
- Same seed → same trajectory replay
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = '009_deterministic_runtime'
down_revision = '008_unified_instrumentation'


def upgrade():
    """Add deterministic metadata columns to outbox_event_envelopes"""
    # Add deterministic_mode column
    op.add_column(
        'outbox_event_envelopes',
        sa.Column('deterministic_mode', sa.Boolean(), nullable=True, index=True)
    )
    
    # Add deterministic_seed column
    op.add_column(
        'outbox_event_envelopes',
        sa.Column('deterministic_seed', sa.Integer(), nullable=True, index=True)
    )
    
    # Create index for deterministic queries
    op.create_index(
        'idx_outbox_deterministic',
        'outbox_event_envelopes',
        ['deterministic_mode', 'deterministic_seed']
    )


def downgrade():
    """Remove deterministic metadata columns from outbox_event_envelopes"""
    # Drop index
    op.drop_index('idx_outbox_deterministic', table_name='outbox_event_envelopes')
    
    # Remove deterministic_seed column
    op.drop_column('outbox_event_envelopes', 'deterministic_seed')
    
    # Remove deterministic_mode column
    op.drop_column('outbox_event_envelopes', 'deterministic_mode')
