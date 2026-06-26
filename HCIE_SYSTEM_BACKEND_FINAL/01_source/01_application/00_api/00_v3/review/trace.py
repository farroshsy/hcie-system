"""
ADC Review API — governance trace and interaction-level detail.

Read-only surface over experiment_trajectories for the public review portal.
No auth required: all data is frozen research evidence, not user PII.
Authority State: authoritative (frozen sealed data, 2026-05-26)
"""

import json
import math
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from storage.postgres_store.interaction_store import PostgresInteractionStore


router = APIRouter(prefix="/review", tags=["review"])
review_router = router

_SEALED_RUN_IDS = {
    "phase1": "run-217532ca-39e6-4859-a41f-88ed53e904a2",
    "phase2": "run-94a3b8ba-015b-4d84-b288-004fe60bc282",
    "r12":    "run-aecd9059-aac1-4800-b738-d508eef79608",
}

_TRACE_USER = "run-94a3b8ba-015b-4d84-b288-004fe60bc282::ex_junyi_graph_135350"


def _store() -> PostgresInteractionStore:
    return PostgresInteractionStore()


def _read(store: PostgresInteractionStore, query: str, params: tuple = (), fetch_one: bool = False):
    try:
        return store.execute_read(query, params, fetch_one=fetch_one)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DB read failed: {exc}")


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except Exception:
        return None


def _jsonish(v: Any) -> Any:
    if v is None:
        return {}
    if isinstance(v, (dict, list)):
        return v
    try:
        return json.loads(v)
    except Exception:
        return v


@router.get("/health")
async def review_health() -> Dict[str, Any]:
    """Liveness check for the review API surface."""
    return {"status": "ok", "sealed_run_ids": _SEALED_RUN_IDS}


@router.get("/trace")
async def get_canonical_trace(
    limit: int = Query(100, ge=1, le=500),
) -> Dict[str, Any]:
    """
    Full governance trace for the canonical ADC demo learner
    (ex_junyi_graph_135350, Phase 2 run, 100 interactions).

    Returns the same data as governance_trace.json but live from DB.
    """
    store = _store()
    rows = _read(
        store,
        """
        SELECT
            interaction_number,
            concept,
            mastery_before,
            mastery_after,
            correctness,
            jt_value,
            jt_delta_m_contribution,
            jt_challenge_contribution,
            jt_uncertainty_contribution,
            jt_zpd_contribution,
            jt_transfer_contribution,
            transfer_amount,
            transfer_amounts_json,
            jt_attribution,
            event_id
        FROM experiment_trajectories
        WHERE user_id = %s
        ORDER BY interaction_number ASC
        LIMIT %s
        """,
        (_TRACE_USER, limit),
    )
    if not rows:
        # Reaching here means the query SUCCEEDED but returned 0 rows (a genuine
        # SQL/column error would have been raised as 503 by _read above). So the
        # canonical trace user simply has no rows in experiment_trajectories.
        raise HTTPException(
            status_code=404,
            detail=f"No trace rows for canonical user {_TRACE_USER!r} in experiment_trajectories",
        )

    trace = []
    for row in rows:
        r = dict(row)
        trace.append({
            "interaction_number": r.get("interaction_number"),
            "concept":            r.get("concept"),
            "mastery_before":     _safe_float(r.get("mastery_before")),
            "mastery_after":      _safe_float(r.get("mastery_after")),
            "correct":            bool(r.get("correctness")),
            "jt_value":           _safe_float(r.get("jt_value")),
            "jt_transfer_contribution":   _safe_float(r.get("jt_transfer_contribution")),
            "jt_delta_m_contribution":    _safe_float(r.get("jt_delta_m_contribution")),
            "jt_challenge_contribution":  _safe_float(r.get("jt_challenge_contribution")),
            "jt_uncertainty_contribution":_safe_float(r.get("jt_uncertainty_contribution")),
            "jt_zpd_contribution":        _safe_float(r.get("jt_zpd_contribution")),
            "transfer_amount_raw":        _safe_float(r.get("transfer_amount")),
            "transfer_amounts_json":      _jsonish(r.get("transfer_amounts_json")),
            "jt_attribution":             _jsonish(r.get("jt_attribution")),
            "event_id":                   r.get("event_id"),
        })

    n_active = sum(
        1 for ix in trace
        if (ix.get("jt_transfer_contribution") or 0) > 0.08
    )

    return {
        "user_id":          _TRACE_USER,
        "run_id":           _SEALED_RUN_IDS["phase2"],
        "n_interactions":   len(trace),
        "n_transfer_active": n_active,
        "source":           "live_db",
        "trace":            trace,
    }


