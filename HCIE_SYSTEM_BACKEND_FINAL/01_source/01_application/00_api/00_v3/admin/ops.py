"""Slice 4b admin operations and observability endpoints."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies.rbac import require_admin
from storage.postgres_store.interaction_store import PostgresInteractionStore


router = APIRouter(prefix="/admin", tags=["v3-admin-ops"])


class ProjectionRebuildRequest(BaseModel):
    reason: str
    limit: int = 1000


class ResetNormalizationRequest(BaseModel):
    reason: str


def _store() -> PostgresInteractionStore:
    return PostgresInteractionStore()


def _ensure_audit_table(store: PostgresInteractionStore) -> None:
    store.execute_write(
        """
        CREATE TABLE IF NOT EXISTS admin_audit_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            reason TEXT,
            prior_state JSONB NOT NULL DEFAULT '{}'::jsonb,
            result JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        (),
    )


def _audit(
    store: PostgresInteractionStore,
    *,
    actor: str,
    action: str,
    reason: str,
    prior_state: Dict[str, Any],
    result: Dict[str, Any],
) -> None:
    _ensure_audit_table(store)
    store.execute_write(
        """
        INSERT INTO admin_audit_log (actor, action, reason, prior_state, result)
        VALUES (%s, %s, %s, %s::jsonb, %s::jsonb)
        """,
        (
            actor,
            action,
            reason,
            json.dumps(prior_state, default=str),
            json.dumps(result, default=str),
        ),
    )


def _actor(admin: Dict[str, Any]) -> str:
    return str(admin.get("email") or admin.get("id") or admin.get("user_id") or "admin")


