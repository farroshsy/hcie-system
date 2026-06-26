"""
Request models for API endpoints
Pydantic models for request validation
"""

from pydantic import BaseModel, Field
from typing import Optional

class TaskSubmission(BaseModel):
    """Task submission request model"""
    user_id: str = Field(..., description="User identifier")
    task_id: str = Field(..., description="Task identifier")
    node_id: str = Field(..., description="Concept/node identifier")
    representation: str = Field(..., description="Task representation type")
    answer: str = Field(..., description="User's answer")
    response_time: float = Field(..., description="Time taken to answer in seconds")
    mode: str = Field(default="hcie", description="Policy mode (ct, hcie, dag, random)")
    difficulty: float = Field(default=0.5, description="Task difficulty level")
    beta: float = Field(default=0.5, description="Transfer learning beta parameter")
    learner_mode: str = Field(default="lyapunov", description="Learning model (lyapunov, bayesian, kalman)")
    force_correct: Optional[bool] = Field(default=None, description="Force correctness for research experiments")
    prior_mastery: Optional[float] = Field(default=None, description="Override initial mastery for controlled experiments")

class TaskRequest(BaseModel):
    """Task generation request model"""
    user_id: str = Field(..., description="User identifier")
    policy_mode: Optional[str] = Field("hcie", description="Policy mode to use")
    difficulty_range: Optional[tuple[float, float]] = Field(None, description="Difficulty range filter")
    concept_filter: Optional[list[str]] = Field(None, description="Concept filter")

class UserSessionRequest(BaseModel):
    """User session management request"""
    user_id: str = Field(..., description="User identifier")
    session_data: Optional[dict] = Field(None, description="Session metadata")

class AnalyticsRequest(BaseModel):
    """Analytics data request"""
    metric_type: str = Field(..., description="Type of analytics data requested")
    user_id: Optional[str] = Field(None, description="User ID for user-specific analytics")
    date_range: Optional[tuple[str, str]] = Field(None, description="Date range for analytics")
    filters: Optional[dict] = Field(None, description="Additional filters")
