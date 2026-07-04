"""
PostgreSQL Models for HCIE System
SQLAlchemy models for persistent storage
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class User(Base):
    """User model for storing user profiles and metadata"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User metadata
    display_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    # Learning metadata
    total_interactions = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)
    average_response_time = Column(Float, default=0.0)
    
    # System metadata
    policy_mode = Column(String, default="hcie")  # "hcie", "heuristic", "static", "random", "ct", "ednet"
    last_interaction = Column(DateTime, nullable=True)
    
    # Relationships
    interactions = relationship("Interaction", back_populates="user")
    mastery_snapshots = relationship("MasterySnapshot", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, policy_mode={self.policy_mode})>"

class Concept(Base):
    """Concept model for storing concept metadata"""
    __tablename__ = "concepts"
    
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Concept metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String, nullable=True)  # e.g., "math", "science"
    
    # CT/EdNet mode support
    category = Column(String, nullable=True)  # CT category or EdNet domain
    cognitive_level = Column(Integer, nullable=True)  # 1-4 for CT, null for EdNet
    grade_level = Column(String, nullable=True)  # elementary/middle/high_school for CT
    
    # Difficulty and metadata
    difficulty = Column(Float, default=0.5)
    prerequisite_concepts = Column(JSON, default=list)  # List of concept IDs
    
    # System metadata
    is_active = Column(Boolean, default=True)
    
    # Relationships
    interactions = relationship("Interaction", back_populates="concept")
    mastery_snapshots = relationship("MasterySnapshot", back_populates="concept")
    
    def __repr__(self):
        return f"<Concept(id={self.id}, difficulty={self.difficulty})>"

class Interaction(Base):
    """Interaction model for storing user learning interactions"""
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True)  # Database has integer, not UUID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    concept_id = Column(String, ForeignKey("concepts.id"), nullable=False)
    
    # Interaction data
    task_id = Column(String, nullable=False)
    representation = Column(String, nullable=False)
    answer = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    correct = Column(Boolean, nullable=False)
    response_time = Column(Float, nullable=False)
    
    # System data
    difficulty = Column(Float, nullable=False)
    reward = Column(Float, nullable=False)
    policy_mode = Column(String, nullable=False)
    
    # CT/EdNet mode support
    learning_gain = Column(Float, nullable=True)  # Calculated learning gain
    zpd_alignment = Column(Float, nullable=True)  # ZPD alignment score
    time_efficiency = Column(Float, nullable=True)  # Response time efficiency
    
    # Learning metrics
    mastery_before = Column(Float, nullable=True)
    mastery_after = Column(Float, nullable=True)
    mastery_change = Column(Float, nullable=True)
    uncertainty_before = Column(Float, nullable=True)
    uncertainty_after = Column(Float, nullable=True)
    
    # CT-specific metrics
    concept_bonus = Column(Float, nullable=True)  # Concept-specific bonus for CT mode
    
    # Selection metrics
    selection_score = Column(Float, nullable=True)
    thompson_score = Column(Float, nullable=True)
    learning_gain = Column(Float, nullable=True)
    
    # Additional metadata
    interaction_metadata = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    concept = relationship("Concept", back_populates="interactions")
    
    def __repr__(self):
        mode_info = f"({self.policy_mode})" if self.policy_mode else ""
        return f"<Interaction(user={self.user_id}, concept={self.concept_id}, correct={self.correct}){mode_info}>"

class MasterySnapshot(Base):
    """Mastery snapshot model for tracking mastery over time"""
    __tablename__ = "mastery_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    concept_id = Column(String, ForeignKey("concepts.id"), nullable=False)
    
    # Mastery parameters
    alpha = Column(Float, nullable=False)
    beta = Column(Float, nullable=False)
    mastery_mean = Column(Float, nullable=False)
    uncertainty = Column(Float, nullable=False)
    
    # Additional metrics
    total_samples = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=True)
    
    # Context
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=True)
    snapshot_type = Column(String, default="periodic")  # "periodic", "after_interaction", "manual"
    
    # Relationships
    user = relationship("User", back_populates="mastery_snapshots")
    concept = relationship("Concept", back_populates="mastery_snapshots")
    
    def __repr__(self):
        return f"<MasterySnapshot(user_id={self.user_id}, concept_id={self.concept_id}, mastery={self.mastery_mean:.3f})>"

class RepresentationEffectiveness(Base):
    """Representation effectiveness model for tracking representation performance"""
    __tablename__ = "representation_effectiveness"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    concept_id = Column(String, ForeignKey("concepts.id"), nullable=False)
    representation = Column(String, nullable=False)
    
    # Effectiveness parameters
    alpha = Column(Float, nullable=False)
    beta = Column(Float, nullable=False)
    mean_effectiveness = Column(Float, nullable=False)
    uncertainty = Column(Float, nullable=False)
    
    # Metrics
    total_samples = Column(Integer, nullable=False)
    total_reward = Column(Float, nullable=False)
    average_reward = Column(Float, nullable=True)
    
    # System metadata
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RepresentationEffectiveness(user_id={self.user_id}, concept={self.concept_id}, rep={self.representation})>"

class LearningSession(Base):
    """Learning session model for tracking user sessions"""
    __tablename__ = "learning_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session data
    session_start = Column(DateTime, nullable=False)
    session_end = Column(DateTime, nullable=True)
    total_interactions = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)
    average_response_time = Column(Float, default=0.0)
    
    # Session metrics
    total_reward = Column(Float, default=0.0)
    average_reward = Column(Float, default=0.0)
    mastery_improvement = Column(Float, default=0.0)
    
    # Context
    policy_mode = Column(String, nullable=False)
    device_type = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Additional metadata
    interaction_metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<LearningSession(user_id={self.user_id}, interactions={self.total_interactions})>"

class SystemEvent(Base):
    """System event model for logging system events"""
    __tablename__ = "system_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Event data
    event_type = Column(String, nullable=False)
    event_source = Column(String, nullable=False)
    event_level = Column(String, default="INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # Event details
    user_id = Column(UUID(as_uuid=True), nullable=True)
    concept_id = Column(String, nullable=True)
    message = Column(Text, nullable=True)
    
    # Event data
    event_data = Column(JSON, default=dict)
    
    # Performance metrics
    processing_time_ms = Column(Float, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<SystemEvent(type={self.event_type}, level={self.event_level})>"

class AnalyticsAggregation(Base):
    """Analytics aggregation model for storing aggregated analytics data"""
    __tablename__ = "analytics_aggregations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Aggregation metadata
    aggregation_type = Column(String, nullable=False)  # "daily", "weekly", "monthly"
    aggregation_period = Column(String, nullable=False)  # "2024-01-01", "2024-W01", "2024-01"
    
    # User metrics
    total_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    
    # Interaction metrics
    total_interactions = Column(Integer, default=0)
    correct_interactions = Column(Integer, default=0)
    average_correctness = Column(Float, default=0.0)
    average_response_time = Column(Float, default=0.0)
    
    # Learning metrics
    average_mastery = Column(Float, default=0.0)
    mastery_improvement = Column(Float, default=0.0)
    total_concepts_mastered = Column(Integer, default=0)
    
    # System metrics
    average_reward = Column(Float, default=0.0)
    policy_distribution = Column(JSON, default=dict)
    representation_distribution = Column(JSON, default=dict)
    
    # Additional data
    event_data = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<AnalyticsAggregation(type={self.aggregation_type}, period={self.aggregation_period})>"
