"""Seed media-backed task variants for K-12 concepts.

Revision ID: 027_seed_media_task_variants
Revises: 026_add_task_media
Create Date: 2026-06-02 00:00:00.000000

Adds one video-question and one audio-listening task per K-12 concept already
present in the catalog. Media is URL-based so concurrent learners stream from
existing CDNs instead of the experiment host.
"""

from alembic import op


revision = "027_seed_media_task_variants"
down_revision = "026_add_task_media"
branch_labels = None
depends_on = None


VIDEO_URL = "https://www.youtube.com/embed/zOjov-2OZ0E"
AUDIO_URL = "https://upload.wikimedia.org/wikipedia/commons/c/c8/Example.ogg"


def upgrade():
    op.execute(f"""
        INSERT INTO tasks (
            id, title, description, concept_id, concept_type, difficulty,
            cognitive_level, task_type, content, solution, hints, metadata,
            media_url, media_type, transcript, created_at, updated_at
        )
        SELECT
            c.id || '_video_q1',
            'Watch: ' || COALESCE(c.concept_area, c.id),
            'Video-supported check for ' || c.id,
            c.id,
            'k12',
            LEAST(0.95, COALESCE(c.difficulty, 0.5) + 0.04),
            c.cognitive_level,
            'video_mcq',
            jsonb_build_object(
                'question', 'After watching the clip and reading the transcript, which statement best matches ' || c.id || '?',
                'choices', jsonb_build_array(
                    COALESCE(c.description, c.id),
                    'This concept is unrelated to computer science learning.',
                    'This concept can be mastered without practicing any task.',
                    'This concept is only useful after the final assessment.'
                ),
                'correct_answer', COALESCE(c.description, c.id),
                'explanation', 'The media reinforces the concept description and asks learners to connect it back to the curriculum node.',
                'transcript', 'This short media checkpoint introduces ' || c.id || ' in the ' || COALESCE(c.concept_area, 'Computer Science') || ' strand. Focus on the definition, the example, and why the concept matters before answering.',
                'media_url', '{VIDEO_URL}',
                'media_type', 'video'
            ),
            jsonb_build_object('explanation', 'Match the media to the concept description.'),
            '[]'::jsonb,
            '{{"seeded_for": "027_media_variants", "delivery": "url_embed"}}'::jsonb,
            '{VIDEO_URL}',
            'video',
            'This short media checkpoint introduces ' || c.id || ' in the ' || COALESCE(c.concept_area, 'Computer Science') || ' strand. Focus on the definition, the example, and why the concept matters before answering.',
            NOW(),
            NOW()
        FROM k12_concepts c
        WHERE EXISTS (
            SELECT 1 FROM tasks t
            WHERE t.concept_id = c.id AND t.concept_type = 'k12'
        )
        ON CONFLICT (id) DO UPDATE SET
            content = EXCLUDED.content,
            solution = EXCLUDED.solution,
            metadata = EXCLUDED.metadata,
            media_url = EXCLUDED.media_url,
            media_type = EXCLUDED.media_type,
            transcript = EXCLUDED.transcript,
            updated_at = NOW();
    """)

    op.execute(f"""
        INSERT INTO tasks (
            id, title, description, concept_id, concept_type, difficulty,
            cognitive_level, task_type, content, solution, hints, metadata,
            media_url, media_type, transcript, created_at, updated_at
        )
        SELECT
            c.id || '_audio_q1',
            'Listen: ' || COALESCE(c.concept_area, c.id),
            'Audio-supported check for ' || c.id,
            c.id,
            'k12',
            LEAST(0.95, COALESCE(c.difficulty, 0.5) + 0.02),
            c.cognitive_level,
            'audio_mcq',
            jsonb_build_object(
                'question', 'After listening and reading the transcript, what is the main idea of ' || c.id || '?',
                'choices', jsonb_build_array(
                    COALESCE(c.description, c.id),
                    'A random activity with no prerequisite relationship.',
                    'A media-only item that does not need practice.',
                    'A concept that should always be skipped.'
                ),
                'correct_answer', COALESCE(c.description, c.id),
                'explanation', 'The listening checkpoint reinforces the same concept identity before asking for recall.',
                'transcript', 'Audio checkpoint: ' || c.id || ' belongs to ' || COALESCE(c.concept_area, 'Computer Science') || '. Listen for the key idea, then choose the statement that matches the concept.',
                'media_url', '{AUDIO_URL}',
                'media_type', 'audio'
            ),
            jsonb_build_object('explanation', 'Match the audio checkpoint to the concept description.'),
            '[]'::jsonb,
            '{{"seeded_for": "027_media_variants", "delivery": "url_embed"}}'::jsonb,
            '{AUDIO_URL}',
            'audio',
            'Audio checkpoint: ' || c.id || ' belongs to ' || COALESCE(c.concept_area, 'Computer Science') || '. Listen for the key idea, then choose the statement that matches the concept.',
            NOW(),
            NOW()
        FROM k12_concepts c
        WHERE EXISTS (
            SELECT 1 FROM tasks t
            WHERE t.concept_id = c.id AND t.concept_type = 'k12'
        )
        ON CONFLICT (id) DO UPDATE SET
            content = EXCLUDED.content,
            solution = EXCLUDED.solution,
            metadata = EXCLUDED.metadata,
            media_url = EXCLUDED.media_url,
            media_type = EXCLUDED.media_type,
            transcript = EXCLUDED.transcript,
            updated_at = NOW();
    """)


def downgrade():
    op.execute("""
        DELETE FROM tasks
        WHERE metadata->>'seeded_for' = '027_media_variants'
    """)
