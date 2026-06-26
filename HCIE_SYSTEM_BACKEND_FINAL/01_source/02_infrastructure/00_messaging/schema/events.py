"""
Kafka Event Schemas for HCIE System
Defines the structure of all events published/consumed by the system
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    """Event types for HCIE system"""
    TASK_GENERATED = "task_generated"
    TASK_SUBMITTED = "task_submitted"
    MASTERY_UPDATED = "mastery_updated"
    POLICY_EXECUTED = "policy_executed"
    REWARD_CALCULATED = "reward_calculated"
    USER_SESSION_STARTED = "user_session_started"
    USER_SESSION_ENDED = "user_session_ended"
    SYSTEM_HEALTH_CHECK = "system_health_check"
    # Auth events
    USER_REGISTERED = "user_registered"
    USER_LOGGED_IN = "user_logged_in"
    TOKEN_REFRESHED = "token_refreshed"
    USER_PROFILE_UPDATED = "user_profile_updated"
    USER_LOGGED_OUT = "user_logged_out"
    PASSWORD_CHANGED = "password_changed"

class BaseEvent(BaseModel):
    """Base event schema"""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(..., description="Event timestamp")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    source: str = Field(..., description="Event source service")
    version: str = Field("1.0", description="Event schema version")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TaskGeneratedEvent(BaseEvent):
    """Event when a new task is generated for a user"""
    event_type: EventType = EventType.TASK_GENERATED
    task_id: str = Field(..., description="Generated task ID")
    concept_id: str = Field(..., description="Selected concept")
    representation: str = Field(..., description="Task representation")
    difficulty: float = Field(..., description="Task difficulty")
    policy_mode: str = Field(..., description="Policy used for selection")
    selection_metrics: Dict[str, Any] = Field(..., description="Selection metrics")
    processing_time_ms: float = Field(..., description="Time to generate task")

class TaskSubmittedEvent(BaseEvent):
    """Event when a user submits a task"""
    event_type: EventType = EventType.TASK_SUBMITTED
    task_id: str = Field(..., description="Submitted task ID")
    concept_id: str = Field(..., description="Task concept")
    representation: str = Field(..., description="Task representation")
    answer: str = Field(..., description="User's answer")
    correct_answer: str = Field(..., description="Correct answer")
    correct: bool = Field(..., description="Whether answer was correct")
    response_time: float = Field(..., description="Time taken to answer")
    difficulty: float = Field(..., description="Task difficulty")
    reward: float = Field(..., description="Calculated reward")

class MasteryUpdatedEvent(BaseEvent):
    """Event when user mastery is updated"""
    event_type: EventType = EventType.MASTERY_UPDATED
    concept_id: str = Field(..., description="Updated concept")
    previous_mastery: float = Field(..., description="Previous mastery level")
    new_mastery: float = Field(..., description="New mastery level")
    mastery_change: float = Field(..., description="Change in mastery")
    uncertainty: float = Field(..., description="Current uncertainty")
    transferred_nodes: int = Field(..., description="Number of transferred nodes")

class PolicyExecutedEvent(BaseEvent):
    """Event when a policy decision is executed"""
    event_type: EventType = EventType.POLICY_EXECUTED
    policy_mode: str = Field(..., description="Policy mode used")
    available_concepts: List[str] = Field(..., description="Available concepts")
    selected_concept: str = Field(..., description="Selected concept")
    policy_score: float = Field(..., description="Policy score")
    context: Dict[str, Any] = Field(..., description="Decision context")

class RewardCalculatedEvent(BaseEvent):
    """Event when reward is calculated"""
    event_type: EventType = EventType.REWARD_CALCULATED
    task_id: str = Field(..., description="Task ID")
    user_id: str = Field(..., description="User ID")
    concept_id: str = Field(..., description="Concept ID")
    correct: bool = Field(..., description="Whether answer was correct")
    response_time: float = Field(..., description="Response time")
    difficulty: float = Field(..., description="Task difficulty")
    reward: float = Field(..., description="Calculated reward")
    reward_components: Dict[str, float] = Field(..., description="Reward breakdown")

class UserSessionStartedEvent(BaseEvent):
    """Event when a user session starts"""
    event_type: EventType = EventType.USER_SESSION_STARTED
    user_agent: Optional[str] = Field(None, description="User agent string")
    ip_address: Optional[str] = Field(None, description="User IP address")
    initial_context: Dict[str, Any] = Field(default_factory=dict, description="Initial session context")

class UserSessionEndedEvent(BaseEvent):
    """Event when a user session ends"""
    event_type: EventType = EventType.USER_SESSION_ENDED
    session_duration: float = Field(..., description="Session duration in seconds")
    total_interactions: int = Field(..., description="Total interactions in session")
    final_context: Dict[str, Any] = Field(default_factory=dict, description="Final session context")

class SystemHealthCheckEvent(BaseEvent):
    """Event for system health monitoring"""
    event_type: EventType = EventType.SYSTEM_HEALTH_CHECK
    service_name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    metrics: Dict[str, Any] = Field(..., description="Health metrics")
    checks: Dict[str, bool] = Field(..., description="Individual check results")

# Auth Events
class UserRegisteredEvent(BaseEvent):
    """Event when a user registers"""
    event_type: EventType = EventType.USER_REGISTERED
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    role: str = Field(..., description="User role")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    experiment_group: Optional[str] = Field(None, description="Experiment group assignment")

class UserLoggedInEvent(BaseEvent):
    """Event when a user logs in"""
    event_type: EventType = EventType.USER_LOGGED_IN
    email: str = Field(..., description="User email")
    login_method: str = Field(..., description="Login method (password, token, etc.)")
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")

class TokenRefreshedEvent(BaseEvent):
    """Event when a token is refreshed"""
    event_type: EventType = EventType.TOKEN_REFRESHED
    email: str = Field(..., description="User email")
    token_id: Optional[str] = Field(None, description="Token ID")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")

class UserProfileUpdatedEvent(BaseEvent):
    """Event when a user profile is updated"""
    event_type: EventType = EventType.USER_PROFILE_UPDATED
    email: str = Field(..., description="User email")
    updated_fields: Dict[str, Any] = Field(..., description="Fields that were updated")

class UserLoggedOutEvent(BaseEvent):
    """Event when a user logs out"""
    event_type: EventType = EventType.USER_LOGGED_OUT
    email: str = Field(..., description="User email")
    session_duration: Optional[float] = Field(None, description="Session duration in seconds")

class PasswordChangedEvent(BaseEvent):
    """Event when a user changes password"""
    event_type: EventType = EventType.PASSWORD_CHANGED
    email: str = Field(..., description="User email")
    changed_at: datetime = Field(..., description="When password was changed")
    method: str = Field(..., description="How password was changed")
