"""Stage 0: run sealing — sealed_runs manifest + run_forks lineage.

Adds two additive tables. No change to existing tables or behavior.
"""

revision = "025_add_run_sealing"
down_revision = "024_add_outbox_envelope_user_id_index"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS sealed_runs (
            seal_id            TEXT PRIMARY KEY,
            experiment_run_id  TEXT NOT NULL,
            sealed_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
            as_of_row_count    BIGINT NOT NULL,
            content_hash       TEXT NOT NULL,
            frozen_stats       JSONB NOT NULL,
            dataset_id         TEXT,
            sealed_by          TEXT,
            note               TEXT
        );
    """)
    # one seal per run; re-sealing returns the existing manifest (see run_sealing.seal_run)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_sealed_runs_run ON sealed_runs(experiment_run_id);")
    op.execute("""
        CREATE TABLE IF NOT EXISTS run_forks (
            parent_run_id  TEXT NOT NULL,
            child_run_id   TEXT NOT NULL,
            active         BOOLEAN NOT NULL DEFAULT TRUE,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    # at most one ACTIVE child per parent → safe find-or-create under concurrency
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_run_forks_active_parent ON run_forks(parent_run_id) WHERE active;")
    op.execute("CREATE INDEX IF NOT EXISTS ix_run_forks_child ON run_forks(child_run_id);")


def downgrade():
    op.execute("DROP TABLE IF EXISTS run_forks;")
    op.execute("DROP TABLE IF EXISTS sealed_runs;")