@router.get("/trace/{interaction_number}")
async def get_interaction_detail(interaction_number: int) -> Dict[str, Any]:
    """Single interaction detail for the Replay Explorer."""
    store = _store()
    row = _read(
        store,
        """
        SELECT *
        FROM experiment_trajectories
        WHERE user_id = %s AND interaction_number = %s
        LIMIT 1
        """,
        (_TRACE_USER, interaction_number),
        fetch_one=True,
    )
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Interaction {interaction_number} not found for canonical trace user",
        )

    r = dict(row)
    return {
        "interaction_number": r.get("interaction_number"),
        "concept":            r.get("concept"),
        "mastery_before":     _safe_float(r.get("mastery_before")),
        "mastery_after":      _safe_float(r.get("mastery_after")),
        "correct":            bool(r.get("correctness")),
        "jt_value":           _safe_float(r.get("jt_value")),
        "jt_transfer_contribution":   _safe_float(r.get("jt_transfer_contribution")),
        "jt_delta_m_contribution":    _safe_float(r.get("jt_delta_m_contribution")),
        "jt_challenge_contribution":  _safe_float(r.get("jt_challenge_contribution")),
        "jt_uncertainty_contribution":_safe_float(r.get("jt_uncertainty_contribution")),
        "jt_zpd_contribution":        _safe_float(r.get("jt_zpd_contribution")),
        "transfer_amount_raw":        _safe_float(r.get("transfer_amount")),
        "transfer_amounts_json":      _jsonish(r.get("transfer_amounts_json")),
        "jt_attribution":             _jsonish(r.get("jt_attribution")),
        "event_id":                   r.get("event_id"),
        "source":                     "live_db",
        "run_id":                     _SEALED_RUN_IDS["phase2"],
    }


@router.get("/trace/user/{user_id}")
async def get_user_trace(
    user_id: str,
    run_id: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
) -> Dict[str, Any]:
    """
    Governance trace for an arbitrary user_id from the sealed runs.
    Used by the Replay Explorer when the reviewer picks a different learner.
    """
    store = _store()
    if run_id:
        full_user_id = f"{run_id}::{user_id}" if "::" not in user_id else user_id
    else:
        full_user_id = user_id

    rows = _read(
        store,
        """
        SELECT
            interaction_number, concept, mastery_before, mastery_after,
            correctness, jt_value, jt_transfer_contribution,
            jt_delta_m_contribution, jt_challenge_contribution,
            jt_uncertainty_contribution, jt_zpd_contribution,
            transfer_amount, transfer_amounts_json, jt_attribution, event_id
        FROM experiment_trajectories
        WHERE user_id = %s
        ORDER BY interaction_number ASC
        LIMIT %s
        """,
        (full_user_id, limit),
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No trace found for user_id={full_user_id!r}")

    trace = []
    for row in rows:
        r = dict(row)
        trace.append({
            "interaction_number": r.get("interaction_number"),
            "concept":            r.get("concept"),
            "mastery_before":     _safe_float(r.get("mastery_before")),
            "mastery_after":      _safe_float(r.get("mastery_after")),
            "correct":            bool(r.get("correctness")),
            "jt_value":           _safe_float(r.get("jt_value")),
            "jt_transfer_contribution":   _safe_float(r.get("jt_transfer_contribution")),
            "jt_delta_m_contribution":    _safe_float(r.get("jt_delta_m_contribution")),
            "jt_challenge_contribution":  _safe_float(r.get("jt_challenge_contribution")),
            "jt_uncertainty_contribution":_safe_float(r.get("jt_uncertainty_contribution")),
            "jt_zpd_contribution":        _safe_float(r.get("jt_zpd_contribution")),
            "transfer_amount_raw":        _safe_float(r.get("transfer_amount")),
            "transfer_amounts_json":      _jsonish(r.get("transfer_amounts_json")),
            "jt_attribution":             _jsonish(r.get("jt_attribution")),
            "event_id":                   r.get("event_id"),
        })

    n_active = sum(1 for ix in trace if (ix.get("jt_transfer_contribution") or 0) > 0.08)
    return {
        "user_id":           full_user_id,
        "n_interactions":    len(trace),
        "n_transfer_active": n_active,
        "source":            "live_db",
        "trace":             trace,
    }
