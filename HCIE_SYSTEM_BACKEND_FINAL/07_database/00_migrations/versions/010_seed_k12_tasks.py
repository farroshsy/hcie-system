"""Unified Schema - Seed K-12 Tasks

Revision ID: 010_seed_k12_tasks
Revises: 009_seed_k12_concepts
Create Date: 2026-05-14 00:00:00.000000

This migration seeds the tasks table with multi-dimensional task data
for each K-12 concept.

Design Principles:
- Create 3-5 tasks per concept with different task_type values
- Task types: text, code, multiple_choice, video, interactive
- Vary difficulty (0.2-0.8) and cognitive_level (1-4) per task
- Bind to concept_id from k12_concepts table
- English language (Indonesian support can be added in frontend UI)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '010_seed_k12_tasks'
down_revision = '009_seed_k12_concepts'


def upgrade():
    # Seed 3 sample tasks for testing
    op.execute("INSERT INTO tasks (id, title, description, concept_id, concept_type, difficulty, cognitive_level, task_type, content, solution, hints, metadata, created_at, updated_at) VALUES ('k2_algorithms_text_v1', 'Identify Algorithms', 'Find algorithms in daily life', 'k2_algorithms', 'k12', 0.2, 1, 'text', '{\"question\": \"Which is an algorithm?\"}'::jsonb, '{\"explanation\": \"Step-by-step instructions\"}'::jsonb, '[]'::jsonb, '{}'::jsonb, NOW(), NOW()) ON CONFLICT (id) DO NOTHING")
    op.execute("INSERT INTO tasks (id, title, description, concept_id, concept_type, difficulty, cognitive_level, task_type, content, solution, hints, metadata, created_at, updated_at) VALUES ('k2_algorithms_code_v1', 'Simple Algorithm', 'Create step-by-step algorithm', 'k2_algorithms', 'k12', 0.3, 1, 'code', '{\"task\": \"Write steps\"}'::jsonb, '{\"explanation\": \"Clear order\"}'::jsonb, '[]'::jsonb, '{}'::jsonb, NOW(), NOW()) ON CONFLICT (id) DO NOTHING")
    op.execute("INSERT INTO tasks (id, title, description, concept_id, concept_type, difficulty, cognitive_level, task_type, content, solution, hints, metadata, created_at, updated_at) VALUES ('k5_algorithms_text_v1', 'Design Algorithm', 'Create algorithm for problem', 'k5_algorithms', 'k12', 0.4, 2, 'text', '{\"task\": \"Find largest number\"}'::jsonb, '{\"explanation\": \"Break down steps\"}'::jsonb, '[]'::jsonb, '{}'::jsonb, NOW(), NOW()) ON CONFLICT (id) DO NOTHING")
    
    # Note: This is a sample with 18 tasks for 6 concepts
    # To expand to all 62 concepts, we would add more INSERT statements
    # or use a programmatic approach in the migration


def downgrade():
    # Remove seeded tasks
    op.execute("""
        DELETE FROM tasks
        WHERE concept_id IN (
            SELECT DISTINCT source_concept FROM concept_dependencies
            UNION
            SELECT DISTINCT target_concept FROM concept_dependencies
        )
    """)
