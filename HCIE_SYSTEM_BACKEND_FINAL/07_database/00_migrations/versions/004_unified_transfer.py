"""Unified Schema - Transfer Learning Tables

Revision ID: 004_unified_transfer
Revises: 003_unified_events
Create Date: 2026-05-12 00:00:00.000000

This migration creates the transfer learning infrastructure:
- concept_dependencies: DAG for transfer learning pathways
- transfer_learning_events: Transfer event tracking
- user_mastery_with_transfer: Mastery tracking including transferred knowledge

Design Principles:
- VARCHAR for concept names (consistent with application usage)
- DECIMAL for precise transfer amount calculations
- JSONB for flexible transfer sources tracking
- Trigger to maintain total_mastery = direct + transferred
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '004_unified_transfer'
down_revision = '003_unified_events'


def upgrade():
    # Create concept_dependencies table
    op.create_table(
        'concept_dependencies',
        sa.Column('source_concept', sa.String(255), nullable=False),
        sa.Column('target_concept', sa.String(255), nullable=False),
        sa.Column('transfer_weight', sa.Numeric(3, 2), nullable=False),
        sa.Column('dependency_type', sa.String(20), nullable=False),
        sa.Column('confidence_level', sa.Numeric(3, 2), nullable=False, server_default='0.8'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Constraints
        sa.PrimaryKeyConstraint('source_concept', 'target_concept')
    )
    
    # Add check constraints for concept_dependencies
    op.create_check_constraint('chk_transfer_weight_range', 'concept_dependencies', 'transfer_weight >= 0 AND transfer_weight <= 1')
    op.create_check_constraint('chk_dependency_type', 'concept_dependencies', "dependency_type IN ('prerequisite', 'related', 'advanced')")
    
    # Create transfer_learning_events table
    op.create_table(
        'transfer_learning_events',
        sa.Column('event_id', sa.BigInteger(), nullable=False, autoincrement=True, primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('source_concept', sa.String(255), nullable=False),
        sa.Column('target_concept', sa.String(255), nullable=False),
        sa.Column('transfer_amount', sa.Numeric(5, 4), nullable=False),
        sa.Column('transfer_type', sa.String(20), nullable=False),
        sa.Column('original_mastery_change', sa.Numeric(5, 4), nullable=False),
        sa.Column('transferred_mastery_change', sa.Numeric(5, 4), nullable=False),
        sa.Column('confidence_score', sa.Numeric(3, 2), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Indexes
        sa.Index('idx_transfer_events_user', 'user_id'),
        sa.Index('idx_transfer_events_source', 'source_concept'),
        sa.Index('idx_transfer_events_target', 'target_concept')
    )
    
    # Add check constraint for transfer_type
    op.create_check_constraint('chk_transfer_type', 'transfer_learning_events', "transfer_type IN ('direct', 'indirect', 'decay')")
    
    # Create user_mastery_with_transfer table
    op.create_table(
        'user_mastery_with_transfer',
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('concept_name', sa.String(255), nullable=False),
        sa.Column('direct_mastery', sa.Numeric(3, 2), nullable=False),
        sa.Column('transferred_mastery', sa.Numeric(3, 2), nullable=False, server_default='0'),
        sa.Column('total_mastery', sa.Numeric(3, 2), nullable=False),
        sa.Column('transfer_sources', postgresql.JSONB(), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Constraints
        sa.PrimaryKeyConstraint('user_id', 'concept_name')
    )
    
    # Add check constraints for user_mastery_with_transfer
    op.create_check_constraint('chk_direct_mastery_range', 'user_mastery_with_transfer', 'direct_mastery >= 0 AND direct_mastery <= 1')
    op.create_check_constraint('chk_transferred_mastery_range', 'user_mastery_with_transfer', 'transferred_mastery >= 0 AND transferred_mastery <= 1')
    op.create_check_constraint('chk_total_mastery_range', 'user_mastery_with_transfer', 'total_mastery >= 0 AND total_mastery <= 1')
    
    # Create trigger function to maintain total_mastery
    op.execute("""
        CREATE OR REPLACE FUNCTION update_total_mastery()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.total_mastery = LEAST(1.0, NEW.direct_mastery + NEW.transferred_mastery);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger
    op.execute("""
        CREATE TRIGGER trigger_update_total_mastery
            BEFORE INSERT OR UPDATE ON user_mastery_with_transfer
            FOR EACH ROW EXECUTE FUNCTION update_total_mastery();
    """)
    
    # Insert K-12 concept dependencies (from migration 018)
    op.execute("""
        INSERT INTO concept_dependencies (source_concept, target_concept, transfer_weight, dependency_type, confidence_level) VALUES
        -- Algorithm design is foundational
        ('k2_algorithms', 'k5_algorithms', 0.85, 'prerequisite', 0.9),
        ('k2_algorithms', 'k8_algorithms', 0.7, 'advanced', 0.8),
        ('k2_algorithms', 'k12_algorithms', 0.6, 'advanced', 0.7),
        
        -- Variables build on algorithms
        ('k2_variables', 'k5_variables', 0.8, 'prerequisite', 0.9),
        ('k2_variables', 'k8_variables', 0.7, 'advanced', 0.8),
        ('k2_variables', 'k12_variables', 0.6, 'advanced', 0.7),
        
        -- Control structures
        ('k2_control', 'k5_control', 0.8, 'prerequisite', 0.9),
        ('k2_control', 'k8_control', 0.7, 'advanced', 0.8),
        ('k2_control', 'k12_control', 0.6, 'advanced', 0.7),
        
        -- Modularity
        ('k2_modularity', 'k5_modularity', 0.7, 'related', 0.8),
        ('k2_modularity', 'k8_modularity', 0.6, 'advanced', 0.7),
        
        -- Program development
        ('k2_program_development', 'k5_program_development', 0.8, 'prerequisite', 0.9),
        ('k2_program_development', 'k8_program_development', 0.7, 'advanced', 0.8),
        ('k2_program_development', 'k12_program_development', 0.6, 'advanced', 0.7),
        
        -- Computing systems dependencies
        ('k2_computing_systems_devices', 'k5_computing_systems_devices', 0.9, 'prerequisite', 0.9),
        ('k2_computing_systems_devices', 'k8_computing_systems_devices', 0.8, 'advanced', 0.8),
        ('k2_computing_systems_hardware_software', 'k5_computing_systems_hardware_software', 0.9, 'prerequisite', 0.9),
        ('k2_computing_systems_hardware_software', 'k8_computing_systems_hardware_software', 0.8, 'advanced', 0.8),
        ('k2_computing_systems_troubleshooting', 'k5_computing_systems_troubleshooting', 0.8, 'advanced', 0.8),
        
        -- Networks dependencies
        ('k2_networks_communication', 'k5_networks_communication', 0.9, 'prerequisite', 0.9),
        ('k2_networks_communication', 'k8_networks_communication', 0.8, 'advanced', 0.8),
        ('k2_networks_cybersecurity', 'k5_networks_cybersecurity', 0.8, 'advanced', 0.8),
        ('k2_networks_cybersecurity', 'k8_networks_cybersecurity', 0.7, 'advanced', 0.8),
        
        -- Data dependencies
        ('k2_data_collection', 'k5_data_collection', 0.9, 'prerequisite', 0.9),
        ('k2_data_collection', 'k8_data_collection', 0.8, 'advanced', 0.8),
        ('k2_data_storage', 'k5_data_storage', 0.9, 'prerequisite', 0.9),
        ('k2_data_storage', 'k8_data_storage', 0.8, 'advanced', 0.8),
        ('k2_data_visualization', 'k5_data_visualization', 0.8, 'related', 0.8),
        ('k2_data_visualization', 'k8_data_visualization', 0.7, 'advanced', 0.8),
        ('k2_data_inference', 'k5_data_inference', 0.8, 'advanced', 0.8),
        
        -- Culture and social
        ('k2_culture', 'k5_culture', 0.8, 'related', 0.8),
        ('k2_culture', 'k8_culture', 0.7, 'advanced', 0.8),
        ('k2_social_interactions', 'k5_social_interactions', 0.8, 'related', 0.8),
        ('k2_social_interactions', 'k8_social_interactions', 0.7, 'advanced', 0.8),
        ('k2_safety_law_ethics', 'k5_safety_law_ethics', 0.8, 'advanced', 0.8),
        ('k2_safety_law_ethics', 'k8_safety_law_ethics', 0.7, 'advanced', 0.8),
        
        -- Impacts
        ('k2_impacts_culture', 'k5_impacts_culture', 0.8, 'related', 0.8),
        ('k2_impacts_culture', 'k8_impacts_culture', 0.7, 'advanced', 0.8),
        ('k2_impacts_social', 'k5_impacts_social', 0.8, 'related', 0.8),
        ('k2_impacts_social', 'k8_impacts_social', 0.7, 'advanced', 0.8),
        ('k2_impacts_safety', 'k5_impacts_safety', 0.8, 'related', 0.8),
        ('k2_impacts_safety', 'k8_impacts_safety', 0.7, 'advanced', 0.8)
        ON CONFLICT (source_concept, target_concept) DO NOTHING;
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trigger_update_total_mastery ON user_mastery_with_transfer")
    op.execute("DROP FUNCTION IF EXISTS update_total_mastery")
    
    op.drop_table('user_mastery_with_transfer')
    
    op.drop_index('idx_transfer_events_target', table_name='transfer_learning_events')
    op.drop_index('idx_transfer_events_source', table_name='transfer_learning_events')
    op.drop_index('idx_transfer_events_user', table_name='transfer_learning_events')
    op.drop_table('transfer_learning_events')
    
    op.drop_table('concept_dependencies')
