"""Bandit State Persistence - Add SQL backup for bandit state and regret tracking

Revision ID: 014_bandit_persistence
Revises: 013_phase_a_observability
Create Date: 2026-05-18 00:00:00.000000

This migration adds SQL backup tables for bandit state and regret tracking:
- bandit_state: Stores alpha/beta parameters for Thompson sampling
- bandit_regret: Stores cumulative regret metrics for research/analysis

Design Principles:
- Provides production resilience against Redis flush
- Enables recovery of bandit learning history
- Supports policy learning history analysis
- Dual-write strategy (Redis + SQL) for performance and durability
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '014_bandit_persistence'
down_revision = '013_phase_a_observability'


def upgrade():
    # Create bandit_state table for alpha/beta parameters
    op.execute("""
    CREATE TABLE IF NOT EXISTS bandit_state (
        user_id UUID NOT NULL,
        arm VARCHAR(255) NOT NULL,
        alpha FLOAT NOT NULL,
        beta FLOAT NOT NULL,
        last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, arm)
    )
    """)
    
    # Create bandit_regret table for regret tracking
    op.execute("""
    CREATE TABLE IF NOT EXISTS bandit_regret (
        user_id UUID NOT NULL,
        regret_type VARCHAR(50) NOT NULL,
        cumulative_regret FLOAT NOT NULL DEFAULT 0.0,
        step_count INTEGER NOT NULL DEFAULT 0,
        last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, regret_type)
    )
    """)
    
    # Add indexes for query performance
    op.execute("CREATE INDEX IF NOT EXISTS idx_bandit_state_user ON bandit_state(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_bandit_state_last_updated ON bandit_state(last_updated)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_bandit_regret_user ON bandit_regret(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_bandit_regret_last_updated ON bandit_regret(last_updated)")


def downgrade():
    # Remove indexes
    op.execute("DROP INDEX IF EXISTS idx_bandit_regret_last_updated")
    op.execute("DROP INDEX IF EXISTS idx_bandit_regret_user")
    op.execute("DROP INDEX IF EXISTS idx_bandit_state_last_updated")
    op.execute("DROP INDEX IF EXISTS idx_bandit_state_user")
    
    # Remove tables
    op.execute("DROP TABLE IF EXISTS bandit_regret")
    op.execute("DROP TABLE IF EXISTS bandit_state")
