"""
Response models for API endpoints
Pydantic models for response formatting
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union

class TaskResponse(BaseModel):
    """Task response model"""
    user_id: str = Field(..., description="User identifier")
    task_id: str = Field(..., description="Task identifier")
    node_id: str = Field(..., description="Concept/node identifier")
    representation: str = Field(..., description="Task representation type")
    question: str = Field(..., description="Task question/prompt")
    difficulty: float = Field(..., description="Task difficulty level")
    selection_metrics: Dict[str, Union[float, str, int]] = Field(..., description="Task selection metrics")
    timestamp: float = Field(..., description="Task generation timestamp")
    real_data: bool = Field(..., description="Whether real EdNet data was used")

class TaskSubmissionResponse(BaseModel):
    """Task submission response model"""
    success: bool = Field(..., description="Whether submission was successful")
    correct: bool = Field(..., description="Whether answer was correct")
    reward: float = Field(..., description="Calculated reward")
    response_time: float = Field(..., description="Response time in seconds")
    difficulty: float = Field(..., description="Task difficulty")
    learning_metrics: Dict[str, Any] = Field(..., description="Learning progress metrics")
    timestamp: float = Field(..., description="Submission timestamp")
    real_data: bool = Field(..., description="Whether real processing was used")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Overall system status")
    services: Dict[str, bool] = Field(..., description="Service status indicators")
    environment: Optional[Dict[str, Any]] = Field(None, description="Environment information")
    timestamp: Optional[str] = Field(None, description="Health check timestamp")

class UserHistoryResponse(BaseModel):
    """User task history response model"""
    user_id: str = Field(..., description="User identifier")
    history: list = Field(..., description="List of task interactions")
    total: int = Field(..., description="Total number of interactions")

class AnalyticsResponse(BaseModel):
    """Analytics data response model"""
    metric_type: str = Field(..., description="Type of analytics data")
    data: Dict[str, Any] = Field(..., description="Analytics data")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")
    timestamp: float = Field(..., description="Response timestamp")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: float = Field(..., description="Error timestamp")
    status_code: int = Field(..., description="HTTP status code")
