"""Unified Schema - Event Sourcing Tables

Revision ID: 003_unified_events
Revises: 002_unified_learning
Create Date: 2026-05-12 00:00:00.000000

This migration creates the event sourcing infrastructure:
- interactions: Learning interaction records
- outbox_events: Outbox pattern for reliable event publishing
- processed_events: Idempotency tracking for processed events
- user_state: User learning progress state
- outbox_event_envelopes: Advanced outbox pattern with correlation/causation IDs

Design Principles:
- VARCHAR(255) for user_id and event_id (consistent with application usage)
- SERIAL for auto-increment primary keys
- JSONB for flexible event payload storage
- Proper indexes for event queries and idempotency
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003_unified_events'
down_revision = '002_unified_learning'


def upgrade():
    # Create interactions table
    op.create_table(
        'interactions',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True, primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('concept_id', sa.String(255), nullable=False),
        sa.Column('representation', sa.String(255), nullable=False),
        sa.Column('correct', sa.Boolean(), nullable=False),
        sa.Column('reward', sa.Float(), nullable=False),
        sa.Column('response_time', sa.Float(), nullable=False),
        sa.Column('difficulty', sa.Float(), nullable=False),
        sa.Column('task_id', sa.String(255), nullable=True),
        sa.Column('policy_mode', sa.String(255), nullable=True),
        sa.Column('learning_gain', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Indexes
        sa.Index('idx_interactions_user_id', 'user_id'),
        sa.Index('idx_interactions_concept_id', 'concept_id'),
        sa.Index('idx_interactions_timestamp', 'timestamp'),
        sa.Index('idx_interactions_correct', 'correct')
    )
    
    # Create outbox_events table
    op.create_table(
        'outbox_events',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True, primary_key=True),
        sa.Column('event_id', sa.String(255), nullable=False, unique=True),
        sa.Column('topic', sa.String(255), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('error_message', sa.Text(), nullable=True),
        
        # Indexes
        sa.Index('idx_outbox_events_status', 'status'),
        sa.Index('idx_outbox_events_created_at', 'created_at'),
        sa.Index('idx_outbox_events_topic', 'topic')
    )
    
    # Create processed_events table
    op.create_table(
        'processed_events',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True, primary_key=True),
        sa.Column('event_id', sa.String(255), nullable=False, unique=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Indexes
        sa.Index('idx_processed_events_event_id', 'event_id'),
        sa.Index('idx_processed_events_user_id', 'user_id')
    )
    
    # Create user_state table
    op.create_table(
        'user_state',
        sa.Column('user_id', sa.String(255), nullable=False, primary_key=True),
        sa.Column('mastery', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create outbox_event_envelopes table
    op.create_table(
        'outbox_event_envelopes',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True, primary_key=True),
        sa.Column('event_id', sa.String(255), nullable=False, unique=True),
        sa.Column('event_type', sa.String(255), nullable=False),
        sa.Column('topic', sa.String(255), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('envelope', postgresql.JSONB(), nullable=False),
        sa.Column('correlation_id', sa.String(255), nullable=True),
        sa.Column('causation_id', sa.String(255), nullable=True),
        sa.Column('source_service', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        
        # Indexes
        sa.Index('idx_outbox_event_envelopes_event_type_topic', 'event_type', 'topic'),
        sa.Index('idx_outbox_event_envelopes_timestamp', 'timestamp')
    )


def downgrade():
    op.drop_index('idx_outbox_event_envelopes_timestamp', table_name='outbox_event_envelopes')
    op.drop_index('idx_outbox_event_envelopes_event_type_topic', table_name='outbox_event_envelopes')
    op.drop_table('outbox_event_envelopes')
    
    op.drop_table('user_state')
    
    op.drop_index('idx_processed_events_user_id', table_name='processed_events')
    op.drop_index('idx_processed_events_event_id', table_name='processed_events')
    op.drop_table('processed_events')
    
    op.drop_index('idx_outbox_events_topic', table_name='outbox_events')
    op.drop_index('idx_outbox_events_created_at', table_name='outbox_events')
    op.drop_index('idx_outbox_events_status', table_name='outbox_events')
    op.drop_table('outbox_events')
    
    op.drop_index('idx_interactions_correct', table_name='interactions')
    op.drop_index('idx_interactions_timestamp', table_name='interactions')
    op.drop_index('idx_interactions_concept_id', table_name='interactions')
    op.drop_index('idx_interactions_user_id', table_name='interactions')
    op.drop_table('interactions')
