"""Add Missing Columns to Exploration Events Table

Revision ID: 023_add_exploration_events_missing_columns
Revises: 022_seed_k12_full_task_catalog
Create Date: 2026-05-27 00:00:00.000000

This migration adds missing columns to the exploration_events table:
- event_id: Unique event identifier for traceability
- experiment_run_id: Experiment run identifier for grouping

This handles the case where the exploration_events table was created
without these columns (e.g., from an older migration or manual setup).

Design Principles:
- Safe for existing tables (IF NOT EXISTS)
- Adds index on event_id for query performance
- Maintains backward compatibility
"""

from alembic import op
import sqlalchemy as sa

revision = '023_add_exploration_events_missing_columns'
down_revision = '022_seed_k12_full_task_catalog'


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Check if exploration_events table exists
    if "exploration_events" not in inspector.get_table_names():
        # Table doesn't exist, nothing to do
        return
    
    # Add missing columns if they don't exist
    op.execute("ALTER TABLE exploration_events ADD COLUMN IF NOT EXISTS event_id TEXT")
    op.execute("ALTER TABLE exploration_events ADD COLUMN IF NOT EXISTS experiment_run_id TEXT")
    
    # Create index on event_id for query performance
    op.execute("CREATE INDEX IF NOT EXISTS idx_exploration_events_event_id ON exploration_events(event_id) WHERE event_id IS NOT NULL")


def downgrade():
    # Remove the index
    op.execute("DROP INDEX IF EXISTS idx_exploration_events_event_id")
    
    # Remove the columns (safe even if they don't exist)
    op.execute("ALTER TABLE exploration_events DROP COLUMN IF EXISTS event_id")
    op.execute("ALTER TABLE exploration_events DROP COLUMN IF EXISTS experiment_run_id")
