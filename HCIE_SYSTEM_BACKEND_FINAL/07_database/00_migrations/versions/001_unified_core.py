"""Unified Schema - Core Tables

Revision ID: 001_unified_core
Revises: 
Create Date: 2026-05-12 00:00:00.000000

This migration creates the core tables for the unified schema:
- users: User accounts with multi-tenant support and experiment tracking
- tenants: Multi-tenant organization support
- experiments: Experiment definitions with tenant scoping

Design Principles:
- UUID for database-generated primary keys
- VARCHAR(255) for user-facing IDs (consistent with application usage)
- tenant_id NOT NULL for all tenant-scoped tables
- Proper indexes for common query patterns
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_unified_core'
down_revision = None


def upgrade():
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Index('idx_tenants_name', 'name')
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='student'),
        
        # Multi-tenant support
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # HCIE-specific fields
        sa.Column('policy_mode', sa.String(50), nullable=False, server_default='hcie'),
        sa.Column('learning_rate', sa.Float(), nullable=False, server_default=sa.text('0.01')),
        sa.Column('forgetting_rate', sa.Float(), nullable=False, server_default=sa.text('0.001')),
        
        # Experiment system
        sa.Column('experiment_id', sa.String(255), nullable=True),
        sa.Column('experiment_group', sa.String(50), nullable=True),
        sa.Column('user_type', sa.String(50), nullable=False, server_default='real'),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_active', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign key to tenants
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='RESTRICT'),
        
        # Indexes
        sa.Index('idx_users_email', 'email'),
        sa.Index('idx_users_tenant', 'tenant_id'),
        sa.Index('idx_users_experiment', 'experiment_id'),
        sa.Index('idx_users_user_type', 'user_type')
    )
    
    # Add check constraint for user_type
    op.create_check_constraint('chk_users_user_type', 'users', "user_type IN ('real', 'simulated')")
    
    # Create experiments table
    op.create_table(
        'experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('groups', postgresql.JSONB(), nullable=False, server_default=sa.text("'[\"hcie\", \"random\"]'::jsonb")),
        sa.Column('status', sa.String(50), nullable=False, server_default='created'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign key to tenants
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        
        # Indexes
        sa.Index('idx_experiments_tenant', 'tenant_id'),
        sa.Index('idx_experiments_status', 'status')
    )


def downgrade():
    op.drop_index('idx_experiments_status', table_name='experiments')
    op.drop_index('idx_experiments_tenant', table_name='experiments')
    op.drop_table('experiments')
    
    op.drop_index('idx_users_user_type', table_name='users')
    op.drop_index('idx_users_experiment', table_name='users')
    op.drop_index('idx_users_tenant', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
    
    op.drop_index('idx_tenants_name', table_name='tenants')
    op.drop_table('tenants')
