"""Add language + archetype tags to tasks; create learning_materials and
user_archetype_profile tables.

Revision ID: 029_add_language_archetype_and_materials
Revises: 028_seed_media_for_orphan_task_concepts
Create Date: 2026-06-02 00:00:00.000000

Three additions, all additive:

1. ``tasks.language`` and ``tasks.archetype_tags`` — lets a single concept
   carry parallel EN/ID rows and lets each task self-describe which learner
   archetypes it best fits. The recommend hot path filters by language; the
   tags are only joined into the ``selection_metrics`` payload as a
   covariate, never multiplied into the bandit score (see Slice 5b design
   note: keeps HCIE/JT validation clean).

2. ``learning_materials`` — a separate artifact class from gradeable tasks.
   Stored in its own table because the contract differs (no answer, no
   correctness signal, no MAB scoring) and folding them into ``tasks`` would
   force every read path to branch on "is this gradeable?" forever.

3. ``user_archetype_profile`` — captures the self-reported VARK / behavioural
   / motivational profile from the onboarding card. ``source`` distinguishes
   self-report from any future inferred profile so we can compare the two.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "029_add_language_archetype_and_materials"
down_revision = "028_seed_media_for_orphan_task_concepts"
branch_labels = None
depends_on = None


def upgrade():
    # ── tasks: language + archetype tags ──────────────────────────────────
    op.add_column(
        "tasks",
        sa.Column("language", sa.String(8), nullable=False, server_default="en"),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "archetype_tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.create_index("idx_tasks_concept_language", "tasks", ["concept_id", "language"])
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tasks_archetype_tags "
        "ON tasks USING gin (archetype_tags)"
    )

    # ── learning_materials ────────────────────────────────────────────────
    op.create_table(
        "learning_materials",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("concept_id", sa.Text(), nullable=False),
        sa.Column("language", sa.String(8), nullable=False, server_default="en"),
        sa.Column("modality", sa.String(32), nullable=False),
        sa.Column(
            "archetype_tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("media_url", sa.Text(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("difficulty", sa.Float(), nullable=False, server_default="0.4"),
        sa.Column(
            "prerequisites_assumed",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Modality is an open enum at the column level; we constrain at the
        # API layer so future modalities (e.g. ``simulation``) don't require
        # a migration.
        sa.CheckConstraint(
            "modality IN ('reading','video','audio','diagram','interactive','example')",
            name="chk_learning_materials_modality",
        ),
    )
    op.create_index(
        "idx_learning_materials_concept_language",
        "learning_materials",
        ["concept_id", "language"],
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_learning_materials_archetype_tags "
        "ON learning_materials USING gin (archetype_tags)"
    )

    # ── user_archetype_profile ────────────────────────────────────────────
    # Note: we intentionally do NOT declare JSONB server defaults for the
    # score columns. The application layer always supplies a complete profile
    # on insert, and the colon characters in inline JSONB literals collide
    # with SQLAlchemy's ``text()`` bind-parameter syntax (``:name``), which
    # silently rewrote ``"visual":0.25`` to ``"visual"NULL.25`` and aborted
    # the migration. NULL is acceptable because the API guarantees no row is
    # created without a populated profile.
    op.create_table(
        "user_archetype_profile",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "vark_scores",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "behav_scores",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "motiv_scores",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("source", sa.String(16), nullable=False, server_default="self_report"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column(
            "raw_responses",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "source IN ('self_report','inferred','hybrid','default')",
            name="chk_archetype_source",
        ),
    )


def downgrade():
    op.drop_table("user_archetype_profile")
    op.execute("DROP INDEX IF EXISTS idx_learning_materials_archetype_tags")
    op.drop_index(
        "idx_learning_materials_concept_language", table_name="learning_materials"
    )
    op.drop_table("learning_materials")
    op.execute("DROP INDEX IF EXISTS idx_tasks_archetype_tags")
    op.drop_index("idx_tasks_concept_language", table_name="tasks")
    op.drop_column("tasks", "archetype_tags")
    op.drop_column("tasks", "language")
