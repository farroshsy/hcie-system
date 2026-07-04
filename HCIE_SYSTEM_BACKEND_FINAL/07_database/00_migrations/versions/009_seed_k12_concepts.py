"""Unified Schema - Seed K-12 Concepts

Revision ID: 009_seed_k12_concepts
Revises: 008_unified_instrumentation
Create Date: 2026-05-14 00:00:00.000000

This migration seeds the k12_concepts table with 62 unique concepts
extracted from concept_dependencies table.

Design Principles:
- Extract unique concepts from concept_dependencies edges
- Assign grade bands based on concept name prefixes (k2, k5, k8, k12)
- Assign concept areas based on concept name keywords
- Set cognitive levels based on grade band progression
- English language (Indonesian support can be added in frontend UI)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '009_seed_k12_concepts'
down_revision = '012_transfer_events'


def upgrade():
    # Seed k12_concepts with 62 unique concepts from concept_dependencies
    op.execute("""
        INSERT INTO k12_concepts (id, grade_band, concept_area, cognitive_level, difficulty, description, learning_objectives, created_at, updated_at)
        SELECT DISTINCT
            concept as id,
            CASE
                WHEN concept LIKE 'k2_%' THEN 'K-2'
                WHEN concept LIKE 'k5_%' THEN 'K-5'
                WHEN concept LIKE 'k8_%' THEN 'K-8'
                WHEN concept LIKE 'k12_%' THEN 'K-12'
                ELSE 'K-12'
            END as grade_band,
            CASE
                WHEN concept LIKE '%algorithm%' THEN 'Algorithms'
                WHEN concept LIKE '%variable%' THEN 'Variables'
                WHEN concept LIKE '%control%' THEN 'Control Structures'
                WHEN concept LIKE '%modularity%' THEN 'Modularity'
                WHEN concept LIKE '%program_development%' THEN 'Program Development'
                WHEN concept LIKE '%computing_systems%' THEN 'Computing Systems'
                WHEN concept LIKE '%networks%' THEN 'Networks'
                WHEN concept LIKE '%data%' THEN 'Data'
                WHEN concept LIKE '%culture%' THEN 'Culture'
                WHEN concept LIKE '%social%' THEN 'Social'
                WHEN concept LIKE '%safety%' THEN 'Safety'
                WHEN concept LIKE '%ethics%' THEN 'Ethics'
                WHEN concept LIKE '%impacts%' THEN 'Impacts'
                ELSE 'General'
            END as concept_area,
            CASE
                WHEN concept LIKE 'k2_%' THEN 1
                WHEN concept LIKE 'k5_%' THEN 2
                WHEN concept LIKE 'k8_%' THEN 3
                WHEN concept LIKE 'k12_%' THEN 4
                ELSE 2
            END as cognitive_level,
            CASE
                WHEN concept LIKE 'k2_%' THEN 0.2
                WHEN concept LIKE 'k5_%' THEN 0.4
                WHEN concept LIKE 'k8_%' THEN 0.6
                WHEN concept LIKE 'k12_%' THEN 0.8
                ELSE 0.5
            END as difficulty,
            concept as description,
            '["Understand", "Apply", "Analyze"]'::jsonb as learning_objectives,
            NOW() as created_at,
            NOW() as updated_at
        FROM (
            SELECT source_concept as concept FROM concept_dependencies
            UNION
            SELECT target_concept as concept FROM concept_dependencies
        ) as concepts
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade():
    # Remove seeded concepts
    op.execute("""
        DELETE FROM k12_concepts
        WHERE id IN (
            SELECT DISTINCT source_concept FROM concept_dependencies
            UNION
            SELECT DISTINCT target_concept FROM concept_dependencies
        )
    """)
