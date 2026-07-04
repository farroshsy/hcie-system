"""Seed media variants for task concepts absent from k12_concepts.

Revision ID: 028_seed_media_for_orphan_task_concepts
Revises: 027_seed_media_task_variants
Create Date: 2026-06-02 00:00:00.000000

Migration 027 uses k12_concepts as the source of concept metadata. A few legacy
task rows can reference concept IDs that have not been backfilled into
k12_concepts yet. This migration covers those active task concepts too.
"""

from alembic import op


revision = "028_seed_media_for_orphan_task_concepts"
down_revision = "027_seed_media_task_variants"
branch_labels = None
depends_on = None


VIDEO_URL = "https://www.youtube.com/embed/zOjov-2OZ0E"
AUDIO_URL = "https://upload.wikimedia.org/wikipedia/commons/c/c8/Example.ogg"


def upgrade():
    op.execute(f"""
        WITH orphan_concepts AS (
            SELECT DISTINCT t.concept_id
            FROM tasks t
            LEFT JOIN k12_concepts c ON c.id = t.concept_id
            WHERE t.concept_type = 'k12'
              AND t.concept_id IS NOT NULL
              AND c.id IS NULL
        )
        INSERT INTO tasks (
            id, title, description, concept_id, concept_type, difficulty,
            cognitive_level, task_type, content, solution, hints, metadata,
            media_url, media_type, transcript, created_at, updated_at
        )
        SELECT
            o.concept_id || '_video_q1',
            'Watch: ' || o.concept_id,
            'Video-supported check for ' || o.concept_id,
            o.concept_id,
            'k12',
            0.6,
            3,
            'video_mcq',
            jsonb_build_object(
                'question', 'After watching the clip and reading the transcript, which statement best matches ' || o.concept_id || '?',
                'choices', jsonb_build_array(
                    'This checkpoint reviews ' || o.concept_id || ' as part of the K-12 CS sequence.',
                    'This concept is unrelated to computer science learning.',
                    'This concept should be skipped because it has no task row.',
                    'This media item does not require an answer.'
                ),
                'correct_answer', 'This checkpoint reviews ' || o.concept_id || ' as part of the K-12 CS sequence.',
                'explanation', 'The media checkpoint is attached to an active task concept even though the concept metadata row is missing.',
                'transcript', 'This media checkpoint reviews ' || o.concept_id || ' as part of the K-12 CS sequence.',
                'media_url', '{VIDEO_URL}',
                'media_type', 'video'
            ),
            jsonb_build_object('explanation', 'Match the media checkpoint to the active concept.'),
            '[]'::jsonb,
            '{{"seeded_for": "028_orphan_media_variants", "delivery": "url_embed"}}'::jsonb,
            '{VIDEO_URL}',
            'video',
            'This media checkpoint reviews ' || o.concept_id || ' as part of the K-12 CS sequence.',
            NOW(),
            NOW()
        FROM orphan_concepts o
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute(f"""
        WITH orphan_concepts AS (
            SELECT DISTINCT t.concept_id
            FROM tasks t
            LEFT JOIN k12_concepts c ON c.id = t.concept_id
            WHERE t.concept_type = 'k12'
              AND t.concept_id IS NOT NULL
              AND c.id IS NULL
        )
        INSERT INTO tasks (
            id, title, description, concept_id, concept_type, difficulty,
            cognitive_level, task_type, content, solution, hints, metadata,
            media_url, media_type, transcript, created_at, updated_at
        )
        SELECT
            o.concept_id || '_audio_q1',
            'Listen: ' || o.concept_id,
            'Audio-supported check for ' || o.concept_id,
            o.concept_id,
            'k12',
            0.58,
            3,
            'audio_mcq',
            jsonb_build_object(
                'question', 'After listening and reading the transcript, what is the main idea of ' || o.concept_id || '?',
                'choices', jsonb_build_array(
                    'This checkpoint reviews ' || o.concept_id || ' as part of the K-12 CS sequence.',
                    'This concept has no connection to the active task catalog.',
                    'This listening item should always be skipped.',
                    'This item is only a system health check.'
                ),
                'correct_answer', 'This checkpoint reviews ' || o.concept_id || ' as part of the K-12 CS sequence.',
                'explanation', 'The listening checkpoint is attached to an active task concept even though the concept metadata row is missing.',
                'transcript', 'Audio checkpoint for ' || o.concept_id || ': listen for the key idea, then choose the matching statement.',
                'media_url', '{AUDIO_URL}',
                'media_type', 'audio'
            ),
            jsonb_build_object('explanation', 'Match the audio checkpoint to the active concept.'),
            '[]'::jsonb,
            '{{"seeded_for": "028_orphan_media_variants", "delivery": "url_embed"}}'::jsonb,
            '{AUDIO_URL}',
            'audio',
            'Audio checkpoint for ' || o.concept_id || ': listen for the key idea, then choose the matching statement.',
            NOW(),
            NOW()
        FROM orphan_concepts o
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade():
    op.execute("""
        DELETE FROM tasks
        WHERE metadata->>'seeded_for' = '028_orphan_media_variants'
    """)
