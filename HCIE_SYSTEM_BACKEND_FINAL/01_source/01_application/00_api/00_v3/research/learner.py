"""
Learner research API.

Read-only Slice 3 surface over projection and trajectory read models.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.services.projection.learner_research_projection import (
    LearnerResearchProjection,
)
from storage.postgres_store.interaction_store import PostgresInteractionStore


router = APIRouter(
    prefix="/research/learner/{user_id}",
    tags=["research-learner"],
)

learner_research_router = router


def get_learner_research_projection() -> LearnerResearchProjection:
    return LearnerResearchProjection(PostgresInteractionStore())


@router.get("/governance/state")
async def governance_state(
    user_id: str,
    projection: LearnerResearchProjection = Depends(get_learner_research_projection),
) -> Dict[str, Any]:
    return projection.governance_state(user_id)


@router.get("/governance/trajectory")
async def governance_trajectory(
    user_id: str,
    limit: int = Query(500, ge=1, le=5000),
    projection: LearnerResearchProjection = Depends(get_learner_research_projection),
) -> Dict[str, Any]:
    return projection.governance_trajectory(user_id, limit=limit)


@router.get("/governance/ensemble-weights")
async def governance_ensemble_weights(
    user_id: str,
    limit: int = Query(500, ge=1, le=5000),
    projection: LearnerResearchProjection = Depends(get_learner_research_projection),
) -> Dict[str, Any]:
    return projection.ensemble_weights(user_id, limit=limit)


@router.get("/adaptation/trajectory")
async def adaptation_trajectory(
    user_id: str,
    projection: LearnerResearchProjection = Depends(get_learner_research_projection),
) -> Dict[str, Any]:
    return projection.adaptation_trajectory(user_id)


@router.get("/jt-attribution")
async def jt_attribution(
    user_id: str,
    limit: int = Query(500, ge=1, le=5000),
    projection: LearnerResearchProjection = Depends(get_learner_research_projection),
) -> Dict[str, Any]:
    return projection.jt_attribution(user_id, limit=limit)


@router.get("/discriminability")
async def discriminability(
    user_id: str,
    limit: int = Query(500, ge=1, le=5000),
    projection: LearnerResearchProjection = Depends(get_learner_research_projection),
) -> Dict[str, Any]:
    return projection.discriminability(user_id, limit=limit)


@router.get("/bandit-state")
async def bandit_state(
    user_id: str,
    limit: int = Query(500, ge=1, le=5000),
    projection: LearnerResearchProjection = Depends(get_learner_research_projection),
) -> Dict[str, Any]:
    return projection.bandit_state(user_id, limit=limit)


@router.get("/representation-arms")
async def representation_arms(
    user_id: str,
    concept_id: Optional[str] = Query(None),
    projection: LearnerResearchProjection = Depends(get_learner_research_projection),
) -> Dict[str, Any]:
    """Live per-modality Beta(alpha, beta) arms for the representation bandit."""
    return projection.representation_arms(user_id, concept_id=concept_id)


@router.get("/ranking")
async def ranking(
    user_id: str,
    limit: int = Query(500, ge=1, le=5000),
    projection: LearnerResearchProjection = Depends(get_learner_research_projection),
) -> Dict[str, Any]:
    return projection.ranking(user_id, limit=limit)


@router.get("/trajectory.csv")
async def trajectory_csv(
    user_id: str,
    limit: int = Query(500, ge=1, le=5000),
    projection: LearnerResearchProjection = Depends(get_learner_research_projection),
) -> Response:
    return Response(
        content=projection.trajectory_csv(user_id, limit=limit),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{user_id}-trajectory.csv"',
        },
    )