@router.get("/health/detail")
async def health_detail(_admin: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    store = _store()
    postgres = bool(store.execute_read("SELECT 1 AS ok", fetch_one=True))
    redis = False
    try:
        from storage.redis_store.redis_store import RedisFeatureStore

        client = RedisFeatureStore()._ensure_connected()
        redis = bool(client and client.ping())
    except Exception:
        redis = False
    outbox = store.execute_read(
        "SELECT COUNT(*) AS pending FROM outbox_event_envelopes WHERE status = 'pending'",
        fetch_one=True,
    ) or {"pending": None}
    projection = store.execute_read(
        "SELECT COUNT(*) AS rows, MAX(updated_at) AS latest FROM learner_projections",
        fetch_one=True,
    ) or {"rows": 0, "latest": None}
    return {
        "status": "ok" if postgres else "degraded",
        "postgres": postgres,
        "redis": redis,
        "outbox": outbox,
        "projection": projection,
        "semantic_version": "1.0",
    }


@router.get("/outbox/status")
async def outbox_status(_admin: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    rows = _store().execute_read(
        """
        SELECT status, COUNT(*) AS count, MAX(published_at) AS last_published_at
        FROM outbox_event_envelopes
        GROUP BY status
        ORDER BY status
        """
    )
    return {"status": "ok", "buckets": rows or [], "semantic_version": "1.0"}


@router.get("/kafka/topics")
async def kafka_topics(_admin: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    try:
        from kafka import KafkaAdminClient

        bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        client = KafkaAdminClient(bootstrap_servers=bootstrap, request_timeout_ms=3000)
        topics = sorted(client.list_topics())
        client.close()
        return {"status": "ok", "topics": topics, "bootstrap": bootstrap, "semantic_version": "1.0"}
    except Exception as exc:
        return {"status": "degraded", "error": str(exc), "topics": [], "semantic_version": "1.0"}


@router.get("/projection/status")
async def projection_status(_admin: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    row = _store().execute_read(
        """
        SELECT COUNT(*) AS rows, MAX(updated_at) AS latest_updated_at,
               COUNT(DISTINCT user_id) AS users
        FROM learner_projections
        """,
        fetch_one=True,
    ) or {"rows": 0, "latest_updated_at": None, "users": 0}
    return {
        "status": "ok",
        "authority": "learner_projections",
        "projection": row,
        "semantic_version": "1.0",
    }


@router.post("/projection/rebuild")
async def projection_rebuild(
    body: ProjectionRebuildRequest,
    admin: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    """Audited rebuild from persisted `learning_analytics` envelopes only."""

    store = _store()
    before = store.execute_read(
        "SELECT COUNT(*) AS rows, MAX(updated_at) AS latest FROM learner_projections",
        fetch_one=True,
    ) or {}
    rows = store.execute_read(
        """
        SELECT envelope
        FROM outbox_event_envelopes
        WHERE topic = 'learning_analytics'
        ORDER BY created_at ASC
        LIMIT %s
        """,
        (body.limit,),
    ) or []
    rebuilt = 0
    try:
        from app.workers.projection_consumer import ProjectionConsumerService

        consumer = ProjectionConsumerService()
        if not consumer.initialize():
            raise RuntimeError("projection_consumer_initialize_failed")
        for row in rows:
            envelope = row.get("envelope") or {}
            payload = envelope.get("payload", envelope) if isinstance(envelope, dict) else {}
            event_type = payload.get("event_type") or envelope.get("event_type")
            if event_type == "CognitionUpdated" and consumer.process_cognition_event(payload):
                rebuilt += 1
            elif event_type == "AdaptationGenerated" and consumer.process_adaptation_event(payload):
                rebuilt += 1
    except Exception as exc:
        result = {"status": "failed", "error": str(exc), "events_seen": len(rows), "rebuilt": rebuilt}
        _audit(
            store,
            actor=_actor(admin),
            action="projection.rebuild",
            reason=body.reason,
            prior_state=before,
            result=result,
        )
        raise HTTPException(status_code=503, detail=result) from exc

    result = {"status": "ok", "events_seen": len(rows), "rebuilt": rebuilt}
    _audit(
        store,
        actor=_actor(admin),
        action="projection.rebuild",
        reason=body.reason,
        prior_state=before,
        result=result,
    )
    return {**result, "authority": "learning_analytics", "semantic_version": "1.0"}


@router.get("/runtime/services")
async def runtime_services(_admin: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    try:
        from app.infrastructure.di.get_container import get_container

        container = get_container()
        bindings = sorted(getattr(container, "_bindings", {}).keys())
        return {"status": "ok", "services": bindings, "semantic_version": "1.0"}
    except Exception as exc:
        return {"status": "degraded", "error": str(exc), "services": [], "semantic_version": "1.0"}


@router.get("/observability/links")
async def observability_links(_admin: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    host = os.getenv("HCIE_OBSERVABILITY_HOST", "localhost")
    return {
        "status": "ok",
        "links": {
            "grafana": f"http://{host}:3000",
            "prometheus": f"http://{host}:9090",
            "loki": f"http://{host}:3100",
            "pyroscope": f"http://{host}:4040",
            "alertmanager": f"http://{host}:9093",
            "dozzle": f"http://{host}:9999",
        },
        "semantic_version": "1.0",
    }


@router.post("/governance/reset-normalization")
async def reset_governance_normalization(
    body: ResetNormalizationRequest,
    admin: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    store = _store()
    try:
        from app.infrastructure.di.get_container import get_container

        brain = get_container().unified_brain()
        governance = getattr(brain, "jt_governance", None)
        prior = {
            "normalization_state": getattr(governance, "normalization_state", None),
            "component_stats": getattr(governance, "component_stats", None),
        }
        if not governance or not hasattr(governance, "reset_normalization_state"):
            raise RuntimeError("governance_reset_not_available")
        governance.reset_normalization_state()
        result = {"status": "ok", "reset_at": datetime.utcnow().isoformat() + "Z"}
    except Exception as exc:
        result = {"status": "failed", "error": str(exc)}
        _audit(
            store,
            actor=_actor(admin),
            action="governance.reset_normalization",
            reason=body.reason,
            prior_state={},
            result=result,
        )
        raise HTTPException(status_code=503, detail=result) from exc

    _audit(
        store,
        actor=_actor(admin),
        action="governance.reset_normalization",
        reason=body.reason,
        prior_state=prior,
        result=result,
    )
    return {**result, "semantic_version": "1.0"}


@router.get("/container/services")
async def container_services(_admin: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    return await runtime_services(_admin)
