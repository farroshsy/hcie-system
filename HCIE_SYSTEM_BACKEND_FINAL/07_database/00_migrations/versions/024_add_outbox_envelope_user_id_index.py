"""Add Performance Index for Outbox Event Envelopes User ID

Revision ID: 024_add_outbox_envelope_user_id_index
Revises: 023_add_exploration_events_missing_columns
Create Date: 2026-05-28 00:00:00.000000

This migration adds a performance index on the outbox_event_envelopes table
for session-trace optimization. The index is a partial index on CognitionUpdated
events only to keep the index size small and improve query performance for
user-specific session trace queries.

Performance Impact:
- Optimizes session-trace queries that filter by user_id on CognitionUpdated events
- Reduces query time from sequential scans to indexed lookups
- Partial index keeps storage overhead minimal by indexing only relevant event types

Design Principles:
- Uses CONCURRENTLY to avoid blocking writes in production
- Partial index (WHERE event_type = 'CognitionUpdated') keeps index small
- IF NOT EXISTS ensures idempotency
- Safe for existing tables and data
"""

from alembic import op
import sqlalchemy as sa

revision = '024_add_outbox_envelope_user_id_index'
down_revision = '023_add_exploration_events_missing_columns'


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Check if outbox_event_envelopes table exists
    if "outbox_event_envelopes" not in inspector.get_table_names():
        # Table doesn't exist, nothing to do
        return
    
    # Create partial index on user_id for CognitionUpdated events.
    # CREATE INDEX CONCURRENTLY cannot run inside a transaction block, and alembic
    # wraps each migration in a transaction by default — so escape into an
    # autocommit block. Without this the whole 021->025 chain fails here and the
    # live DB stays stuck at 020 (schema drift). IF NOT EXISTS keeps it idempotent.
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_outbox_envelope_user_id
            ON outbox_event_envelopes(((envelope::jsonb -> 'payload' ->> 'user_id')))
            WHERE event_type = 'CognitionUpdated'
        """)
        # Update query planner statistics for the freshly indexed table
        op.execute("ANALYZE outbox_event_envelopes")


def downgrade():
    # Remove the performance index
    op.execute("DROP INDEX IF EXISTS idx_outbox_envelope_user_id")
