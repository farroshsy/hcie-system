"""
Experiment Database Models

Persistent storage for pedagogical experiment metadata and assignments.
Supports replay-deterministic cohort assignment and experiment lineage tracking.
"""

from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, JSON, Integer
from sqlalchemy.dialects.postgresql import ENUM, ARRAY
from datetime import datetime
from storage.models.base import Base


class Experiment(Base):
    """Pedagogical experiment metadata"""
    __tablename__ = "experiments"
    
    experiment_id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    hypothesis = Column(Text, nullable=False)
    experiment_type = Column(
        ENUM('policy_comparison', 'cohort_segmentation', 'parameter_tuning', 
              'feature_flag', 'longitudinal_study', name='experiment_type'),
        nullable=False
    )
    policy_versions = Column(ARRAY(String), nullable=False)  # e.g., ["v1.0.0", "v1.1.0"]
    cohort_criteria = Column(JSON, nullable=False)  # Learner segmentation criteria
    rollout_percentage = Column(Float, nullable=False)  # 0.0 to 1.0
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    status = Column(
        ENUM('draft', 'active', 'paused', 'completed', 'archived', name='experiment_status'),
        nullable=False,
        default='draft'
    )
    evaluation_metrics = Column(ARRAY(String), nullable=True)  # Metrics to track
    replay_compatible = Column(Boolean, nullable=False, default=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExperimentAssignment(Base):
    """User-to-experiment assignment (replay-deterministic)"""
    __tablename__ = "experiment_assignments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    experiment_id = Column(String(64), nullable=False, index=True)
    assignment_key = Column(String(255), nullable=False, unique=True)  # For replay determinism
    policy_version = Column(String(32), nullable=False)  # Assigned policy version
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Track assignment consistency for validation
    assignment_hash = Column(String(64), nullable=False)  # SHA256 of deterministic inputs


class ExperimentMetric(Base):
    """Evaluation metrics collected during experiment"""
    __tablename__ = "experiment_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    metric_name = Column(String(128), nullable=False)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    metadata = Column(JSON, nullable=True)  # Additional context for the metric
