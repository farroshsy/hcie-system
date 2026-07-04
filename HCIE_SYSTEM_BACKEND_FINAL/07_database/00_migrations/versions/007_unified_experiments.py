"""Unified Schema - Experiment Infrastructure Tables

Revision ID: 007_unified_experiments
Revises: 006_unified_sessions
Create Date: 2026-05-12 00:00:00.000000

This migration creates the experiment infrastructure:
- experiment_runs: Track individual experiment runs
- cohort_assignments: Assign learners to experiment cohorts
- trajectory_records: Store learning trajectories for analysis

Design Principles:
- VARCHAR for experiment_run_id (consistent with application usage)
- VARCHAR for user_id (consistent with application usage)
- Proper foreign key constraints to experiments table
- Comprehensive signal tracking for cognitive trajectory analysis
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '007_unified_experiments'
down_revision = '006_unified_sessions'


def upgrade():
    # Create experiment_runs table
    op.create_table(
        'experiment_runs',
        sa.Column('id', sa.String(255), nullable=False, primary_key=True),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_name', sa.String(255), nullable=False),
        sa.Column('policy', sa.String(50), nullable=False, server_default='hcie'),
        sa.Column('learner_archetype', sa.String(50), nullable=False, server_default='novice'),
        sa.Column('num_learners', sa.Integer(), nullable=False, server_default=sa.text('100')),
        sa.Column('num_concepts', sa.Integer(), nullable=False, server_default=sa.text('20')),
        sa.Column('num_interactions', sa.Integer(), nullable=False, server_default=sa.text('100')),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('config', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('results', postgresql.JSONB(), nullable=True),
        sa.Column('metrics', postgresql.JSONB(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign key to experiments
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        
        # Indexes
        sa.Index('idx_experiment_runs_experiment', 'experiment_id'),
        sa.Index('idx_experiment_runs_status', 'status'),
        sa.Index('idx_experiment_runs_policy', 'policy')
    )
    
    # Create cohort_assignments table
    op.create_table(
        'cohort_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('experiment_run_id', sa.String(255), nullable=False),
        sa.Column('cohort_name', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign key to experiment_runs
        sa.ForeignKeyConstraint(['experiment_run_id'], ['experiment_runs.id'], ondelete='CASCADE'),
        
        # Unique constraint
        sa.UniqueConstraint('experiment_run_id', 'user_id', name='uq_cohort_assignment'),
        
        # Indexes
        sa.Index('idx_cohort_assignments_run', 'experiment_run_id'),
        sa.Index('idx_cohort_assignments_user', 'user_id')
    )
    
    # Create trajectory_records table
    op.create_table(
        'trajectory_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('experiment_run_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('concept', sa.String(255), nullable=False),
        sa.Column('interaction_id', sa.String(255), nullable=False),
        sa.Column('event_id', sa.String(255), nullable=False),
        sa.Column('interaction_number', sa.Integer(), nullable=False),
        
        # State before interaction
        sa.Column('mastery_before', sa.Float(), nullable=True),
        sa.Column('uncertainty_before', sa.Float(), nullable=True),
        sa.Column('confidence_before', sa.Float(), nullable=True),
        sa.Column('lyapunov_mastery_before', sa.Float(), nullable=True),
        sa.Column('bayesian_alpha_before', sa.Float(), nullable=True),
        sa.Column('bayesian_beta_before', sa.Float(), nullable=True),
        sa.Column('kalman_mastery_before', sa.Float(), nullable=True),
        sa.Column('kalman_covariance_before', sa.Float(), nullable=True),
        
        # Interaction data
        sa.Column('correctness', sa.Boolean(), nullable=True),
        sa.Column('response_time', sa.Float(), nullable=True),
        sa.Column('difficulty', sa.Float(), nullable=True),
        sa.Column('policy', sa.String(255), nullable=True),
        sa.Column('arm_selected', sa.String(255), nullable=True),
        
        # State after interaction
        sa.Column('mastery_after', sa.Float(), nullable=True),
        sa.Column('uncertainty_after', sa.Float(), nullable=True),
        sa.Column('confidence_after', sa.Float(), nullable=True),
        sa.Column('lyapunov_mastery_after', sa.Float(), nullable=True),
        sa.Column('bayesian_alpha_after', sa.Float(), nullable=True),
        sa.Column('bayesian_beta_after', sa.Float(), nullable=True),
        sa.Column('kalman_mastery_after', sa.Float(), nullable=True),
        sa.Column('kalman_covariance_after', sa.Float(), nullable=True),
        
        # Governance signals
        sa.Column('jt_value', sa.Float(), nullable=True),
        sa.Column('jt_volatility', sa.Float(), nullable=True),
        sa.Column('stability_index', sa.Float(), nullable=True),
        sa.Column('exploration_pressure', sa.Float(), nullable=True),
        
        # Transfer signals
        sa.Column('transfer_amount', sa.Float(), nullable=True),
        sa.Column('transfer_efficiency', sa.Float(), nullable=True),
        
        # ZPD signals
        sa.Column('zpd_target', sa.Float(), nullable=True),
        sa.Column('zpd_alignment_error', sa.Float(), nullable=True),
        sa.Column('zpd_score', sa.Float(), nullable=True),
        
        # Metadata
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign key to experiment_runs
        sa.ForeignKeyConstraint(['experiment_run_id'], ['experiment_runs.id'], ondelete='CASCADE'),
        
        # Indexes
        sa.Index('idx_trajectory_records_run', 'experiment_run_id'),
        sa.Index('idx_trajectory_records_user', 'experiment_run_id', 'user_id'),
        sa.Index('idx_trajectory_records_concept', 'experiment_run_id', 'concept'),
        sa.Index('idx_trajectory_records_interaction', 'experiment_run_id', 'interaction_number')
    )


def downgrade():
    op.drop_index('idx_trajectory_records_interaction', table_name='trajectory_records')
    op.drop_index('idx_trajectory_records_concept', table_name='trajectory_records')
    op.drop_index('idx_trajectory_records_user', table_name='trajectory_records')
    op.drop_index('idx_trajectory_records_run', table_name='trajectory_records')
    op.drop_table('trajectory_records')
    
    op.drop_index('idx_cohort_assignments_user', table_name='cohort_assignments')
    op.drop_index('idx_cohort_assignments_run', table_name='cohort_assignments')
    op.drop_table('cohort_assignments')
    
    op.drop_index('idx_experiment_runs_policy', table_name='experiment_runs')
    op.drop_index('idx_experiment_runs_status', table_name='experiment_runs')
    op.drop_index('idx_experiment_runs_experiment', table_name='experiment_runs')
    op.drop_table('experiment_runs')
