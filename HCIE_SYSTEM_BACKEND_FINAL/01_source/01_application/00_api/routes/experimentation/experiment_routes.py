"""
Experimentation API Routes

API endpoints for managing pedagogical experiments and assignments.
Supports experiment lifecycle, cohort assignment, and evaluation metrics.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.experiment.experiment_registry import (
    ExperimentRegistry,
    Experiment,
    ExperimentStatus,
    ExperimentType,
    get_experiment_registry
)

router = APIRouter(prefix="/api/experiments", tags=["experimentation"])


class CreateExperimentRequest(BaseModel):
    """Request to create a new experiment"""
    experiment_id: str
    name: str
    description: str
    hypothesis: str
    experiment_type: str
    policy_versions: List[str]
    cohort_criteria: Dict[str, Any]
    rollout_percentage: float
    start_date: str  # ISO format
    end_date: Optional[str] = None
    evaluation_metrics: Optional[List[str]] = None
    replay_compatible: bool = True
    metadata: Optional[Dict[str, Any]] = None


class ExperimentResponse(BaseModel):
    """Experiment response model"""
    experiment_id: str
    name: str
    description: str
    hypothesis: str
    experiment_type: str
    policy_versions: List[str]
    cohort_criteria: Dict[str, Any]
    rollout_percentage: float
    start_date: str
    end_date: Optional[str]
    status: str
    evaluation_metrics: List[str]
    replay_compatible: bool
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class AssignmentResponse(BaseModel):
    """User assignment response"""
    user_id: str
    experiment_id: Optional[str]
    policy_version: Optional[str]
    assigned_at: Optional[str]


@router.post("/", response_model=ExperimentResponse)
async def create_experiment(request: CreateExperimentRequest) -> ExperimentResponse:
    """
    Create a new pedagogical experiment.
    
    This registers an experiment hypothesis for validation.
    Experiments must be replay-compatible to support counterfactual analysis.
    """
    registry = get_experiment_registry()
    
    # Validate experiment type
    try:
        exp_type = ExperimentType(request.experiment_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid experiment_type: {request.experiment_type}")
    
    # Parse dates
    try:
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date) if request.end_date else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")
    
    # Validate rollout percentage
    if not 0.0 <= request.rollout_percentage <= 1.0:
        raise HTTPException(status_code=400, detail="rollout_percentage must be between 0.0 and 1.0")
    
    # Create experiment
    experiment = Experiment(
        experiment_id=request.experiment_id,
        name=request.name,
        description=request.description,
        hypothesis=request.hypothesis,
        experiment_type=exp_type,
        policy_versions=request.policy_versions,
        cohort_criteria=request.cohort_criteria,
        rollout_percentage=request.rollout_percentage,
        start_date=start_date,
        end_date=end_date,
        status=ExperimentStatus.DRAFT,
        evaluation_metrics=request.evaluation_metrics or [],
        replay_compatible=request.replay_compatible,
        metadata=request.metadata or {}
    )
    
    # Register experiment
    if not registry.register_experiment(experiment):
        raise HTTPException(status_code=409, detail=f"Experiment {request.experiment_id} already exists")
    
    return ExperimentResponse(**experiment.to_dict())


@router.get("/", response_model=List[ExperimentResponse])
async def list_experiments(
    status: Optional[str] = None,
    experiment_type: Optional[str] = None
) -> List[ExperimentResponse]:
    """
    List all experiments with optional filtering.
    
    Query parameters:
    - status: Filter by experiment status (draft, active, paused, completed, archived)
    - experiment_type: Filter by experiment type
    """
    registry = get_experiment_registry()
    
    # Parse filters
    status_filter = ExperimentStatus(status) if status else None
    type_filter = ExperimentType(experiment_type) if experiment_type else None
    
    experiments = registry.list_experiments(
        status=status_filter,
        experiment_type=type_filter
    )
    
    return [ExperimentResponse(**exp.to_dict()) for exp in experiments]


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(experiment_id: str) -> ExperimentResponse:
    """Get experiment details by ID"""
    registry = get_experiment_registry()
    experiment = registry.get_experiment(experiment_id)
    
    if not experiment:
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found")
    
    return ExperimentResponse(**experiment.to_dict())


@router.put("/{experiment_id}/status")
async def update_experiment_status(
    experiment_id: str,
    new_status: str
) -> Dict[str, Any]:
    """
    Update experiment lifecycle status.
    
    Valid statuses: draft, active, paused, completed, archived
    """
    registry = get_experiment_registry()
    
    try:
        status = ExperimentStatus(new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
    
    if not registry.update_experiment_status(experiment_id, status):
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found")
    
    return {
        "success": True,
        "experiment_id": experiment_id,
        "new_status": new_status
    }


@router.get("/assignment/{user_id}", response_model=AssignmentResponse)
async def get_user_assignment(
    user_id: str,
    experiment_seed: Optional[str] = None
) -> AssignmentResponse:
    """
    Get current experiment and policy assignment for a user.
    
    This uses deterministic hashing to ensure replay compatibility:
    Same user_id + same experiment_seed → same assignment.
    
    Query parameters:
    - experiment_seed: Optional seed for deterministic assignment (e.g., date, experiment_id)
    """
    registry = get_experiment_registry()
    
    assignment = registry.get_user_assignment(user_id)
    
    if not assignment:
        return AssignmentResponse(
            user_id=user_id,
            experiment_id=None,
            policy_version=None,
            assigned_at=None
        )
    
    return AssignmentResponse(
        user_id=user_id,
        experiment_id=assignment["experiment_id"],
        policy_version=assignment["policy_version"],
        assigned_at=datetime.utcnow().isoformat()
    )


@router.get("/{experiment_id}/lineage")
async def get_experiment_lineage(experiment_id: str) -> Dict[str, Any]:
    """
    Get experiment lineage for replay and analysis.
    
    Returns experiment metadata, assignment counts, and policy distribution.
    Critical for validating replay determinism and cohort analysis.
    """
    registry = get_experiment_registry()
    lineage = registry.get_experiment_lineage(experiment_id)
    
    if not lineage:
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found")
    
    return lineage


@router.post("/{experiment_id}/metrics")
async def record_experiment_metric(
    experiment_id: str,
    user_id: str,
    metric_name: str,
    metric_value: float,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record evaluation metric for experiment.
    
    This is a simplified version - production would need proper metrics storage.
    For now, metrics are logged for validation.
    
    Body parameters:
    - user_id: Learner identifier
    - metric_name: Name of the metric (e.g., "mastery_gain", "pacing_stability")
    - metric_value: Numeric metric value
    - timestamp: Optional ISO timestamp (defaults to current time)
    """
    registry = get_experiment_registry()
    
    # Parse timestamp
    parsed_timestamp = None
    if timestamp:
        try:
            parsed_timestamp = datetime.fromisoformat(timestamp)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO format.")
    
    if not registry.record_experiment_metric(
        experiment_id, user_id, metric_name, metric_value, parsed_timestamp
    ):
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found")
    
    return {
        "success": True,
        "experiment_id": experiment_id,
        "user_id": user_id,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "recorded_at": (parsed_timestamp or datetime.utcnow()).isoformat()
    }
