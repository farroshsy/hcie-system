"""Add media fields to task catalog rows.

Revision ID: 026_add_task_media
Revises: 025_add_run_sealing
Create Date: 2026-06-02 00:00:00.000000

These additive columns let existing task catalog rows carry video/audio URLs
without changing the JSONB content contract. Existing text/MCQ rows remain
valid with NULL media fields.
"""

from alembic import op
import sqlalchemy as sa


revision = "026_add_task_media"
down_revision = "025_add_run_sealing"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tasks", sa.Column("media_url", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("media_type", sa.String(16), nullable=True))
    op.add_column("tasks", sa.Column("transcript", sa.Text(), nullable=True))
    op.create_index("idx_tasks_media_type", "tasks", ["media_type"])


def downgrade():
    op.drop_index("idx_tasks_media_type", table_name="tasks")
    op.drop_column("tasks", "transcript")
    op.drop_column("tasks", "media_type")
    op.drop_column("tasks", "media_url")
