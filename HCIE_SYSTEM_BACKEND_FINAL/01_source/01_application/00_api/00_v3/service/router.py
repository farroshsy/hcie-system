"""Slice 4c internal service endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies.service import require_service_token
from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
from storage.postgres_store.interaction_store import PostgresInteractionStore


router = APIRouter(prefix="/service", tags=["v3-service"])


class EventIngestRequest(BaseModel):
    event_type: str = "UserInteractionSubmitted"
    topic: str = "user-interactions"
    payload: Dict[str, Any]
    event_id: Optional[str] = None


class BatchReplayRequest(BaseModel):
    experiment_run_id: str
    num_users: int = Field(default=10, ge=1, le=1000)


def _postgres() -> PostgresInteractionStore:
    return PostgresInteractionStore()


@router.post("/events/ingest")
async def ingest_event(
    body: EventIngestRequest,
    _service: Dict[str, str] = Depends(require_service_token),
) -> Dict[str, Any]:
    """Persist an external event into the canonical outbox path."""

    event_id = body.event_id or str(uuid.uuid4())
    store = _postgres()
    outbox = get_outbox_pattern(store)
    event = outbox.create_event(
        event_id=event_id,
        event_type=body.event_type,
        topic=body.topic,
        payload={
            **body.payload,
            "event_id": event_id,
            "event_type": body.event_type,
            "source": body.payload.get("source", "v3_service_ingest"),
            "timestamp": body.payload.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            "ingested_at": datetime.utcnow().isoformat() + "Z",
        },
    )
    try:
        outbox.save_event(event)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail={"reason": "invalid_event_for_outbox_schema", "error": str(exc)},
        ) from exc
    return {
        "status": "accepted",
        "event_id": event_id,
        "topic": body.topic,
        "authority": "outbox_event_envelopes",
        "semantic_version": "1.0",
    }


def _batch_replay(experiment_run_id: str, num_users: int) -> Dict[str, Any]:
    try:
        from app.infrastructure.di.get_container import get_container
        from infrastructure.experiment.replay_engine import ReplayEngine
        from infrastructure.experiment.trajectory_recorder import TrajectoryRecorder

        store = _postgres()
        # Stage 0 backstop (reject mode): never write into a sealed run. The
        # friendly 409 + continuation handoff is at the replay endpoint; this
        # guard catches any other caller of _batch_replay. No-op for normal runs.
        from app.api.v3.experiments.run_sealing import assert_writable
        assert_writable(store, experiment_run_id)
        recorder = TrajectoryRecorder(store)
        brain = get_container().unified_brain()
        return ReplayEngine(brain, recorder).batch_replay(
            experiment_run_id=experiment_run_id,
            num_users=num_users,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/replay/batch")
async def replay_batch(
    body: BatchReplayRequest,
    _service: Dict[str, str] = Depends(require_service_token),
) -> Dict[str, Any]:
    """Run ReplayEngine batch replay through the service-token surface."""

    result = _batch_replay(body.experiment_run_id, body.num_users)
    return {
        "status": "ok",
        "experiment_run_id": body.experiment_run_id,
        "result": result,
        "semantic_version": "1.0",
    }


@router.post("/projection/rebuild")
async def projection_rebuild_service_alias(
    _service: Dict[str, str] = Depends(require_service_token),
) -> Dict[str, Any]:
    """Service route is intentionally non-authoritative for rebuilds."""

    raise HTTPException(
        status_code=409,
        detail={
            "reason": "admin_rebuild_required",
            "canonical_path": "/v3/admin/projection/rebuild",
            "authority": "admin_audited_projection_rebuild",
        },
    )
