"""Unified Schema - Learning Tables

Revision ID: 002_unified_learning
Revises: 001_unified_core
Create Date: 2026-05-12 00:00:00.000000

This migration creates the learning content tables:
- k12_concepts: K-12 CS Framework concepts (canonical)
- tasks: Learning tasks bound to K-12 concepts (concept_type='k12')

Phase 14c amendment (replay-breaking, see final_intent.md section 10):
The ct_concepts table was removed from this baseline. The CT vocabulary
is retired and superseded by the K-12 DAG seeded by 009_seed_k12_concepts
and 010_seed_k12_tasks. Any pre-Phase-14c snapshot that created
ct_concepts must reset via downgrade-and-replay; partial upgrades from
pre-amendment baselines are not supported.

Design Principles:
- VARCHAR for concept and task IDs (consistent with application usage)
- JSONB for flexible metadata storage
- Proper indexes for concept and task queries
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_unified_learning'
down_revision = '001_unified_core'


def upgrade():
    # Create k12_concepts table
    op.create_table(
        'k12_concepts',
        sa.Column('id', sa.String(255), nullable=False, primary_key=True),
        sa.Column('grade_band', sa.String(50), nullable=True),
        sa.Column('concept_area', sa.String(100), nullable=True),
        sa.Column('cognitive_level', sa.Integer(), nullable=True),
        sa.Column('difficulty', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('prerequisites', postgresql.JSONB(), nullable=True),
        sa.Column('learning_objectives', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Indexes
        sa.Index('idx_k12_concepts_grade_band', 'grade_band'),
        sa.Index('idx_k12_concepts_concept_area', 'concept_area')
    )
    
    # Create tasks table (canonical K-12 binding via concept_type='k12')
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(255), nullable=False, primary_key=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('concept_id', sa.String(255), nullable=True),
        sa.Column('concept_type', sa.String(50), nullable=True),  # 'ct' or 'k12'
        sa.Column('difficulty', sa.Float(), nullable=True),
        sa.Column('cognitive_level', sa.Integer(), nullable=True),
        sa.Column('task_type', sa.String(50), nullable=True),  # 'text', 'code', 'multiple_choice', etc.
        sa.Column('content', postgresql.JSONB(), nullable=True),
        sa.Column('solution', postgresql.JSONB(), nullable=True),
        sa.Column('hints', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Indexes
        sa.Index('idx_tasks_concept_id', 'concept_id'),
        sa.Index('idx_tasks_concept_type', 'concept_type'),
        sa.Index('idx_tasks_difficulty', 'difficulty')
    )


def downgrade():
    op.drop_index('idx_tasks_difficulty', table_name='tasks')
    op.drop_index('idx_tasks_concept_type', table_name='tasks')
    op.drop_index('idx_tasks_concept_id', table_name='tasks')
    op.drop_table('tasks')

    # Phase 14c: ct_concepts removed from baseline upgrade; downgrade is
    # defensive in case the table exists in a pre-amendment snapshot.
    op.execute("DROP TABLE IF EXISTS ct_concepts")

    op.drop_index('idx_k12_concepts_concept_area', table_name='k12_concepts')
    op.drop_index('idx_k12_concepts_grade_band', table_name='k12_concepts')
    op.drop_table('k12_concepts')
