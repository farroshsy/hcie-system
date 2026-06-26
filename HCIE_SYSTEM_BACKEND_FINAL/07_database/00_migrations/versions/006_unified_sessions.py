"""Unified Schema - Session Runtime Tables

Revision ID: 006_unified_sessions
Revises: 005_unified_policy
Create Date: 2026-05-12 00:00:00.000000

This migration creates the session runtime infrastructure:
- sessions: Learning session tracking
- session_tasks: Tasks within a session

Design Principles:
- UUID for session_id (database-generated)
- VARCHAR for user_id (consistent with application usage)
- Proper foreign key constraints to users and tasks
- Indexes for session queries
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '006_unified_sessions'
down_revision = '005_unified_policy'


def upgrade():
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('current_task_id', sa.String(255), nullable=True),
        sa.Column('tasks_completed', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('target_concepts', postgresql.JSONB(), nullable=True),
        sa.Column('initial_concept_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('paused_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Indexes
        sa.Index('idx_sessions_user_id', 'user_id'),
        sa.Index('idx_sessions_status', 'status'),
        sa.Index('idx_sessions_created_at', 'created_at')
    )
    
    # Create session_tasks table
    op.create_table(
        'session_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', sa.String(255), nullable=False),
        sa.Column('concept_id', sa.String(255), nullable=False),
        sa.Column('question', sa.Text(), nullable=True),
        sa.Column('options', postgresql.JSONB(), nullable=True),
        sa.Column('difficulty', sa.Float(), nullable=True),
        sa.Column('difficulty_dimensions', postgresql.JSONB(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('misconception_detected', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('misconception_detail', sa.Text(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign key to sessions
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        
        # Indexes
        sa.Index('idx_session_tasks_session_id', 'session_id'),
        sa.Index('idx_session_tasks_task_id', 'task_id'),
        sa.Index('idx_session_tasks_concept_id', 'concept_id')
    )


def downgrade():
    op.drop_index('idx_session_tasks_concept_id', table_name='session_tasks')
    op.drop_index('idx_session_tasks_task_id', table_name='session_tasks')
    op.drop_index('idx_session_tasks_session_id', table_name='session_tasks')
    op.drop_table('session_tasks')
    
    op.drop_index('idx_sessions_created_at', table_name='sessions')
    op.drop_index('idx_sessions_status', table_name='sessions')
    op.drop_index('idx_sessions_user_id', table_name='sessions')
    op.drop_table('sessions')
