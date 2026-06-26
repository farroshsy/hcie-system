"""Allow synthetic learner IDs in learning_state.

Revision ID: 016_learning_state_text_user_ids
Revises: 015_seed_cohort_k12_task_catalog
Create Date: 2026-05-21 00:00:00.000000

Slice 4 synthetic learners are partitioned with IDs like
``synthetic:{cohort_id}:{run_id}:...``. The write path persists canonical
attempt state to learning_state, so user_id must be text instead of UUID.
"""

from alembic import op


revision = "016_learning_state_text_user_ids"
down_revision = "015_seed_cohort_k12_task_catalog"


def upgrade():
    # learning_state is normally created lazily by the repository at API
    # startup, but fresh installs hit this migration before the API ever
    # runs. Create the table with TEXT user_id when absent; otherwise
    # widen an existing UUID column for synthetic learner IDs.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS learning_state (
            user_id TEXT NOT NULL,
            concept VARCHAR(255) NOT NULL,
            state_data JSONB NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (user_id, concept)
        )
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'learning_state'
                  AND column_name = 'user_id'
                  AND udt_name = 'uuid'
            ) THEN
                ALTER TABLE learning_state
                ALTER COLUMN user_id TYPE TEXT
                USING user_id::text;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_learning_state_user_id ON learning_state(user_id);
        CREATE INDEX IF NOT EXISTS idx_learning_state_concept ON learning_state(concept);
        CREATE INDEX IF NOT EXISTS idx_learning_state_updated_at ON learning_state(updated_at);
        """
    )


def downgrade():
    op.execute("DELETE FROM learning_state WHERE user_id LIKE 'synthetic:%'")
    op.execute(
        """
        ALTER TABLE learning_state
        ALTER COLUMN user_id TYPE UUID
        USING user_id::uuid
        """
    )
