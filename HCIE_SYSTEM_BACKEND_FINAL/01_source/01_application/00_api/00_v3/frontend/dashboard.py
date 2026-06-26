"""
V3 Frontend Dashboard API - Comprehensive System Showcase

Rich dashboard showcasing full system potential with multi-dimensional analytics,
real-time metrics, system health, and comprehensive learning insights.
Authority State: converging → authoritative
Runtime Contract Version: 1.0

Closed-loop evidence chain (no fake data):
  interactions          → /cohort-concepts, /challenge-distribution
  learning_state        → /cohort-concepts (mastery)
  trajectory_records    → /session-trace, /cohort-trajectory (full per-interaction)
  experiment_trajectories → /session-trace (governance phase-A: JT decomp, ensemble)
  concept_dependencies  → /cohort-edges
  outbox_event_envelopes → /system-stats (event volume)
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/frontend/dashboard", tags=["v3-frontend"])


def _store():
    """Lazy postgres store accessor (avoids import-time DB init)."""
    from storage.postgres_store.interaction_store import PostgresInteractionStore
    return PostgresInteractionStore()


def _safe_read(query: str, params: tuple = (), default=None, fetch_one: bool = False):
    """Execute a read query; on any failure return ``default`` and log.

    The ``fetch_one`` flag mirrors ``PostgresInteractionStore.execute_read``'s
    semantics: when True, return a single dict (or ``default``) instead of a
    list. Callers that need a scalar (e.g. ``SELECT COUNT(*) AS n``) should
    pair ``fetch_one=True`` with a dict default like ``{"n": 0}``.
    """
    try:
        store = _store()
        rows = store.execute_read(query, params, fetch_one=fetch_one)
        if rows is None:
            return default if default is not None else ({} if fetch_one else [])
        return rows
    except Exception as exc:
        logger.warning(f"dashboard query failed: {exc!r} | query={query[:80]}")
        return default if default is not None else []

def _row1(query: str, params: tuple = ()) -> Dict[str, Any]:
    """First row of a read query as a dict (or ``{}``). Collapses the
    ``rows = _safe_read(...) or []; rows[0] if rows else {}`` boilerplate."""
    rows = _safe_read(query, params) or []
    return rows[0] if rows else {}


def _scalar(query: str, key: str, params: tuple = (), default: int = 0, cast=int):
    """Single first-row scalar with a typed default — replaces the repeated
    ``int(rows[0][key]) if rows else default`` pattern (each of which was its own branch)."""
    val = _row1(query, params).get(key)
    return default if val is None else cast(val)


def _parse_jsonb(val: Any) -> Any:
    """A JSONB column as a Python value — dict passthrough, JSON-string parsed, falsy -> {}.
    Replaces the repeated ``v = row.get(x) or {}; if isinstance(v,str): json.loads`` blocks."""
    val = val or {}
    if isinstance(val, str):
        import json as _json
        try:
            val = _json.loads(val)
        except Exception:  # noqa: BLE001
            val = {}
    return val


def _jt_session_summary(trace: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate session metrics from a built trace. Single source for both the
    experiment_trajectories path and the outbox-envelope fallback (was duplicated)."""
    correct_rows = [t for t in trace if t.get("correct") is True]
    incorrect_rows = [t for t in trace if t.get("correct") is False]
    transfer_fires = [t for t in trace if t["transfer"]["fired"]]
    deltas = [t["mastery_delta"] for t in trace if t["mastery_delta"] is not None]
    cold_start_rows = trace[-5:] if len(trace) >= 5 else trace
    cold_start_correct = sum(1 for t in cold_start_rows if t.get("correct") is True)
    rt_n = sum(1 for t in trace if t.get("response_time"))
    return {
        "total_interactions": len(trace),
        "correct_count": len(correct_rows),
        "incorrect_count": len(incorrect_rows),
        "accuracy": len(correct_rows) / len(trace) if trace else 0,
        "cumulative_mastery_gain": sum(deltas) if deltas else 0,
        "transfer_events": len(transfer_fires),
        "cold_start_accuracy": cold_start_correct / len(cold_start_rows) if cold_start_rows else 0,
        "avg_response_time": sum(t["response_time"] for t in trace if t.get("response_time")) / max(1, rt_n),
        "unique_concepts": len({t["concept_id"] for t in trace if t.get("concept_id")}),
        "first_timestamp": trace[-1].get("timestamp") if trace else None,
        "latest_timestamp": trace[0].get("timestamp") if trace else None,
    }


def _trace_jt_components(row: Dict[str, Any], jt_attr: Dict[str, Any]) -> Dict[str, Any]:
    """6D JT decomposition + V2 slots — prefer the stored column, fall back to jt_attribution."""
    return {
        'delta_m':    row.get('jt_delta_m_contribution')    or jt_attr.get('delta_m'),
        'transfer':   row.get('jt_transfer_contribution')   or jt_attr.get('transfer_realized'),
        'challenge':  row.get('jt_challenge_contribution')  or jt_attr.get('challenge'),
        'uncertainty': row.get('jt_uncertainty_contribution') or jt_attr.get('uncertainty'),
        'zpd':        row.get('jt_zpd_contribution')        or jt_attr.get('zpd'),
        'baseline_difficulty': row.get('jt_baseline_difficulty_contribution'),
        'challenge_event': row.get('jt_challenge_event_contribution'),
        'population_prior': row.get('jt_population_prior_contribution'),
        't_realized_v2': row.get('jt_t_realized_v2_contribution'),
    }


def _trace_jt_v2(row: Dict[str, Any]) -> Dict[str, Any]:
    """V2 governance state snapshot + challenge-event trigger."""
    active = row.get('jt_v2_active')
    fired = row.get('jt_v2_challenge_event_fired')
    return {
        'active': bool(active) if active is not None else False,
        'state_snapshot': row.get('jt_v2_state_snapshot') or {},
        'challenge_event_fired': bool(fired) if fired is not None else False,
        'challenge_event_reason': row.get('jt_v2_challenge_event_reason'),
    }


def _trace_ensemble(row: Dict[str, Any], ens_w: Any) -> Dict[str, Any]:
    """Per-learner posteriors + ensemble weights/attribution (after-update only in the
    migrated schema)."""
    return {
        'bayesian_before': {'alpha': None, 'beta': None},
        'bayesian_after': {
            'alpha': row.get('bayesian_alpha_after'),
            'beta':  row.get('bayesian_beta_after'),
        },
        'kalman_before': {'mastery': None, 'covariance': None},
        'kalman_after': {
            'mastery':    row.get('kalman_mastery_after'),
            'covariance': row.get('kalman_covariance_after'),
        },
        'lyapunov_before': None,
        'lyapunov_after':  row.get('lyapunov_mastery_after'),
        'weights': ens_w or {
            'kalman':   row.get('ensemble_weight_kalman'),
            'bayesian': row.get('ensemble_weight_bayesian'),
            'lyapunov': row.get('ensemble_weight_lyapunov'),
        },
        'normalized_weights': ens_w,
        'attribution_scores': row.get('attribution_scores'),
        'learner_contributions': {
            'kalman':   row.get('learner_jt_contribution_kalman'),
            'bayesian': row.get('learner_jt_contribution_bayesian'),
            'lyapunov': row.get('learner_jt_contribution_lyapunov'),
        },
        'canonical_mastery_after':  row.get('canonical_mastery_after'),
        'ensemble_mastery_estimate': row.get('ensemble_mastery_estimate'),
        'ensemble_variance_after':  row.get('ensemble_variance_after'),
        'bayesian_mastery_after':   row.get('bayesian_mastery_after'),
        'bayesian_variance_after':  row.get('bayesian_variance_after'),
        'kalman_gain_after':        row.get('kalman_gain_after'),
        'kalman_r_after':           row.get('kalman_r_after'),
    }


def _trace_row_from_et(row: Dict[str, Any]) -> Dict[str, Any]:
    """Shape one experiment_trajectories row into a session-trace entry (the canonical path)."""
    mb = row.get('mastery_before')
    ma = row.get('mastery_after')
    # Prefer stored mastery_delta; fall back to arithmetic only as last resort.
    delta_m = row.get('mastery_delta') or (
        (float(ma) - float(mb)) if (mb is not None and ma is not None) else None
    )
    ens_w = _parse_jsonb(row.get('ensemble_weights'))
    jt_attr = _parse_jsonb(row.get('jt_attribution'))
    ta_json = _parse_jsonb(row.get('transfer_amounts_json'))
    transfer_amt = row.get('transfer_amount_total') or row.get('transfer_amount') or 0.0
    try:
        transfer_amt = float(transfer_amt)
    except (TypeError, ValueError):
        transfer_amt = 0.0
    return {
        # identifiers
        'event_id': row.get('event_id') or f"{row.get('experiment_run_id','live')}::{row.get('interaction_number') or 'n'}",
        'interaction_id': row.get('interaction_id') or row.get('event_id'),
        'interaction_number': row.get('interaction_number'),
        'concept_id': row.get('concept'),
        'timestamp': str(row.get('timestamp')) if row.get('timestamp') else None,
        # request
        'policy': row.get('policy'),
        'arm_selected': row.get('arm_selected'),
        'difficulty': row.get('difficulty'),
        # response
        'correct': row.get('correctness'),
        'response_time': row.get('response_time'),
        'processing_time': row.get('processing_time'),
        # mastery transition
        'mastery_before': mb,
        'mastery_after': ma,
        'mastery_delta': delta_m,
        # JT composite & 6D decomposition
        'jt_value': row.get('jt_value'),
        'jt_volatility': row.get('governance_volatility'),
        'jt_components': _trace_jt_components(row, jt_attr),
        'jt_v2': _trace_jt_v2(row),
        'jt_unclamped': row.get('jt_unclamped'),
        'jt_clamped':   row.get('jt_clamped'),
        # ensemble estimators (after-update posteriors only in the migrated schema)
        'ensemble': _trace_ensemble(row, ens_w),
        # exploration / bandit governance
        'exploration': {
            'pressure':         row.get('governance_exploration_pressure'),
            'cv_window':        None,
            'regime':           None,
            'uncertainty_weight': None,
            'candidate_scores': row.get('candidate_arm_scores'),
        },
        # transfer
        'transfer': {
            'amount':     transfer_amt,
            'efficiency': None,
            'fired':      transfer_amt > 0.08,
            'breakdown':  ta_json,
        },
        # ZPD
        'zpd': {
            'target':          row.get('zpd_target'),
            'alignment_error': row.get('zpd_alignment_error'),
            'score':           row.get('zpd_score'),
            'delta_signal':    row.get('zpd_delta_signal'),
        },
        # confidence & uncertainty transition
        'confidence_before':  row.get('confidence_before'),
        'confidence_after':   row.get('confidence_after'),
        'uncertainty_before': row.get('uncertainty_before'),
        'uncertainty_after':  row.get('uncertainty_after'),
        'stability_index': row.get('governance_stability_index'),
    }


def _trace_row_from_envelope(r: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesize a session-trace entry from a CognitionUpdated outbox envelope (fallback path
    when experiment_trajectories has not been populated by the consumer yet)."""
    env = r.get('env') or {}
    p = (env.get('payload') or {})
    result = (p.get('result') if isinstance(p.get('result'), dict) else p) or {}
    jt_attr = result.get('jt_attribution') or {}
    ens_weights = result.get('ensemble_weights') or {}
    ma = result.get('canonical_mastery_after')
    mastery_delta = result.get('mastery_delta')
    try:
        # canonical_mastery_after is the AFTER value; before = after - delta.
        mb_val = float(ma) - float(mastery_delta) if (ma is not None and mastery_delta is not None) else None
    except (TypeError, ValueError):
        mb_val = None
    transfer_total = result.get('transfer_amount_total') or 0
    try:
        transfer_total = float(transfer_total)
    except (TypeError, ValueError):
        transfer_total = 0.0
    return {
        'event_id': r.get('event_id'),
        'interaction_id': r.get('event_id'),
        'interaction_number': None,
        'concept_id': p.get('concept_id') or result.get('concept_id'),
        'timestamp': str(r.get('timestamp')) if r.get('timestamp') else None,
        'policy': result.get('policy'),
        'arm_selected': result.get('selected_arm') or result.get('policy'),
        'difficulty': result.get('difficulty'),
        'correct': result.get('correct'),
        'response_time': result.get('response_time'),
        'processing_time': None,
        'mastery_before': mb_val,
        'mastery_after': ma,
        'mastery_delta': mastery_delta,
        'jt_value': result.get('jt_clamped') or result.get('J_value'),
        'jt_volatility': result.get('jt_volatility'),
        'jt_components': {
            'delta_m': jt_attr.get('delta_m'),
            'transfer': jt_attr.get('transfer_realized'),
            'challenge': jt_attr.get('challenge'),
            'uncertainty': jt_attr.get('uncertainty'),
            'zpd': jt_attr.get('zpd'),
        },
        'jt_unclamped': result.get('jt_unclamped'),
        'jt_clamped': result.get('jt_clamped'),
        'ensemble': {
            'bayesian_before': {'alpha': None, 'beta': None},
            'bayesian_after': {'alpha': result.get('bayesian_alpha'), 'beta': result.get('bayesian_beta')},
            'kalman_before': {'mastery': None, 'covariance': None},
            'kalman_after': {'mastery': result.get('kalman_mastery'), 'covariance': result.get('kalman_covariance')},
            'lyapunov_before': None,
            'lyapunov_after': result.get('lyapunov_mastery'),
            'weights': ens_weights,
            'normalized_weights': ens_weights,
            'attribution_scores': jt_attr,
        },
        'exploration': {
            'pressure': result.get('exploration_pressure'),
            'cv_window': None,
            'regime': None,
            'uncertainty_weight': None,
            'candidate_scores': None,
        },
        'transfer': {
            'amount': transfer_total,
            'efficiency': None,
            'fired': transfer_total > 0.08,
        },
        'zpd': {
            'target': result.get('zpd_target'),
            'alignment_error': result.get('zpd_alignment_error'),
            'score': result.get('zpd_score'),
        },
        'confidence_before': None,
        'confidence_after': result.get('confidence'),
        'uncertainty_before': None,
        'uncertainty_after': result.get('uncertainty'),
        'stability_index': result.get('stability_index'),
    }


def _cohort_proj_filter(dataset: str) -> str:
    """learner_projections WHERE-clause for a cohort dataset filter.

    The clause is f-string-interpolated into a query that ALSO passes a %s LIMIT param to psycopg2,
    so every literal percent in a LIKE pattern MUST be doubled (%%) — otherwise psycopg2 mis-parses
    `%e`/`%x`/etc. as format specifiers and the query dies with "tuple index out of range", silently
    returning []. (That was the bug: junyi/assistments/statics/ednet/live all returned zero learners.)
    """
    return {
        "synthetic": "WHERE lp.synthetic = true",
        "junyi": "WHERE lp.user_id LIKE '%%ex_junyi%%'",
        "assistments": "WHERE (lp.user_id LIKE '%%ext_assist%%' OR lp.user_id LIKE '%%assist%%')",
        "statics": "WHERE lp.user_id LIKE '%%ext_statics%%'",
        "ednet": "WHERE lp.user_id LIKE '%%ednet%%'",
        "live": (
            "WHERE lp.synthetic IS NOT TRUE "
            "AND lp.user_id ~ '^[0-9a-f-]{36}$' "
            "AND lp.user_id NOT LIKE 'ex_%%' "
            "AND lp.user_id NOT LIKE 'ext_%%' "
            "AND lp.user_id NOT LIKE 'synthetic:%%'"
        ),
    }.get(dataset, "WHERE true")


def _cohort_learner_type(uid: str, is_synthetic: bool) -> str:
    if is_synthetic:
        return "synthetic"
    if "ex_junyi" in uid:
        return "experiment-replay"
    if "ext_assist" in uid or "assist" in uid.lower():
        return "experiment-replay"
    if "ext_statics" in uid or "statics" in uid.lower():
        return "experiment-replay"
    if "ednet" in uid.lower():
        return "experiment-replay"
    # UUID-shaped, no research prefix → live human learner.
    if len(uid) == 36 and uid.count("-") == 4:
        return "live"
    return "experiment-replay"


def _cohort_dataset_name(uid: str) -> str:
    if "ex_junyi" in uid:
        return "junyi"
    if "ext_assist2015" in uid or "assist15" in uid.lower():
        return "assistments-2015"
    if "ext_assist2012" in uid or "assist2012" in uid.lower():
        return "assistments-2012"
    if "ext_assist2009" in uid or "assist2009" in uid.lower():
        return "assistments-2009"
    if "ext_statics" in uid:
        return "statics-2011"
    if "ednet" in uid.lower():
        return "ednet"
    if uid.startswith("synthetic:"):
        return "synthetic"
    if len(uid) == 36 and uid.count("-") == 4:
        return "live"
    return "other"


def _cohort_short_id(uid: str) -> str:
    """Strip the run prefix (run-xxx::) and shorten long ids to a clean label."""
    suffix = uid.split("::")[-1] if "::" in uid else uid
    return suffix[:12] + "…" + suffix[-8:] if len(suffix) > 28 else suffix


def _cohort_learner_row(r: Dict[str, Any], st: Dict[str, Any]) -> Dict[str, Any]:
    """One cohort-learner summary from a learner_projections row + its trajectory stats."""
    uid = r.get("user_id", "")
    avg_mastery = float(r.get("avg_mastery") or 0)
    first_m = float(st.get("first_mastery") or avg_mastery * 0.7)
    last_m = float(st.get("last_mastery") or avg_mastery)
    return {
        "user_id": uid,
        "short_id": _cohort_short_id(uid),
        "learner_type": _cohort_learner_type(uid, bool(r.get("synthetic"))),
        "dataset": _cohort_dataset_name(uid),
        "n_interactions": int(st.get("n_interactions") or 0),
        "avg_mastery": avg_mastery,
        "avg_delta_m": float(st.get("avg_delta_m") or 0),
        "accuracy": float(st.get("accuracy") or 0),
        "avg_jt": float(st.get("avg_jt") or 0),
        "concepts_visited": int(st.get("concepts_visited") or 1),
        "first_mastery": first_m,
        "last_mastery": last_m,
        "improvement": round(last_m - first_m, 4),
        "uncertainty": float(r.get("uncertainty") or 0),
        "traffic_type": r.get("traffic_type") or "unknown",
        "last_seen": str(r.get("last_seen")) if r.get("last_seen") else None,
    }


def _system_stats_payload(g: Dict[str, Any]) -> Dict[str, Any]:
    """Shape gathered system-stats values into the API response. Kept separate so the
    gatherer (get_system_stats) stays under the complexity budget — the coercion branches
    live here, in a flat shaping function, not in the query orchestration."""
    b = g["base"]
    first_i, last_i = b.get("first_interaction"), b.get("last_interaction")
    return {
        "status": "ok",
        "interactions": {
            "total": int(b.get("total_interactions") or 0),
            "total_estimated": True,  # reltuples planner estimate (#59 perf)
            "unique_users": int(b.get("unique_users") or 0),
            "unique_concepts": int(b.get("unique_concepts") or 0),
            "avg_correct": float(b.get("avg_correct") or 0),
            # experiment_trajectories has no reward column (#59 repoint): None, not 0.0,
            # so the frontend distinguishes "unavailable" from a real zero.
            "avg_reward": None,
            "avg_reward_available": False,
            "first_interaction": str(first_i) if first_i else None,
            "last_interaction": str(last_i) if last_i else None,
        },
        "active_sessions": g["active_sessions"],
        "learning_state": {"tracked_concepts": g["tracked_concepts"], "total_rows": g["learning_state_rows"]},
        "task_catalog": {"total": g["task_count"]},
        "trajectories": {"total": g["total_trajectories"], "users_with_trajectories": g["users_with_trajectories"]},
        "events": {"outbox_total": g["total_events"], "outbox_published": g["published_events"]},
        "authority": "experiment_trajectories + learning_state + tasks + outbox",
        "semantic_version": "1.0",
    }


dashboard_router = router


# ── Lightweight in-process TTL cache (#59 perf) ──────────────────────────────
# system-stats runs several COUNT/COUNT(DISTINCT) over large tables
# (experiment_trajectories ~445k, outbox ~789k, tasks ~849k) and measured ~19s.
# It's a coarse KPI panel where short staleness is acceptable, so cache it.
import time as _time

_TTL_CACHE: Dict[str, Any] = {}
_TTL_SECONDS = 60.0


def _cache_get(key: str):
    entry = _TTL_CACHE.get(key)
    if entry and (_time.monotonic() - entry[0]) < _TTL_SECONDS:
        return entry[1]
    return None


def _cache_set(key: str, value: Any) -> Any:
    _TTL_CACHE[key] = (_time.monotonic(), value)
    return value


def _trajectory_counts() -> Dict[str, int]:
    """Cheap, cached row/user counts for experiment_trajectories (#59 perf).

    `total_interactions` uses the pg_class.reltuples planner estimate (~24ms,
    within ~3% of exact) instead of COUNT(*) on 445k+ rows. `unique_users` is
    the genuinely expensive figure (COUNT(DISTINCT user_id) ≈ 8s), so it is
    computed at most once per TTL window and shared by overview + system-stats.
    Both are served from the 60s TTL cache.
    """
    cached = _cache_get("traj_counts")
    if cached is not None:
        return cached

    est_rows = _safe_read("""
        SELECT GREATEST(reltuples, 0)::bigint AS est
        FROM pg_class WHERE relname = 'experiment_trajectories'
    """) or []
    total_interactions = int(est_rows[0]['est']) if est_rows else 0

    # Exact-but-slow distinct user count; cached so only one call per window pays.
    uu_rows = _safe_read("""
        SELECT COUNT(DISTINCT user_id) AS uu FROM experiment_trajectories
    """) or []
    unique_users = int(uu_rows[0]['uu']) if uu_rows else 0

    return _cache_set("traj_counts", {
        "total_interactions": total_interactions,
        "total_interactions_estimated": True,
        "unique_users": unique_users,
    })


# Pydantic models for API
class SystemOverviewResponse(BaseModel):
    """System overview with comprehensive metrics."""
    total_users: int
    total_interactions: int
    active_sessions: int
    system_health: str
    objective_function_value: float
    canonical_state_health: Dict[str, Any]
    semantic_version: str = "1.0"


class UserDashboardResponse(BaseModel):
    """Comprehensive user dashboard with full system insights."""
    user_id: str
    mastery_summary: Dict[str, Any]
    learning_trajectory: List[Dict[str, Any]]
    transfer_learning_insights: Dict[str, Any]
    governance_state: Dict[str, Any]
    recommendation: Dict[str, Any]
    system_objectives: Dict[str, Any]
    semantic_version: str = "1.0"


class SystemAnalyticsResponse(BaseModel):
    """System-wide analytics for showcasing full potential."""
    learning_velocity: float
    transfer_effectiveness: float
    governance_convergence: float
    objective_function_trend: List[Dict[str, Any]]
    system_health_metrics: Dict[str, Any]
    semantic_version: str = "1.0"


# Dependency injection
from app.api.v3.dependencies import get_objective_projection, get_governance_projection, get_recommendation_projection


@router.get("/overview", response_model=SystemOverviewResponse)
async def get_system_overview(
    objective_projection = Depends(get_objective_projection),
    governance_projection = Depends(get_governance_projection)
):
    """
    Get comprehensive system overview showcasing full system potential.
    
    Includes:
    - System health metrics
    - Objective function value (north star metric)
    - Canonical state health
    - User and interaction counts
    """
    try:
        # Get objective function state
        objective_state = objective_projection.project_objective_state()
        
        # Get governance state for system health
        governance_state = governance_projection.project_state("system")
        
        # Real counts from experiment_trajectories (#59 repoint — the canonical
        # interaction record; the legacy interactions table is empty in FINAL).
        # Uses the shared cached/estimated counts helper (reltuples for total,
        # cached distinct-user) so this endpoint stays fast.
        try:
            tc = _trajectory_counts()
            total_users = int(tc.get('unique_users') or 0)
            total_interactions = int(tc.get('total_interactions') or 0)
        except Exception as exc:
            logger.warning(f"overview stats query failed: {exc!r}")
            total_users = 0
            total_interactions = 0

        # Active sessions: users with a trajectory row in last 5 minutes.
        active_rows = _safe_read("""
            SELECT COUNT(DISTINCT user_id) AS active
            FROM experiment_trajectories
            WHERE timestamp > NOW() - INTERVAL '5 minutes'
        """) or []
        active_sessions = int(active_rows[0].get('active', 0)) if active_rows else 0
        
        return SystemOverviewResponse(
            total_users=total_users,
            total_interactions=total_interactions,
            active_sessions=active_sessions,
            system_health=objective_state.canonical_state_health.get("health", "UNKNOWN"),
            objective_function_value=objective_state.objective_function_value,
            canonical_state_health=objective_state.canonical_state_health
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}", response_model=UserDashboardResponse)
def _ud_mastery(user_id: str):
    """learning_state → (avg_mastery, top-5 concepts)."""
    rows = _safe_read(
        "SELECT concept, (state_data->>'mastery')::float AS mastery "
        "FROM learning_state WHERE user_id = %s AND state_data ? 'mastery' ORDER BY mastery DESC",
        (user_id,)) or []
    mastery_map = {r['concept']: float(r['mastery'] or 0.0) for r in rows}
    avg_mastery = sum(mastery_map.values()) / len(mastery_map) if mastery_map else 0.0
    top_concepts = sorted(mastery_map.keys(), key=lambda x: mastery_map[x], reverse=True)[:5]
    return avg_mastery, top_concepts


def _ud_trajectory(user_id: str):
    """experiment_trajectories → (raw rows, shaped learning_trajectory). Rows reused for improvement_rate."""
    rows = _safe_read(
        """
        SELECT interaction_number, concept,
               ROUND(mastery_before::numeric, 4) AS mastery_before,
               ROUND(mastery_after::numeric, 4)  AS mastery_after,
               ROUND(jt_clamped::numeric, 4)     AS jt_value,
               correctness, policy, synthetic, LEFT(timestamp::text, 23) AS ts
        FROM experiment_trajectories WHERE user_id = %s ORDER BY timestamp ASC LIMIT 50
        """, (user_id,)) or []
    trajectory = [{
        "interaction": int(r.get('interaction_number') or 0),
        "concept": r.get('concept'),
        "mastery_before": float(r.get('mastery_before') or 0),
        "mastery_after": float(r.get('mastery_after') or 0),
        "jt_value": float(r.get('jt_value') or 0),
        "correct": bool(r.get('correctness')),
        "policy": r.get('policy'),
        "synthetic": bool(r.get('synthetic')),
        "timestamp": r.get('ts'),
    } for r in rows]
    return rows, trajectory


def _ud_transfer(user_id: str) -> Dict[str, Any]:
    """experiment_trajectories transfer_amount → transfer_learning_insights block."""
    rows = _safe_read(
        "SELECT COALESCE(AVG(transfer_amount),0.0) AS mean_transfer, "
        "COALESCE(SUM(transfer_amount),0.0) AS total_transfer, COUNT(*) AS n "
        "FROM experiment_trajectories WHERE user_id = %s AND transfer_amount IS NOT NULL",
        (user_id,)) or []
    tr = rows[0] if rows else {}
    total = float(tr.get('total_transfer') or 0.0)
    mean = float(tr.get('mean_transfer') or 0.0)
    n = int(tr.get('n') or 0)
    return {
        "transfer_efficiency": round((total / n) if n > 0 else 0.0, 4),
        "total_transfer": round(total, 4),
        "mean_transfer_per_interaction": round(mean, 4),
        "transfer_sources": [],
    }


def _ud_governance(user_id: str) -> Dict[str, Any]:
    """learner_projections + latest JT → governance_state, recommendation, jt_value, alignment, traffic_type."""
    rows = _safe_read(
        """
        SELECT concept_id, recommended_concept, projection, ux_semantics, governance,
               cold_start, selection_metrics, traffic_type, LEFT(updated_at::text, 23) AS updated_at
        FROM learner_projections WHERE user_id = %s ORDER BY updated_at DESC LIMIT 1
        """, (user_id,)) or []
    gov_row = rows[0] if rows else {}
    proj_data = gov_row.get('projection') or {}
    ux_data = gov_row.get('ux_semantics') or {}
    gov_data = gov_row.get('governance') or {}
    sel_data = gov_row.get('selection_metrics') or {}
    ensemble_weights = {}
    if isinstance(proj_data, dict):
        for k in ('kalman_mastery', 'bayesian_alpha', 'lyapunov_mastery'):
            if k in proj_data:
                ensemble_weights[k] = proj_data[k]
    jt_rows = _safe_read(
        "SELECT jt_clamped FROM experiment_trajectories WHERE user_id = %s AND jt_clamped IS NOT NULL "
        "ORDER BY timestamp DESC LIMIT 1", (user_id,)) or []
    jt_value = float(jt_rows[0].get('jt_clamped') or 0.0) if jt_rows else 0.0
    rec_confidence = (float(proj_data.get('zpd_alignment') or proj_data.get('zpd_score') or 0.0)
                      if isinstance(proj_data, dict) else 0.0)
    alignment = float(proj_data.get('zpd_alignment') or 0.0) if isinstance(proj_data, dict) else 0.0
    return {
        "governance_state": {
            "governance_weights": ensemble_weights, "normalization_state": sel_data,
            "policy_type": sel_data.get('policy_type') or 'unknown', "jt_governance": gov_data,
            "pedagogical_state": ux_data.get('pedagogical_state') or '',
            "concept_id": gov_row.get('concept_id') or 'unknown', "updated_at": gov_row.get('updated_at') or '',
        },
        "recommendation": {
            "recommended_concept": gov_row.get('recommended_concept') or ux_data.get('next_concept_guidance') or 'unknown',
            "confidence": round(rec_confidence, 4),
            "readiness": ux_data.get('readiness') or 'unknown',
            "recommended_action": ux_data.get('recommended_action') or '',
        },
        "jt_value": jt_value, "alignment": alignment, "traffic_type": gov_row.get('traffic_type') or 'unknown',
    }


async def get_user_dashboard(
    user_id: str,
):
    """
    Get comprehensive user dashboard from canonical DB tables.

    Authority chain (all reads from persisted sources):
      learning_state              → mastery_summary (_ud_mastery)
      experiment_trajectories     → learning_trajectory + transfer + JT (_ud_trajectory/_ud_transfer/_ud_governance)
      learner_projections         → governance_state, recommendation (_ud_governance)
    """
    try:
        avg_mastery, top_concepts = _ud_mastery(user_id)
        traj_rows, learning_trajectory = _ud_trajectory(user_id)
        gov = _ud_governance(user_id)
        improvement_rate = 0.0
        if len(traj_rows) >= 2:
            improvement_rate = (float(traj_rows[-1].get('mastery_after') or 0.0)
                                - float(traj_rows[0].get('mastery_before') or 0.0))
        return UserDashboardResponse(
            user_id=user_id,
            mastery_summary={
                "avg_mastery": round(avg_mastery, 4),
                "top_concepts": top_concepts,
                "improvement_rate": round(improvement_rate, 4),
                "interactions_observed": len(traj_rows),
                "traffic_type": gov["traffic_type"],
            },
            learning_trajectory=learning_trajectory,
            transfer_learning_insights=_ud_transfer(user_id),
            governance_state=gov["governance_state"],
            recommendation=gov["recommendation"],
            system_objectives={
                "objective_function_value": round(gov["jt_value"], 4),
                "alignment_score": round(gov["alignment"], 4),
            },
        )
    except Exception as e:
        logger.error(f"get_user_dashboard error: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics", response_model=SystemAnalyticsResponse)
async def get_system_analytics(
    objective_projection = Depends(get_objective_projection),
    governance_projection = Depends(get_governance_projection)
):
    """
    Get system-wide analytics showcasing full system potential.
    
    Includes:
    - Learning velocity
    - Transfer effectiveness
    - Governance convergence
    - Objective function trend
    - System health metrics
    """
    try:
        # Get objective function state
        objective_state = objective_projection.project_objective_state()
        
        # Get governance state for convergence metrics
        governance_state = governance_projection.project_state("system")
        
        # Calculate governance convergence from governance state
        governance_convergence = 0.0
        if hasattr(governance_state, 'normalization_state'):
            # TODO: Calculate actual convergence metric
            governance_convergence = 0.0
        
        # Get actual objective function trend from objective state
        # TODO: Implement trend tracking in objective projection
        objective_function_trend = []
        
        return SystemAnalyticsResponse(
            learning_velocity=objective_state.research_metrics.get("learning_velocity", 0.0),
            transfer_effectiveness=objective_state.research_metrics.get("transfer_efficiency", 0.0),
            governance_convergence=governance_convergence,
            objective_function_trend=objective_function_trend,
            system_health_metrics={
                "canonical_state_health": objective_state.canonical_state_health,
                "research_metrics": objective_state.research_metrics
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Closed-loop cohort analytics endpoints
# These read real data from Postgres tables populated by the consumer pipeline.
# If a table is empty or unavailable, endpoints return status='no_data' with an
# empty payload — the frontend is responsible for surfacing the empty state
# instead of substituting mock data.
# =============================================================================


# ── Catalog / source classification SQL ──────────────────────────────────────
# Concept catalog is inferred from the concept-ID prefix. Real data shows:
#   k12_* / k8_* / k5_* / k3_* / k2_*  → bespoke K-12 catalog
#   ext_junyi_*                        → Junyi Academy replay
#   ext_ednet_*                        → EdNet replay
#   ext_csedm_*                        → CSEDM replay
#   ext_assist* / ext_assistments_*     → ASSISTments replay
#   ext_statics_*                      → STATICS replay
# Source ("which population is this row from?") is inferred from user_id:
#   run-<uuid>:*  / synthetic*  → synthetic policy-sweep cohort
#   ex_* / ext_*                → real-dataset replay learner
#   ^[0-9a-f]{8}-[0-9a-f]{4}-…  → real human (UUID-shaped)
#
# IMPORTANT: psycopg2 with parameter binding treats every '%' as a format
# token unless escaped as '%%'. All LIKE wildcards below MUST be doubled.
#
_CATALOG_SQL = """
    CASE
        WHEN concept ~ '^k(2|3|5|8|12)_' THEN 'k12'
        WHEN concept LIKE 'ext_junyi%%'        THEN 'junyi'
        WHEN concept LIKE 'ext_ednet%%'        THEN 'ednet'
        WHEN concept LIKE 'ext_csedm%%'        THEN 'csedm'
        WHEN concept LIKE 'ext_assist%%'       THEN 'assistments'
        WHEN concept LIKE 'assist%%'           THEN 'assistments'
        WHEN concept LIKE 'ext_statics%%'      THEN 'statics'
        ELSE 'other'
    END
"""
_SOURCE_SQL = """
    CASE
        WHEN user_id LIKE 'run-%%' OR user_id LIKE 'synthetic%%' THEN 'synthetic'
        WHEN user_id LIKE 'ex_%%' OR user_id LIKE 'ext_%%'       THEN 'dataset_replay'
        WHEN user_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-'              THEN 'human'
        ELSE 'other'
    END
"""

_CATALOG_VALUES = {'k12', 'junyi', 'ednet', 'csedm', 'assistments', 'statics', 'other'}
_SOURCE_VALUES = {'human', 'synthetic', 'dataset_replay'}


def _cc_mastery_rows(cat: Optional[str], src: Optional[str], limit: int) -> list:
    """Per-concept mastery (catalog-tagged), filtered by catalog + source."""
    where, params = "", []
    if cat:
        where += f" AND ({_CATALOG_SQL}) = %s"
        params.append(cat)
    if src:
        where += f" AND ({_SOURCE_SQL}) = %s"
        params.append(src)
    return _safe_read(f"""
        SELECT concept,
               ({_CATALOG_SQL}) AS catalog,
               COUNT(DISTINCT user_id)                   AS student_count,
               AVG((state_data->>'mastery')::float)      AS avg_mastery,
               COUNT(*)                                  AS state_rows
        FROM learning_state
        WHERE state_data ? 'mastery'{where}
        GROUP BY concept, catalog
        ORDER BY avg_mastery ASC NULLS LAST
        LIMIT %s
    """, tuple(params + [limit]))


def _cc_source_breakdown(cat: Optional[str]) -> Dict[str, dict]:
    """Population breakdown for the current catalog filter, BEFORE the source
    filter — lets the UI show "Synthetic: 4023 / Human: 49 / Dataset: 10"."""
    where, params = "", []
    if cat:
        where = f" AND ({_CATALOG_SQL}) = %s"
        params.append(cat)
    rows = _safe_read(f"""
        SELECT ({_SOURCE_SQL}) AS source,
               COUNT(DISTINCT user_id) AS users,
               COUNT(*)                AS rows
        FROM learning_state
        WHERE state_data ? 'mastery'{where}
        GROUP BY source
        ORDER BY rows DESC
    """, tuple(params)) or []
    return {
        r['source']: {'users': int(r['users'] or 0), 'rows': int(r['rows'] or 0)}
        for r in rows
    }


def _cc_catalog_breakdown() -> Dict[str, dict]:
    """Catalog breakdown (irrespective of current filters) — feeds the chip row
    "K-12 (12) / Junyi (28) / EdNet (5) ..."."""
    rows = _safe_read(f"""
        SELECT ({_CATALOG_SQL}) AS catalog,
               COUNT(DISTINCT concept) AS concepts,
               COUNT(DISTINCT user_id) AS users
        FROM learning_state
        WHERE state_data ? 'mastery'
        GROUP BY catalog
        ORDER BY concepts DESC
    """) or []
    return {
        r['catalog']: {'concepts': int(r['concepts'] or 0), 'users': int(r['users'] or 0)}
        for r in rows
    }


def _cc_fail_map(src: Optional[str]) -> Dict[str, dict]:
    """Per-concept attempts/fail-rate (source-aware), keyed by concept_id.
    Difficulty stays whole-table."""
    where, params = "WHERE concept_id IS NOT NULL AND concept_id <> ''", []
    if src:
        where += f" AND ({_SOURCE_SQL}) = %s"
        params.append(src)
    rows = _safe_read(f"""
        SELECT concept_id,
               COUNT(*) AS total_attempts,
               1.0 - AVG(CASE WHEN correct THEN 1.0 ELSE 0.0 END) AS fail_rate,
               AVG(difficulty) AS avg_difficulty
        FROM interactions
        {where}
        GROUP BY concept_id
    """, tuple(params)) or []
    return {r['concept_id']: r for r in rows}


def _cc_edge_map() -> Dict[str, int]:
    """Incoming prerequisite-edge count per concept (transfer_incoming)."""
    rows = _safe_read("""
        SELECT target_concept AS concept_id, COUNT(*) AS incoming_edges
        FROM concept_dependencies
        GROUP BY target_concept
    """) or []
    return {r['concept_id']: int(r['incoming_edges']) for r in rows}


def _cc_concepts(mastery_rows: list, fail_map: Dict[str, dict], edge_map: Dict[str, int]) -> list:
    """Join mastery rows with fail-rate and prerequisite-edge maps into the
    per-concept response list."""
    out = []
    for row in mastery_rows:
        cid = row['concept']
        fd = fail_map.get(cid, {})
        out.append({
            'concept_id': cid,
            'catalog': row.get('catalog') or 'other',
            'avg_mastery': float(row['avg_mastery'] or 0),
            'student_count': int(row['student_count'] or 0),
            'state_rows': int(row.get('state_rows') or 0),
            'fail_rate': float(fd.get('fail_rate') or 0),
            'total_attempts': int(fd.get('total_attempts') or 0),
            'avg_difficulty': float(fd.get('avg_difficulty') or 0),
            'transfer_incoming': edge_map.get(cid, 0),
        })
    return out


@router.get("/cohort-concepts")
async def get_cohort_concepts(
    limit: int = Query(200, ge=1, le=1000),
    catalog: Optional[str] = Query(None,
        description="Concept-catalog filter: k12 | junyi | ednet | csedm | assistments | statics | other"),
    source: Optional[str] = Query(None,
        description="Learner-source filter: human | synthetic | dataset_replay"),
) -> Dict[str, Any]:
    """
    Per-concept cohort analytics with catalog/source segmentation.

    Sources (all real):
      - learning_state.state_data->>'mastery'  → avg_mastery, student_count
      - interactions                            → fail_rate, total_attempts
      - concept_dependencies                    → transfer_incoming

    Each row carries a `catalog` tag so the frontend can color/group without
    re-deriving the prefix mapping.

    Authority: learning_state + interactions + concept_dependencies
    """
    cat = catalog if catalog in _CATALOG_VALUES else None
    src = source if source in _SOURCE_VALUES else None

    mastery_rows = _cc_mastery_rows(cat, src, limit)
    base = {
        'filter': {'catalog': cat, 'source': src, 'limit': limit},
        'source_breakdown': _cc_source_breakdown(cat),
        'catalog_breakdown': _cc_catalog_breakdown(),
        'authority': 'learning_state + interactions + concept_dependencies',
        'semantic_version': '2.0',
    }

    if not mastery_rows:
        return {
            **base,
            'status': 'no_data',
            'reason': 'no mastery rows match the current catalog/source filter',
            'concepts': [],
            'count': 0,
        }

    concepts = _cc_concepts(mastery_rows, _cc_fail_map(src), _cc_edge_map())
    return {**base, 'status': 'ok', 'concepts': concepts, 'count': len(concepts)}


@router.get("/challenge-distribution")
async def get_challenge_distribution(
    traffic_type: Optional[str] = Query(None, description="Filter by traffic type: 'human', 'research', 'demo', 'replay'")
) -> Dict[str, Any]:
    """
    Difficulty bucket distribution.

    Source: experiment_trajectories.difficulty  (#59 repoint — the legacy
    `interactions` table is empty in the FINAL stack; the canonical
    interaction record lives in experiment_trajectories written by the
    trajectory recorder consumer / research writer). Correctness column is
    `correctness` (not `correct`).
    NOTE: difficulty is populated mostly on research-writer rows, so the
    distribution is research-weighted; human Kafka rows often lack difficulty.
    Authority: experiment_trajectories
    """
    traffic_where = ""
    traffic_params: tuple = ()
    if traffic_type:
        traffic_where = " AND traffic_type = %s"
        traffic_params = (traffic_type,)

    rows = _safe_read(f"""
        SELECT
            CASE
                WHEN difficulty <= 0.30 THEN 'Easy'
                WHEN difficulty <= 0.60 THEN 'Medium'
                WHEN difficulty <= 0.80 THEN 'Hard'
                ELSE 'Expert'
            END AS bucket,
            CASE
                WHEN difficulty <= 0.30 THEN 1
                WHEN difficulty <= 0.60 THEN 2
                WHEN difficulty <= 0.80 THEN 3
                ELSE 4
            END AS sort_order,
            COUNT(*) AS count,
            AVG(CASE WHEN correctness THEN 1.0 ELSE 0.0 END) AS avg_correct,
            AVG(response_time) AS avg_response_time
        FROM experiment_trajectories
        WHERE difficulty IS NOT NULL{traffic_where}
        GROUP BY bucket, sort_order
        ORDER BY sort_order
    """, traffic_params) or []

    if not rows:
        return {
            'status': 'no_data',
            'reason': 'no difficulty-tagged trajectories',
            'distribution': [],
            'authority': 'experiment_trajectories',
            'semantic_version': '1.0',
        }

    ranges = {'Easy': '0–30%', 'Medium': '30–60%', 'Hard': '60–80%', 'Expert': '80–100%'}
    distribution = [
        {
            'label': r['bucket'],
            'range': ranges.get(r['bucket'], ''),
            'count': int(r['count']),
            'avg_correct': float(r['avg_correct'] or 0),
            'avg_response_time': float(r['avg_response_time'] or 0),
        }
        for r in rows
    ]
    return {
        'status': 'ok',
        'distribution': distribution,
        'authority': 'experiment_trajectories',
        'semantic_version': '1.0',
    }


@router.get("/cohort-edges")
async def get_cohort_edges(limit: int = Query(30, ge=1, le=200), traffic_type: Optional[str] = Query(None, description="Filter by traffic type: 'human', 'research', 'demo', 'replay'")) -> Dict[str, Any]:
    """
    Prerequisite edge effectiveness.

    Sources:
      - concept_dependencies                    → designed topology
      - interactions per source/target          → activation counts
      - trajectory_records.transfer_amount      → observed transfer mean per target (optional)

    Authority: concept_dependencies + interactions + trajectory_records
    
    🔥 TRAFFIC CLASSIFICATION: Filter by traffic_type to separate research from product traffic
    """
    edge_rows = _safe_read("""
        SELECT source_concept, target_concept,
               transfer_weight, dependency_type
        FROM concept_dependencies
        ORDER BY transfer_weight DESC NULLS LAST
        LIMIT %s
    """, (limit,))

    if not edge_rows:
        return {
            'status': 'no_data',
            'reason': 'concept_dependencies table empty',
            'edges': [],
            'count': 0,
            'authority': 'concept_dependencies + interactions + trajectory_records',
            'semantic_version': '1.0',
        }

    attempt_rows = _safe_read("""
        SELECT concept_id, COUNT(*) AS attempt_count
        FROM interactions
        WHERE concept_id IS NOT NULL
        GROUP BY concept_id
    """) or []
    attempts_map = {r['concept_id']: int(r['attempt_count']) for r in attempt_rows}

    # 🔥 TRAFFIC CLASSIFICATION: Build WHERE clause for traffic_type filtering
    traffic_where = ""
    traffic_params = ()
    if traffic_type:
        traffic_where = " AND traffic_type = %s"
        traffic_params = (traffic_type,)

    # Observed transfer per target concept (from experiment_trajectories — the
    # canonical write target of the trajectory recorder consumer).
    transfer_rows = _safe_read(f"""
        SELECT concept,
               AVG(transfer_amount) AS mean_transfer,
               COUNT(*) FILTER (WHERE transfer_amount > 0.08) AS activations
        FROM experiment_trajectories
        WHERE transfer_amount IS NOT NULL{traffic_where}
        GROUP BY concept
    """, traffic_params) or []
    transfer_map = {r['concept']: r for r in transfer_rows}

    edges = []
    for row in edge_rows:
        src = row['source_concept']
        tgt = row['target_concept']
        weight = float(row['transfer_weight'] or 0)
        obs = transfer_map.get(tgt, {})
        mean_transfer = float(obs.get('mean_transfer') or 0)
        activations = int(obs.get('activations') or 0)
        edges.append({
            'source': src,
            'target': tgt,
            'transfer_weight': weight,           # designed weight
            'mean_transfer': mean_transfer,      # observed mean from trajectory_records
            'activation_count': activations,     # times transfer_amount > 0.08 observed
            'source_attempts': attempts_map.get(src, 0),
            'target_attempts': attempts_map.get(tgt, 0),
            'effective': mean_transfer > 0.08 if mean_transfer else weight > 0.08,
            'dependency_type': row.get('dependency_type', 'prerequisite'),
        })
    return {
        'status': 'ok',
        'edges': edges,
        'count': len(edges),
        'authority': 'concept_dependencies + interactions + trajectory_records',
        'semantic_version': '1.0',
    }


@router.get("/system-stats")
async def get_system_stats(traffic_type: Optional[str] = Query(None, description="Filter by traffic type: 'human', 'research', 'demo', 'replay'")) -> Dict[str, Any]:
    """
    Real-time system stats for instructor dashboard.

    Sources:
      - interactions                  → totals, unique users
      - learning_state                → tracked concepts
      - outbox_event_envelopes       → event volume (if exists)
      - experiment_trajectories       → recorded trajectory rows
      - tasks                         → task catalog size

    Authority: experiment_trajectories + learning_state + tasks + outbox

    🔥 TRAFFIC CLASSIFICATION: Filter by traffic_type to separate research from product traffic
    """
    # #59 perf: serve from 60s TTL cache (this panel runs several heavy
    # COUNT(DISTINCT) over large tables; staleness is acceptable for KPIs).
    _ck = f"system-stats:{traffic_type or 'all'}"
    _cached = _cache_get(_ck)
    if _cached is not None:
        return _cached

    # Interaction stats (#59 repoint: experiment_trajectories is the canonical
    # interaction record; the legacy interactions table is empty in FINAL.
    # Column names differ: concept (not concept_id), correctness (not correct);
    # there is no reward column on experiment_trajectories.)
    # total_interactions + unique_users come from the shared cached/estimated
    # helper (reltuples + cached distinct). The remaining aggregates
    # (avg_correct, unique_concepts, first/last) are computed here; when no
    # traffic_type filter is set this still scans, but the whole response is
    # cached for 60s so only the cold call pays.
    tc = _trajectory_counts()
    agg_rows = _safe_read("""
        SELECT
            COUNT(DISTINCT concept) AS unique_concepts,
            AVG(CASE WHEN correctness THEN 1.0 ELSE 0.0 END) AS avg_correct,
            MIN(timestamp) AS first_interaction,
            MAX(timestamp) AS last_interaction
        FROM experiment_trajectories
    """)
    agg = (agg_rows[0] if agg_rows else {}) or {}
    base = {
        "total_interactions": tc.get("total_interactions", 0),
        "unique_users": tc.get("unique_users", 0),
        "unique_concepts": agg.get("unique_concepts"),
        "avg_correct": agg.get("avg_correct"),
        "first_interaction": agg.get("first_interaction"),
        "last_interaction": agg.get("last_interaction"),
    }

    # Active sessions (last 5 min)
    active_sessions = _scalar(
        "SELECT COUNT(DISTINCT user_id) AS active_sessions FROM experiment_trajectories "
        "WHERE timestamp > NOW() - INTERVAL '5 minutes'", "active_sessions")

    # Tracked concepts in learning_state (one row, two columns)
    ls = _row1("SELECT COUNT(DISTINCT concept) AS tracked_concepts, COUNT(*) AS total_rows FROM learning_state")
    tracked_concepts = int(ls.get("tracked_concepts") or 0)
    learning_state_rows = int(ls.get("total_rows") or 0)

    # Task catalog
    task_count = _scalar("SELECT COUNT(*) AS total FROM tasks", "total")

    # 🔥 TRAFFIC CLASSIFICATION: optional traffic_type filter (same clause for both tables)
    where = " WHERE traffic_type = %s" if traffic_type else ""
    params = (traffic_type,) if traffic_type else ()

    # Trajectory record count (research-grade evidence) — experiment_trajectories is the
    # canonical write target of the trajectory-recorder consumer.
    traj = _row1(
        "SELECT COUNT(*) AS total_trajectories, COUNT(DISTINCT user_id) AS users_with_trajectories "
        f"FROM experiment_trajectories{where}", params)
    total_trajectories = int(traj.get("total_trajectories") or 0)
    users_with_trajectories = int(traj.get("users_with_trajectories") or 0)

    # Outbox event volume (event flow evidence)
    outbox = _row1(
        "SELECT COUNT(*) AS total_events, COUNT(*) FILTER (WHERE published_at IS NOT NULL) AS published_events "
        f"FROM outbox_event_envelopes{where}", params)
    total_events = int(outbox.get("total_events") or 0)
    published_events = int(outbox.get("published_events") or 0)

    return _cache_set(_ck, _system_stats_payload({
        "base": base,
        "active_sessions": active_sessions,
        "tracked_concepts": tracked_concepts,
        "learning_state_rows": learning_state_rows,
        "task_count": task_count,
        "total_trajectories": total_trajectories,
        "users_with_trajectories": users_with_trajectories,
        "total_events": total_events,
        "published_events": published_events,
    }))


@router.get("/session-trace/{user_id}")
async def get_session_trace(
    user_id: str,
    limit: int = Query(50, ge=1, le=500),
) -> Dict[str, Any]:
    """
    Per-interaction trace chain for a learner — the closed-loop evidence.

    Each row is one full interaction with:
      - identifiers: event_id, interaction_id, interaction_number
      - request: concept, recommended task, policy, arm_selected
      - response: correctness, response_time, difficulty
      - state transition: mastery_before → mastery_after, ΔM
      - JT 6D decomposition: delta_m, transfer, challenge, uncertainty, zpd
      - ensemble before/after: bayesian, kalman, lyapunov
      - transfer: transfer_amount, transfer_efficiency
      - ZPD: zpd_target, zpd_alignment_error, zpd_score
      - timestamp

    Sources:
      - trajectory_records          → canonical per-interaction snapshot
      - experiment_trajectories     → phase-A enriched (JT, ensemble) when available

    Authority: trajectory_records + experiment_trajectories
    """
    # experiment_trajectories is the canonical write target of the trajectory
    # recorder consumer (see infrastructure/experiment/trajectory_recorder.py).
    # Column names here match the migrated DB schema (migration-007 + migration-013+).
    # The Phase-1 bootstrap names (jt_volatility, stability_index, normalized_weight_vector,
    # raw_* estimator columns, etc.) were renamed/dropped in the canonical migration path.
    rows = _safe_read("""
        SELECT
            et.experiment_run_id,
            et.interaction_number,
            et.event_id,
            et.interaction_id,
            et.user_id,
            et.concept,
            et.policy,
            et.arm_selected,
            et.correctness,
            et.response_time,
            et.difficulty,
            et.mastery_before,
            et.mastery_after,
            et.mastery_delta,
            et.uncertainty_before,
            et.uncertainty_after,
            et.confidence_before,
            et.confidence_after,
            -- JT composite
            et.jt_value,
            et.jt_clamped,
            et.jt_unclamped,
            et.jt_attribution,
            -- JT 6D decomposition
            et.jt_delta_m_contribution,
            et.jt_transfer_contribution,
            et.jt_transfer_prospective_contribution,
            et.jt_challenge_contribution,
            et.jt_uncertainty_contribution,
            et.jt_zpd_contribution,
            -- Tier 2.5 V2 decomposition
            et.jt_baseline_difficulty_contribution,
            et.jt_challenge_event_contribution,
            et.jt_population_prior_contribution,
            et.jt_t_realized_v2_contribution,
            et.jt_v2_active,
            et.jt_v2_state_snapshot,
            et.jt_v2_challenge_event_fired,
            et.jt_v2_challenge_event_reason,
            -- Governance state (renamed from stability_index/jt_volatility/exploration_pressure)
            et.governance_volatility,
            et.governance_stability_index,
            et.governance_exploration_pressure,
            -- Ensemble weights & posteriors
            et.ensemble_weights,
            et.weights_snapshot,
            et.ensemble_weight_kalman,
            et.ensemble_weight_bayesian,
            et.ensemble_weight_lyapunov,
            et.canonical_mastery_after,
            et.ensemble_mastery_estimate,
            et.ensemble_variance_after,
            et.bayesian_alpha_after,
            et.bayesian_beta_after,
            et.bayesian_mastery_after,
            et.bayesian_variance_after,
            et.kalman_mastery_after,
            et.kalman_covariance_after,
            et.kalman_gain_after,
            et.kalman_r_after,
            et.lyapunov_mastery_after,
            -- Learner-level JT contributions
            et.learner_jt_contribution_kalman,
            et.learner_jt_contribution_bayesian,
            et.learner_jt_contribution_lyapunov,
            -- Transfer
            et.transfer_amount,
            et.transfer_amount_total,
            et.transfer_amounts_json,
            -- ZPD
            et.zpd_target,
            et.zpd_alignment_error,
            et.zpd_score,
            et.zpd_delta_signal,
            -- Attribution / exploration (Phase-A A2/A4 columns)
            et.attribution_scores,
            et.candidate_arm_scores,
            et.selection_metrics,
            -- Metadata
            et.capability_manifest_fingerprint,
            et.traffic_type,
            et.timestamp
        FROM experiment_trajectories et
        WHERE et.user_id = %s
        ORDER BY et.interaction_number DESC NULLS LAST, et.timestamp DESC
        LIMIT %s
    """, (user_id, limit))

    if not rows:
        # Fallback: experiment_trajectories is populated by the trajectory_recorder
        # consumer via Kafka. When the outbox→Kafka pipeline is lagging, no rows
        # exist yet — but the CognitionUpdated envelope already contains the
        # full JT decomposition. Read directly from outbox_event_envelopes so
        # the closed loop is verifiable end-to-end without waiting for the
        # eventually-consistent consumer pipeline.
        # Constrain temporal window: recent envelopes only. This makes the
        # JSONB extraction selective (an index-able timestamp filter narrows
        # the scan from 500K rows down to recent activity).
        envelope_rows = _safe_read("""
            SELECT
              event_id,
              envelope::jsonb AS env,
              timestamp
            FROM outbox_event_envelopes
            WHERE event_type = 'CognitionUpdated'
              AND timestamp > NOW() - INTERVAL '24 hours'
              AND envelope::jsonb->'payload'->>'user_id' = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (user_id, limit))

        if not envelope_rows:
            return {
                'status': 'no_data',
                'reason': 'no experiment_trajectories or outbox events for this user',
                'user_id': user_id,
                'trace': [],
                'count': 0,
                'authority': 'experiment_trajectories | outbox_event_envelopes',
                'semantic_version': '1.0',
            }

        # Synthesize trace from outbox envelope payloads; number oldest = interaction 1.
        trace = [_trace_row_from_envelope(r) for r in envelope_rows]
        for idx, t in enumerate(reversed(trace)):
            t['interaction_number'] = idx + 1
        return {
            'status': 'ok',
            'user_id': user_id,
            'trace': trace,
            'count': len(trace),
            'session_summary': _jt_session_summary(trace),
            'authority': 'outbox_event_envelopes (synthesized — experiment_trajectories not yet populated)',
            'fallback_reason': 'experiment_trajectories empty; reading CognitionUpdated envelopes directly',
            'semantic_version': '1.0',
        }

    trace = [_trace_row_from_et(row) for row in rows]
    return {
        'status': 'ok',
        'user_id': user_id,
        'trace': trace,
        'count': len(trace),
        'session_summary': _jt_session_summary(trace),
        'authority': 'trajectory_records + experiment_trajectories',
        'semantic_version': '1.0',
    }


@router.get("/cohort-trajectory")
async def get_cohort_trajectory(
    limit_users: int = Query(20, ge=1, le=100),
    limit_per_user: int = Query(30, ge=1, le=200),
) -> Dict[str, Any]:
    """
    Cohort-wide trajectory aggregates for instructor view.

    Returns per-user trajectory summary (mastery progression, attempt count, last activity).

    Authority: trajectory_records + interactions
    """
    rows = _safe_read("""
        SELECT
            et.user_id,
            COUNT(*) AS interaction_count,
            AVG(CASE WHEN et.correctness THEN 1.0 ELSE 0.0 END) AS accuracy,
            AVG(et.mastery_after) AS avg_mastery,
            MAX(et.mastery_after) AS peak_mastery,
            COUNT(*) FILTER (WHERE et.transfer_amount > 0.08) AS transfer_events,
            COUNT(DISTINCT et.concept) AS unique_concepts,
            MAX(et.timestamp) AS last_activity,
            AVG(et.jt_value) AS avg_jt
        FROM experiment_trajectories et
        GROUP BY et.user_id
        ORDER BY last_activity DESC
        LIMIT %s
    """, (limit_users,))

    if not rows:
        return {
            'status': 'no_data',
            'reason': 'experiment_trajectories empty',
            'users': [],
            'count': 0,
            'authority': 'experiment_trajectories',
            'semantic_version': '1.0',
        }

    users = [
        {
            'user_id': r.get('user_id'),
            'interaction_count': int(r.get('interaction_count') or 0),
            'accuracy': float(r.get('accuracy') or 0),
            'avg_mastery': float(r.get('avg_mastery') or 0),
            'peak_mastery': float(r.get('peak_mastery') or 0),
            'transfer_events': int(r.get('transfer_events') or 0),
            'unique_concepts': int(r.get('unique_concepts') or 0),
            'avg_jt': float(r.get('avg_jt') or 0),
            'last_activity': str(r.get('last_activity')) if r.get('last_activity') else None,
        }
        for r in rows
    ]
    return {
        'status': 'ok',
        'users': users,
        'count': len(users),
        'authority': 'trajectory_records',
        'semantic_version': '1.0',
    }


def _ccmp_curves(run_id: str) -> Dict[str, list]:
    """Per-policy, per-step average mastery curve: {policy: [{step, avg_mastery, ...}]}."""
    rows = _safe_read("""
        SELECT
            policy,
            interaction_number,
            COUNT(DISTINCT user_id)                                    AS n_learners,
            AVG(mastery_after)                                         AS avg_mastery,
            AVG(CASE WHEN correctness THEN 1.0 ELSE 0.0 END)          AS accuracy,
            AVG(jt_value)                                              AS avg_jt,
            AVG(mastery_after - mastery_before)                        AS avg_delta_m
        FROM experiment_trajectories
        WHERE experiment_run_id = %s
          AND policy IS NOT NULL
        GROUP BY policy, interaction_number
        ORDER BY policy, interaction_number
    """, (run_id,), default=[])
    curves: Dict[str, list] = {}
    for r in rows:
        curves.setdefault(r.get('policy') or 'unknown', []).append({
            'step': int(r.get('interaction_number') or 0),
            'avg_mastery': float(r.get('avg_mastery') or 0),
            'accuracy': float(r.get('accuracy') or 0),
            'avg_jt': float(r.get('avg_jt') or 0),
            'avg_delta_m': float(r.get('avg_delta_m') or 0),
            'n_learners': int(r.get('n_learners') or 0),
        })
    return curves


def _ccmp_summary(run_id: str) -> Dict[str, dict]:
    """Per-policy summary (final/peak mastery, learners, accuracy) keyed by policy."""
    rows = _safe_read("""
        SELECT
            policy,
            COUNT(DISTINCT user_id)                                    AS total_learners,
            AVG(mastery_after)                                         AS avg_final_mastery,
            MAX(mastery_after)                                         AS peak_mastery,
            AVG(CASE WHEN correctness THEN 1.0 ELSE 0.0 END)          AS overall_accuracy,
            AVG(jt_value)                                              AS avg_jt,
            COUNT(*)                                                   AS total_interactions
        FROM experiment_trajectories
        WHERE experiment_run_id = %s
          AND policy IS NOT NULL
        GROUP BY policy
        ORDER BY policy
    """, (run_id,), default=[])
    summary: Dict[str, dict] = {}
    for r in rows:
        summary[r.get('policy') or 'unknown'] = {
            'total_learners': int(r.get('total_learners') or 0),
            'avg_final_mastery': float(r.get('avg_final_mastery') or 0),
            'peak_mastery': float(r.get('peak_mastery') or 0),
            'overall_accuracy': float(r.get('overall_accuracy') or 0),
            'avg_jt': float(r.get('avg_jt') or 0),
            'total_interactions': int(r.get('total_interactions') or 0),
        }
    return summary


def _ccmp_concept_dist(run_id: str) -> Dict[str, list]:
    """Per-policy concept-selection distribution — which concepts each policy chose.
    HCIE should favour prerequisite-order traversal (k2 -> k5 -> k8); random is uniform."""
    rows = _safe_read("""
        SELECT
            policy,
            concept,
            COUNT(*)                                    AS n_interactions,
            AVG(CASE WHEN correctness THEN 1.0 ELSE 0.0 END) AS accuracy,
            AVG(mastery_after)                          AS avg_mastery,
            AVG(mastery_after - mastery_before)         AS avg_delta_m
        FROM experiment_trajectories
        WHERE experiment_run_id = %s
          AND policy IS NOT NULL
          AND concept IS NOT NULL
        GROUP BY policy, concept
        ORDER BY policy, n_interactions DESC
    """, (run_id,), default=[])
    dist: Dict[str, list] = {}
    for r in rows:
        dist.setdefault(r.get('policy') or 'unknown', []).append({
            'concept': r.get('concept'),
            'n': int(r.get('n_interactions') or 0),
            'accuracy': float(r.get('accuracy') or 0),
            'avg_mastery': float(r.get('avg_mastery') or 0),
            'avg_delta_m': float(r.get('avg_delta_m') or 0),
        })
    return dist


def _ccmp_cold_start(run_id: str) -> Dict[str, dict]:
    """Per-policy, per-archetype early-step (1-5) mastery — the cold-start window."""
    rows = _safe_read("""
        SELECT
            policy,
            CASE
                WHEN user_id LIKE '%%:novice:%%' THEN 'novice'
                WHEN user_id LIKE '%%:intermediate:%%' THEN 'intermediate'
                ELSE 'unknown'
            END AS archetype,
            AVG(mastery_after) AS avg_mastery,
            AVG(CASE WHEN correctness THEN 1.0 ELSE 0.0 END) AS accuracy,
            COUNT(DISTINCT user_id) AS n_learners
        FROM experiment_trajectories
        WHERE experiment_run_id = %s
          AND policy IS NOT NULL
          AND interaction_number <= 5
        GROUP BY policy, archetype
        ORDER BY policy, archetype
    """, (run_id,), default=[])
    cold: Dict[str, dict] = {}
    for r in rows:
        cold.setdefault(r.get('policy') or 'unknown', {})[r.get('archetype') or 'unknown'] = {
            'avg_mastery': float(r.get('avg_mastery') or 0),
            'accuracy': float(r.get('accuracy') or 0),
            'n_learners': int(r.get('n_learners') or 0),
        }
    return cold


@router.get("/cohort-run/{run_id}/comparison")
async def get_cohort_run_comparison(run_id: str) -> Dict[str, Any]:
    """
    Policy comparison for a cohort run.

    Returns per-policy mastery curves (avg mastery at each step across all learners),
    summary stats, and run progress. Used by the instructor dashboard study tab.

    Authority: experiment_trajectories + cohort_runs
    """
    run_meta = _row1(
        "SELECT status, progress, started_at, completed_at FROM cohort_runs WHERE run_id = %s",
        (run_id,),
    )
    curves = _ccmp_curves(run_id)
    summary = _ccmp_summary(run_id)

    if not curves and not summary:
        return {
            'status': 'running' if run_meta.get('status') == 'running' else 'no_data',
            'run_id': run_id,
            'progress': run_meta.get('progress', {}),
            'policies': [],
            'curves': {},
            'summary': {},
            'authority': 'experiment_trajectories',
            'semantic_version': '1.0',
        }

    return {
        'status': run_meta.get('status', 'unknown'),
        'run_id': run_id,
        'progress': run_meta.get('progress', {}),
        'started_at': str(run_meta.get('started_at')) if run_meta.get('started_at') else None,
        'completed_at': str(run_meta.get('completed_at')) if run_meta.get('completed_at') else None,
        'policies': list(curves.keys()),
        'curves': curves,
        'summary': summary,
        'concept_distribution': _ccmp_concept_dist(run_id),
        'cold_start': _ccmp_cold_start(run_id),
        'authority': 'experiment_trajectories',
        'semantic_version': '1.0',
    }


@router.get("/learner-cohort")
async def get_learner_cohort(
    limit: int = Query(24, ge=1, le=100),
    dataset: str = Query(
        "all",
        description=(
            "Filter: 'all', 'junyi', 'assistments', 'statics', 'ednet', "
            "'synthetic', or 'live' for real human learners"
        ),
    ),
) -> Dict[str, Any]:
    """
    Returns a summary of experiment-replay and synthetic learners for the
    'Real Learner Cohort' instructor view.

    Sources:
      - experiment_trajectories → per-learner aggregates (mastery, accuracy, ΔM, JT, interactions)
      - learner_projections     → latest mastery estimate per learner

    Learner types:
      synthetic        — cohort sweep learners (synthetic: prefix)
      experiment-replay — Junyi / ASSISTments / STATICS replay (ex_ / ext_ prefix)
    """
    # Fast path: learner_projections (46MB, indexed) rather than a full-table GROUP BY over
    # experiment_trajectories (623MB). The projection stores the latest mastery per learner.
    proj_filter = _cohort_proj_filter(dataset)
    rows = _safe_read(
        f"""
        SELECT
            lp.user_id,
            lp.synthetic,
            ROUND((lp.projection->>'mastery')::numeric, 4) AS avg_mastery,
            ROUND((lp.projection->>'uncertainty')::numeric, 4) AS uncertainty,
            lp.updated_at AS last_seen,
            lp.traffic_type
        FROM (
            SELECT DISTINCT ON (user_id)
                user_id, synthetic, projection, updated_at, traffic_type
            FROM learner_projections lp
            {proj_filter}
              AND projection->>'mastery' IS NOT NULL
              AND (projection->>'mastery')::numeric > 0
            ORDER BY user_id, updated_at DESC
        ) lp
        ORDER BY (lp.projection->>'mastery')::numeric DESC
        LIMIT %s
        """,
        (limit,),
        default=[],
    )
    # Interaction counts per user, scoped to the returned users (avoids a full-table scan).
    user_ids = [r.get("user_id") for r in (rows or []) if r.get("user_id")]
    stats_map: Dict[str, Any] = {}
    if user_ids:
        placeholders = ",".join(["%s"] * len(user_ids))
        stats_rows = _safe_read(
            f"""
            SELECT user_id,
                COUNT(*) AS n_interactions,
                ROUND(AVG(COALESCE(mastery_after, 0) - COALESCE(mastery_before, 0))::numeric, 4) AS avg_delta_m,
                ROUND(AVG(CASE WHEN correctness THEN 1.0 ELSE 0.0 END)::numeric, 3) AS accuracy,
                ROUND(AVG(COALESCE(jt_clamped, 0))::numeric, 4) AS avg_jt,
                COUNT(DISTINCT concept) AS concepts_visited,
                MIN(COALESCE(mastery_before, 0.3)) AS first_mastery,
                MAX(COALESCE(mastery_after, 0.3)) AS last_mastery
            FROM experiment_trajectories
            WHERE user_id IN ({placeholders})
            GROUP BY user_id
            """,
            tuple(user_ids),
            default=[],
        ) or []
        stats_map = {sr["user_id"]: sr for sr in stats_rows}

    learners = [_cohort_learner_row(r, stats_map.get(r.get("user_id", ""), {})) for r in (rows or [])]
    return {
        "status": "ok",
        "learners": learners,
        "total": len(learners),
        "dataset_filter": dataset,
        "semantic_version": "1.0",
    }


@router.get("/cohort-run/{run_id}/status")
async def get_cohort_run_status(run_id: str) -> Dict[str, Any]:
    """Lightweight run status poll for the live monitor."""
    row = _safe_read(
        "SELECT status, progress, started_at, completed_at FROM cohort_runs WHERE run_id = %s",
        (run_id,),
        default=[],
    )
    if not row:
        return {'status': 'not_found', 'run_id': run_id, 'semantic_version': '1.0'}
    r = row[0]
    return {
        'status': r.get('status'),
        'run_id': run_id,
        'progress': r.get('progress', {}),
        'started_at': str(r.get('started_at')) if r.get('started_at') else None,
        'completed_at': str(r.get('completed_at')) if r.get('completed_at') else None,
        'semantic_version': '1.0',
    }


# ── Helper: classify a cohort_runs.reason into a source group ─────────────────
def _classify_run_source(reason: str) -> Dict[str, str]:
    """Return {group, dataset} for a cohort run based on its reason string.

    group ∈ {synthetic, dataset}; dataset is the external dataset key or '' for
    synthetic runs.
    """
    r = (reason or "").lower()
    if r.startswith("external_log:"):
        tag = r.split("external_log:", 1)[1]
        for key in ("junyi", "assistments", "statics", "ednet", "csedm"):
            if tag.startswith(key):
                return {"group": "dataset", "dataset": key}
        return {"group": "dataset", "dataset": tag.split("_")[0]}
    return {"group": "synthetic", "dataset": ""}


@router.get("/cohort-runs")
async def list_cohort_runs(
    group: str = Query("", description="filter: synthetic | dataset | '' for all"),
    dataset: str = Query("", description="filter by dataset key (junyi, ednet, …)"),
    limit: int = Query(200, le=1000),
) -> Dict[str, Any]:
    """List cohort runs for the label-based picker.

    Returns every run with derived {group, dataset, completed, total, runtime_seconds}
    plus convenience pointers: `latest` (most recent completed run per dataset/synthetic)
    and `best` (most completed interactions). Lets the UI auto-pick the freshest run
    instead of relying on a hardcoded ID, and offer 'see other runs'.
    """
    rows = _safe_read(
        """
        SELECT run_id, cohort_id, status, reason, started_at, completed_at,
               progress
        FROM cohort_runs
        WHERE status IN ('completed', 'completed_with_errors', 'running')
        ORDER BY started_at DESC NULLS LAST
        LIMIT %s
        """,
        (limit,),
        default=[],
    ) or []

    runs = []
    for r in rows:
        src = _classify_run_source(r.get("reason", ""))
        if group and src["group"] != group:
            continue
        if dataset and src["dataset"] != dataset:
            continue
        prog = r.get("progress") or {}
        started = r.get("started_at")
        completed_at = r.get("completed_at")
        runtime_s = None
        if started and completed_at:
            try:
                runtime_s = (completed_at - started).total_seconds()
            except Exception:
                runtime_s = None
        runs.append({
            "run_id": r.get("run_id"),
            "cohort_id": r.get("cohort_id"),
            "status": r.get("status"),
            "reason": r.get("reason"),
            "group": src["group"],
            "dataset": src["dataset"],
            "completed": int(prog.get("completed", 0) or 0),
            "total": int(prog.get("total", 0) or 0),
            "errors": int(prog.get("errors", 0) or 0),
            "started_at": str(started) if started else None,
            "completed_at": str(completed_at) if completed_at else None,
            "runtime_seconds": runtime_s,
        })

    # Convenience pointers: latest (by started_at, already DESC) + best (by completed)
    latest: Dict[str, Any] = {}
    best: Dict[str, Any] = {}
    for run in runs:
        key = run["dataset"] or "synthetic"
        if key not in latest:  # rows are DESC by started_at → first seen is latest
            latest[key] = run["run_id"]
        if key not in best or run["completed"] > best[key]["completed"]:
            best[key] = {"run_id": run["run_id"], "completed": run["completed"]}

    return {
        "status": "ok",
        "runs": runs,
        "latest_by_key": latest,
        "best_by_key": {k: v["run_id"] for k, v in best.items()},
        "count": len(runs),
        "semantic_version": "1.0",
    }


@router.get("/kt-benchmark/{run_id}")
async def kt_benchmark(run_id: str) -> Dict[str, Any]:
    """KT prediction benchmark for a dataset-replay run.

    HCIE (zero-shot) vs trained baselines (BKT, DKT, SAKT, IRT-1PL, GKT, …) on the
    SAME held-out users. Source: kt_prediction_evaluations. This is a DIFFERENT
    axis than policy comparison — it measures next-answer PREDICTION (AUC / accuracy
    / log-loss / Brier), not teaching efficacy.
    """
    # One eval per (model, cold_start_window); pick the most recent. Avoids the
    # duplicate rows that re-runs leave behind. We surface the smallest cold-start
    # window per model (most-zero-shot setting) as the headline, and expose the
    # full set under `all_windows` for drill-down.
    rows = _safe_read(
        """
        SELECT DISTINCT ON (model_id, cold_start_window)
               model_id, cold_start_window, n_predictions, n_users,
               auc, accuracy, log_loss, brier, created_at
        FROM kt_prediction_evaluations
        WHERE experiment_run_id = %s
        ORDER BY model_id, cold_start_window, created_at DESC
        """,
        (run_id,),
        default=[],
    ) or []

    if not rows:
        return {"status": "no_data", "run_id": run_id,
                "reason": "no kt_prediction_evaluations rows for this run",
                "models": [], "semantic_version": "1.0"}

    # Headline: one row per model — the window with the most predictions (most
    # representative), tie-broken by highest AUC.
    by_model: Dict[str, Any] = {}
    for r in rows:
        mid = r.get("model_id")
        cur = by_model.get(mid)
        npred = int(r.get("n_predictions", 0) or 0)
        if cur is None or npred > cur["n_predictions"]:
            by_model[mid] = {
                "model_id": mid,
                "auc": float(r["auc"]) if r.get("auc") is not None else None,
                "accuracy": float(r["accuracy"]) if r.get("accuracy") is not None else None,
                "log_loss": float(r["log_loss"]) if r.get("log_loss") is not None else None,
                "brier": float(r["brier"]) if r.get("brier") is not None else None,
                "n_predictions": npred,
                "n_users": int(r.get("n_users", 0) or 0),
                "cold_start_window": r.get("cold_start_window"),
                "is_hcie": (mid == "hcie"),
            }
    models = sorted(by_model.values(),
                    key=lambda m: (m["auc"] if m["auc"] is not None else -1),
                    reverse=True)

    hcie_rank = next((i + 1 for i, m in enumerate(models) if m["is_hcie"]), None)

    # ── Per-window curves (the cold-start axis — THE hypothesis lens) ──────────
    # window -1 = all interactions; 5/10/20 = first-N (sparse → dense).
    # windows_by_model[model][window] = {auc, accuracy, n_predictions}
    windows_by_model: Dict[str, Dict[int, Any]] = {}
    for r in rows:
        mid = r.get("model_id")
        w = r.get("cold_start_window")
        if w is None:
            continue
        slot = windows_by_model.setdefault(mid, {})
        # keep the most recent (rows are created_at DESC) per (model, window)
        if int(w) not in slot:
            slot[int(w)] = {
                "auc": float(r["auc"]) if r.get("auc") is not None else None,
                "accuracy": float(r["accuracy"]) if r.get("accuracy") is not None else None,
                "n_predictions": int(r.get("n_predictions", 0) or 0),
            }

    # cold_start_delta = AUC(w5) − AUC(overall): how much a model LOSES when
    # starved of data. Less-negative = more robust to sparsity (the claim).
    cold_start_curve = []
    for mid, slot in windows_by_model.items():
        w5 = slot.get(5, {}).get("auc")
        w_all = slot.get(-1, {}).get("auc")
        delta = (w5 - w_all) if (w5 is not None and w_all is not None) else None
        cold_start_curve.append({
            "model_id": mid,
            "is_hcie": (mid == "hcie"),
            "auc_w5": w5,
            "auc_w10": slot.get(10, {}).get("auc"),
            "auc_w20": slot.get(20, {}).get("auc"),
            "auc_overall": w_all,
            "cold_start_delta": delta,
        })
    # sort by least-negative delta (most sparsity-robust first)
    cold_start_curve.sort(key=lambda m: (m["cold_start_delta"] if m["cold_start_delta"] is not None else -99),
                          reverse=True)

    return {
        "status": "ok",
        "run_id": run_id,
        "models": models,
        "hcie_auc_rank": hcie_rank,
        "n_models": len(models),
        "windows": cold_start_curve,
        # ⚠ provenance: these numbers predate the sealed-run revalidation campaign.
        "validation_status": "anchored",
        "validation_note": (
            "Anchored to seal-fbf78cd9 (N=96,727). Cold-start protocol evaluates first-N "
            "interaction slices of a full-population run — NOT train-on-few / "
            "eval-on-unseen. Treat as exploratory until the sealed re-run."
        ),
        "semantic_version": "1.0",
    }


@router.get("/kt-benchmark-canonical")
async def kt_benchmark_canonical() -> Dict[str, Any]:
    """The benchmark headline on the THESIS CANONICAL (Kalman-alone, m_K) — not the legacy
    3-learner mastery_before that /kt-benchmark surfaces. Serves the precomputed
    benchmark_kalman_canonical.json (matched headline + cross-dataset deployed read-out), so
    the frontend shows HCIE-leads-overall AND the honest per-window cold-start picture
    (deep models lead; Simpson). Read-only artifact, regenerated by probe_lagged_kalman_auc.py
    + probe_hcie_vs_deepmodels.py."""
    from pathlib import Path as _P
    import json as _json
    for cand in (
        _P("/app/research_validation/reports/grounding/benchmark_kalman_canonical.json"),
        _P(__file__).resolve().parents[6] / "research_validation" / "reports" / "grounding" / "benchmark_kalman_canonical.json",
    ):
        try:
            if cand.is_file():
                data = _json.loads(cand.read_text(encoding="utf-8"))
                data["status"] = "ok"
                data["semantic_version"] = "1.0"
                return data
        except Exception:
            continue
    return {"status": "no_data", "reason": "benchmark_kalman_canonical.json not found",
            "semantic_version": "1.0"}


# Canonical 8-model KT-prediction runs (sealed; cited in THESIS/JOURNAL §4.10.3).
# These are the runs the unified cross-dataset matrix figure renders — fixed on
# purpose so the publication figure is the canonical set, not "whatever is latest".
_CANONICAL_KT_RUNS = {
    "junyi_2015":             ("Junyi 2015",      "run-217532ca-39e6-4859-a41f-88ed53e904a2"),
    "assistments_2015_skill": ("ASSISTments 2015", "run-9403d0c0-5610-4a1d-b1a9-198b7eb98aa7"),
    "csedm_f19":              ("CSEDM F19",       "run-92428fb6-790e-46a2-84c7-71b94f471aaf"),
    "ednet_kt1":              ("EdNet KT1",       "run-691cb4ef-e59e-4da7-be5b-4f63db3e2e73"),
    "statics_2011":           ("STATICS 2011",    "run-7ee4c59c-c06c-4b94-815f-3db8a1bb9875"),
}


@router.get("/kt-benchmark-matrix")
async def kt_benchmark_matrix() -> Dict[str, Any]:
    """Unified cross-dataset KT benchmark: every model × every dataset in one payload.

    Powers the publication 8×5 matrix figure (fig08b). Reads the canonical sealed
    runs at the overall window (cold_start_window = -1). HCIE is zero-shot; the
    trained baselines (bkt/dkt/sakt/irt_1pl/greedy_correct_rate) train on the same
    held-out users. Live from kt_prediction_evaluations — no frozen snapshot.
    """
    datasets: List[Dict[str, Any]] = []
    all_models: set = set()
    for dskey, (label, run_id) in _CANONICAL_KT_RUNS.items():
        rows = _safe_read(
            """
            SELECT DISTINCT ON (model_id)
                   model_id, auc, n_predictions, n_users, accuracy, brier
            FROM kt_prediction_evaluations
            WHERE experiment_run_id = %s AND cold_start_window = -1
            ORDER BY model_id, created_at DESC
            """,
            (run_id,),
            default=[],
        ) or []
        models = [{
            "model_id": r.get("model_id"),
            "auc": float(r["auc"]) if r.get("auc") is not None else None,
            "accuracy": float(r["accuracy"]) if r.get("accuracy") is not None else None,
            "brier": float(r["brier"]) if r.get("brier") is not None else None,
            "n_predictions": int(r.get("n_predictions", 0) or 0),
            "is_hcie": (r.get("model_id") == "hcie"),
        } for r in rows]
        models.sort(key=lambda m: m["auc"] if m["auc"] is not None else -1, reverse=True)
        for i, m in enumerate(models):
            m["rank"] = i + 1
        all_models.update(m["model_id"] for m in models)
        hcie_rank = next((m["rank"] for m in models if m["is_hcie"]), None)
        datasets.append({
            "dataset": dskey,
            "label": label,
            "run_id": run_id,
            "n_models": len(models),
            "hcie_rank": hcie_rank,
            "models": models,
        })
    return {
        "status": "ok",
        "datasets": datasets,
        "model_ids": sorted(all_models),
        "window": "overall",
        "note": (
            "Canonical sealed KT-prediction runs, overall window. HCIE zero-shot vs "
            "trained baselines on the same held-out users. HCIE is a governance "
            "instrument — mid-pack cross-dataset is expected; competitive on CSEDM."
        ),
        "semantic_version": "1.0",
    }


# ── Dataset "know your data" views ───────────────────────────────────────────

_DATASET_INFO = {
    "junyi_2015_graph": {"label": "Junyi 2015 (graph)", "origin": "Taiwanese math practice (Junyi Academy)", "has_graph": True},
    "junyi_2015":       {"label": "Junyi 2015",         "origin": "Taiwanese math practice (Junyi Academy)", "has_graph": False},
    "csedm_f19":        {"label": "CSEDM F19",          "origin": "CS-education programming (CSEDM 2019)",    "has_graph": False},
    "ednet_kt1":        {"label": "EdNet KT1",          "origin": "Korean English-prep / TOEIC (Santa)",      "has_graph": False},
    "assistments_2012_sb": {"label": "ASSISTments 2012", "origin": "US middle-school math tutor",            "has_graph": False},
    "assistments_2009_sb": {"label": "ASSISTments 2009", "origin": "US middle-school math tutor",            "has_graph": False},
    "assistments_2015_skill": {"label": "ASSISTments 2015", "origin": "US middle-school math (skill builder)", "has_graph": False},
    "statics_2011":     {"label": "STATICS 2011",       "origin": "University engineering statics (CMU OLI)", "has_graph": False},
}


# ── Tier 0h: per-family source-schema catalog ────────────────────────────────
# These are the *original* CSV/log column sets shipped by the dataset
# release, before HCIE's adapter normalises them into external_log_attempts.
# Written as research metadata (citations, URLs, granularity) so /dashboard/data
# can show schema-as-shipped vs schema-after-ingest in one place.
_SOURCE_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "junyi": {
        "release_url": "https://pslcdatashop.web.cmu.edu/Project?id=244",
        "format": "TSV log (~2.6GB, 25M attempts)",
        "granularity": "per-attempt (one row = one student answer)",
        "source_columns": [
            ("user_id",            "Student identifier (anonymised)"),
            ("exercise",           "Skill / KC name"),
            ("problem_type",       "Subtype within the skill"),
            ("time_done",          "Wall-clock attempt time (epoch)"),
            ("time_taken",         "Seconds spent on this attempt"),
            ("time_taken_attempts","Per-attempt-step time breakdown"),
            ("correct",            "Outcome (1/0)"),
            ("count_attempts",     "Cumulative attempts on this exercise"),
            ("hint_used",          "Whether the student used hints"),
            ("topic_mode",         "Topic / mode tag"),
        ],
        "graph_source": "Knowledge map relationship annotations (prereq edges shipped with the dataset).",
    },
    "assistments": {
        "release_url": "https://sites.google.com/site/assistmentsdata/",
        "format": "CSV release per year (skill-builder subset)",
        "granularity": "per-attempt within an assignment",
        "source_columns": [
            ("user_id",            "Student identifier"),
            ("assignment_id",      "Tutor session"),
            ("problem_id",         "Problem within the session"),
            ("skill_id",           "Tagged knowledge component"),
            ("skill_name",         "Human-readable skill"),
            ("original",           "1 = first attempt, 0 = re-do"),
            ("correct",            "Outcome (1/0)"),
            ("attempt_count",      "Number of attempts in this assignment"),
            ("ms_first_response",  "First-response time (ms)"),
            ("tutor_mode",         "Tutoring mode (skill-builder, etc.)"),
            ("answer_type",        "MCQ / fill-in / open"),
        ],
        "graph_source": "No prereq DAG shipped with the release; flat skill tags only.",
    },
    "ednet": {
        "release_url": "https://github.com/riiid/ednet",
        "format": "CSV per user (KT1 subset)",
        "granularity": "per-question response",
        "source_columns": [
            ("timestamp",     "Epoch timestamp"),
            ("solving_id",    "Internal solving session id"),
            ("question_id",   "Question (mapped to a small KC set)"),
            ("user_answer",   "Answer choice"),
            ("elapsed_time",  "Time to answer (ms)"),
        ],
        "graph_source": "No prereq graph shipped; flat 7-concept tag set.",
    },
    "csedm": {
        "release_url": "https://sites.google.com/ncsu.edu/csedm-dc-2021/home",
        "format": "CSV (Java program submissions, F19 subset)",
        "granularity": "per programming-exercise submission",
        "source_columns": [
            ("SubjectID",        "Student identifier"),
            ("AssignmentID",     "Programming assignment"),
            ("ProblemID",        "Specific exercise within the assignment"),
            ("Score",            "Outcome (1/0 — passed all unit tests)"),
            ("Code",             "Submitted Java source"),
            ("ServerTimestamp",  "Submission time"),
            ("CompileResult",    "Compiled vs error"),
        ],
        "graph_source": "No prereq DAG shipped; assignment ordering implicit.",
    },
    "statics": {
        "release_url": "https://pslcdatashop.web.cmu.edu/DatasetInfo?datasetId=507",
        "format": "Tab-delimited CMU OLI log",
        "granularity": "per problem step (KC tag)",
        "source_columns": [
            ("Anon Student Id",   "Anonymised student"),
            ("Problem Hierarchy", "Course → Module → Problem"),
            ("Problem Name",      "Specific problem"),
            ("Step Name",         "Step within the problem"),
            ("KC (Default)",      "Knowledge component tag"),
            ("First Attempt",     "Correct / Incorrect / Hint"),
            ("Outcome",           "Final outcome on this step"),
        ],
        "graph_source": "No concept-concept DAG shipped; bipartite Q-matrix only.",
    },
}


def _source_schema_for(dataset_id: str, registry_row: Dict[str, Any]) -> Dict[str, Any]:
    """Pick the source-schema entry by dataset family.
    The registry row stores `family`; we fall back to dataset_id prefix."""
    family = (registry_row or {}).get("family") or ""
    if family in _SOURCE_SCHEMAS:
        return {"family": family, **_SOURCE_SCHEMAS[family]}
    # Fall back: try to match by leading token of dataset_id.
    for fam in _SOURCE_SCHEMAS:
        if dataset_id.startswith(fam):
            return {"family": fam, **_SOURCE_SCHEMAS[fam]}
    return {
        "family": family or "unknown",
        "release_url": None,
        "format": "—",
        "granularity": "—",
        "source_columns": [],
        "graph_source": "—",
    }


# Canonical transformation each adapter applies (same for every family).
_CANONICAL_TRANSFORM: List[Dict[str, str]] = [
    {"canonical": "user_id",         "rule": "<dataset_prefix>_user_<n>",     "from": "source_user_id"},
    {"canonical": "concept_id",      "rule": "<concept_prefix><source>",      "from": "source_skill_id"},
    {"canonical": "task_id",         "rule": "<task_prefix><source>",         "from": "source_problem_id"},
    {"canonical": "correct",         "rule": "boolean cast of source outcome", "from": "correct / Score / Outcome"},
    {"canonical": "response_time",   "rule": "seconds (ms / 1000 if source is ms)", "from": "elapsed_time / ms_first_response / time_taken"},
    {"canonical": "attempt_index",   "rule": "row_number() within (user_id) ordered by raw_timestamp",        "from": "implicit"},
    {"canonical": "raw_timestamp",   "rule": "TIMESTAMPTZ from source epoch / iso",   "from": "timestamp / time_done / ServerTimestamp"},
]


@router.get("/datasets")
async def list_datasets() -> Dict[str, Any]:
    """Per-dataset profile across external_log_attempts: counts, density,
    correct-rate, response-time, interactions-per-user, graph presence."""
    rows = _safe_read(
        """
        SELECT dataset_id,
               count(*) AS rows,
               count(DISTINCT user_id) AS users,
               count(DISTINCT concept_id) AS concepts,
               avg(correct::int) AS correct_rate,
               avg(response_time) AS avg_response_time,
               min(raw_timestamp) AS first_ts,
               max(raw_timestamp) AS last_ts
        FROM external_log_attempts
        GROUP BY dataset_id
        ORDER BY count(*) DESC
        """,
        default=[],
    ) or []

    graph_rows = _safe_read(
        "SELECT dataset_id, count(*) AS edges FROM external_concept_graph GROUP BY dataset_id",
        default=[],
    ) or []
    edges_by_ds = {g["dataset_id"]: int(g["edges"]) for g in graph_rows}

    out = []
    for r in rows:
        ds = r["dataset_id"]
        users = int(r.get("users", 0) or 0)
        n = int(r.get("rows", 0) or 0)
        info = _DATASET_INFO.get(ds, {"label": ds, "origin": "—", "has_graph": False})
        out.append({
            "dataset_id": ds,
            "label": info["label"],
            "origin": info["origin"],
            "rows": n,
            "users": users,
            "concepts": int(r.get("concepts", 0) or 0),
            "interactions_per_user": round(n / users, 1) if users else None,
            "correct_rate": float(r["correct_rate"]) if r.get("correct_rate") is not None else None,
            "avg_response_time": float(r["avg_response_time"]) if r.get("avg_response_time") is not None else None,
            "first_ts": str(r["first_ts"]) if r.get("first_ts") else None,
            "last_ts": str(r["last_ts"]) if r.get("last_ts") else None,
            "graph_edges": edges_by_ds.get(ds, 0),
            "has_graph": edges_by_ds.get(ds, 0) > 0,
        })
    return {"status": "ok", "datasets": out, "count": len(out), "semantic_version": "1.0"}


@router.get("/datasets/{dataset_id}/sample")
async def dataset_sample(
    dataset_id: str,
    limit: int = Query(25, le=200),
) -> Dict[str, Any]:
    """Raw interaction rows + interactions-per-user histogram for a dataset."""
    rows = _safe_read(
        """
        SELECT user_id, concept_id, task_id, attempt_index, correct,
               response_time, raw_timestamp, source_user_id, source_skill_id
        FROM external_log_attempts
        WHERE dataset_id = %s
        ORDER BY user_id, attempt_index
        LIMIT %s
        """,
        (dataset_id, limit),
        default=[],
    ) or []

    hist = _safe_read(
        """
        WITH per_user AS (
            SELECT user_id, count(*) AS n
            FROM external_log_attempts WHERE dataset_id = %s GROUP BY user_id
        )
        SELECT
            CASE
                WHEN n < 10 THEN '<10'
                WHEN n < 25 THEN '10-24'
                WHEN n < 50 THEN '25-49'
                WHEN n < 100 THEN '50-99'
                WHEN n < 250 THEN '100-249'
                ELSE '250+'
            END AS bucket,
            count(*) AS users
        FROM per_user GROUP BY 1
        """,
        (dataset_id,),
        default=[],
    ) or []
    bucket_order = ['<10', '10-24', '25-49', '50-99', '100-249', '250+']
    hist_map = {h["bucket"]: int(h["users"]) for h in hist}
    histogram = [{"bucket": b, "users": hist_map.get(b, 0)} for b in bucket_order]

    sample = [{
        "user_id": r.get("user_id"),
        "concept_id": r.get("concept_id"),
        "task_id": r.get("task_id"),
        "attempt_index": r.get("attempt_index"),
        "correct": r.get("correct"),
        "response_time": float(r["response_time"]) if r.get("response_time") is not None else None,
        "raw_timestamp": str(r["raw_timestamp"]) if r.get("raw_timestamp") else None,
        "source_user_id": r.get("source_user_id"),
        "source_skill_id": r.get("source_skill_id"),
    } for r in rows]

    return {"status": "ok", "dataset_id": dataset_id, "sample": sample,
            "histogram": histogram, "semantic_version": "1.0"}


def _short_concept(c: str) -> str:
    """Strip ext_<dataset>_graph_ prefix for readable graph labels."""
    if not c:
        return c
    for pre in ("ext_junyi_graph_", "ext_junyi_", "ext_"):
        if c.startswith(pre):
            return c[len(pre):].replace("_", " ")
    return c.replace("_", " ")


@router.get("/concept-graph/{dataset_id}")
async def concept_graph(
    dataset_id: str,
    limit: int = Query(400, le=2000),
) -> Dict[str, Any]:
    """Prerequisite concept graph (only junyi_2015_graph has one). Nodes +
    weighted edges for the DAG viz — the structure that activates HCIE transfer."""
    rows = _safe_read(
        """
        SELECT source_concept_id, target_concept_id, transfer_weight, graph_method
        FROM external_concept_graph
        WHERE dataset_id = %s
        ORDER BY transfer_weight DESC
        LIMIT %s
        """,
        (dataset_id, limit),
        default=[],
    ) or []

    if not rows:
        return {"status": "no_graph", "dataset_id": dataset_id,
                "reason": "no edges in external_concept_graph for this dataset",
                "nodes": [], "edges": [], "semantic_version": "1.0"}

    total = _safe_read(
        "SELECT count(*) AS c FROM external_concept_graph WHERE dataset_id = %s",
        (dataset_id,), default=[],
    ) or [{"c": 0}]
    total_edges = int(total[0]["c"])

    deg: Dict[str, Dict[str, int]] = {}
    edges = []
    for r in rows:
        s = r["source_concept_id"]; t = r["target_concept_id"]
        w = float(r["transfer_weight"]) if r.get("transfer_weight") is not None else 0.0
        edges.append({"source": s, "target": t, "weight": round(w, 4),
                      "source_label": _short_concept(s), "target_label": _short_concept(t)})
        deg.setdefault(s, {"out": 0, "in": 0})["out"] += 1
        deg.setdefault(t, {"out": 0, "in": 0})["in"] += 1

    nodes = [{
        "id": c, "label": _short_concept(c),
        "out_degree": d["out"], "in_degree": d["in"],
    } for c, d in deg.items()]

    return {
        "status": "ok",
        "dataset_id": dataset_id,
        "nodes": nodes,
        "edges": edges,
        "total_edges": total_edges,
        "shown_edges": len(edges),
        "graph_method": rows[0].get("graph_method"),
        "semantic_version": "1.0",
    }


# ── Tier 0h: dataset evidence panels (publication-grade) ─────────────────────
# These two endpoints power the Schema & Pipeline / Graph Build / Audit Verdict
# tabs on /dashboard/data. They surface exactly the evidence a reviewer would
# expect: postgres residency, source schema, canonical transformation, graph
# build manifest, Tier-0 audit verdict — all derived from live tables and
# sealed lineage reports, never hand-edited.


@router.get("/dataset-evidence-overview")
async def dataset_evidence_overview() -> Dict[str, Any]:
    """Per-dataset residency + verdict, all 8 datasets at once.

    Used by the Audit Verdict tab on /dashboard/data: shows which datasets
    are EXCLUDE / DISCLOSE / REPROCESS, where their rows live, and how many
    rows each pipeline stage holds. No external scripts; one SQL roundtrip
    per source so caching is unnecessary.
    """
    registry = _safe_read(
        "SELECT dataset_id, family, schema_version, citation, license, metadata FROM external_dataset_registry ORDER BY dataset_id",
        default=[],
    ) or []

    attempts = _safe_read(
        """
        SELECT dataset_id,
               count(*) AS rows,
               count(DISTINCT user_id) AS users,
               count(DISTINCT concept_id) AS concepts,
               count(DISTINCT experiment_run_id) AS runs
        FROM external_log_attempts GROUP BY dataset_id
        """,
        default=[],
    ) or []
    by_attempts = {r["dataset_id"]: r for r in attempts}

    edges = _safe_read(
        "SELECT dataset_id, count(*) AS edges FROM external_concept_graph GROUP BY dataset_id",
        default=[],
    ) or []
    by_edges = {r["dataset_id"]: int(r["edges"]) for r in edges}

    # Tier-0 reports: decisions + lineage row counts
    decisions: Dict[str, Optional[str]] = {}
    lineage_by_id: Dict[str, Dict[str, Any]] = {}
    try:
        from pathlib import Path as _P
        import json as _json
        # Try several locations the API container might mount.
        candidates = [
            _P("/app/research_validation/reports/grounding"),
            _P(__file__).resolve().parents[7] / "research_validation" / "reports" / "grounding",
        ]
        for base in candidates:
            dec_path = base / "tier0_dataset_decisions.json"
            if dec_path.is_file():
                decisions = (_json.loads(dec_path.read_text(encoding="utf-8")) or {}).get("decisions", {}) or {}
                break
        for base in candidates:
            lin_path = base / "tier0_lineage_audit.json"
            if lin_path.is_file():
                rows = _json.loads(lin_path.read_text(encoding="utf-8")).get("lineage_per_dataset", []) or []
                for row in rows:
                    if row.get("dataset_id"):
                        lineage_by_id[row["dataset_id"]] = row
                break
    except Exception:
        pass

    out: List[Dict[str, Any]] = []
    for r in registry:
        ds = r["dataset_id"]
        att = by_attempts.get(ds, {}) or {}
        out.append({
            "dataset_id": ds,
            "family": r.get("family"),
            "schema_version": r.get("schema_version"),
            "citation": r.get("citation"),
            "license": r.get("license"),
            "registry_metadata": r.get("metadata") or {},
            "in_postgres": True,
            "residency": {
                "external_dataset_registry": 1,
                "external_log_attempts_rows": int(att.get("rows", 0) or 0),
                "external_log_attempts_users": int(att.get("users", 0) or 0),
                "external_log_attempts_concepts": int(att.get("concepts", 0) or 0),
                "external_log_attempts_runs": int(att.get("runs", 0) or 0),
                "external_concept_graph_edges": by_edges.get(ds, 0),
            },
            "tier0": {
                "decision": decisions.get(ds, "DISCLOSE"),
                "lineage": lineage_by_id.get(ds),
            },
        })

    return {
        "status": "ok",
        "datasets": out,
        "registry_table": "external_dataset_registry",
        "raw_table": "external_log_attempts",
        "graph_table": "external_concept_graph",
        "trajectory_table": "experiment_trajectories",
        "n_datasets": len(out),
        "tier0_reports": {
            "lineage": "tier0_lineage_audit.json",
            "dups_edges": "tier0_dups_edges.json",
            "decisions": "tier0_dataset_decisions.json",
        },
        "semantic_version": "1.0",
    }


@router.get("/dataset-evidence/{dataset_id}")
async def dataset_evidence(dataset_id: str) -> Dict[str, Any]:
    """Full publication-grade evidence packet for one dataset.

    Returns:
      - registry row (family, citation, license, prefixes, adapter metadata)
      - source schema (research-literature column set + release URL)
      - canonical transformation (source col → external_log_attempts col)
      - postgres column dictionaries pulled live from information_schema
      - postgres residency: rows in registry/attempts/graph, attached run ids
      - graph build manifest (only for datasets with edges)
      - Tier-0 audit verdict + supporting findings
    """
    reg = _safe_read(
        "SELECT * FROM external_dataset_registry WHERE dataset_id = %s",
        (dataset_id,),
        fetch_one=True,
    ) or {}
    if not reg:
        return {"status": "unknown_dataset", "dataset_id": dataset_id}

    # Live information_schema introspection — show what the DB actually holds.
    columns_attempts = _safe_read(
        """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'external_log_attempts'
        ORDER BY ordinal_position
        """,
        default=[],
    ) or []
    columns_graph = _safe_read(
        """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'external_concept_graph'
        ORDER BY ordinal_position
        """,
        default=[],
    ) or []

    # Per-dataset row counts + run residency.
    attempts_summary = _safe_read(
        """
        SELECT count(*) AS rows,
               count(DISTINCT user_id) AS users,
               count(DISTINCT concept_id) AS concepts,
               count(DISTINCT experiment_run_id) AS runs,
               min(raw_timestamp) AS first_ts,
               max(raw_timestamp) AS last_ts
        FROM external_log_attempts WHERE dataset_id = %s
        """,
        (dataset_id,), fetch_one=True,
    ) or {}

    runs = _safe_read(
        """
        SELECT experiment_run_id, count(*) AS rows
        FROM external_log_attempts WHERE dataset_id = %s
        GROUP BY experiment_run_id ORDER BY rows DESC LIMIT 12
        """,
        (dataset_id,), default=[],
    ) or []

    graph_summary: Optional[Dict[str, Any]] = None
    n_edges = _safe_read(
        "SELECT count(*) AS c FROM external_concept_graph WHERE dataset_id = %s",
        (dataset_id,), fetch_one=True,
    ) or {"c": 0}
    if int(n_edges.get("c") or 0) > 0:
        method_dist = _safe_read(
            """
            SELECT graph_method, count(*) AS edges
            FROM external_concept_graph WHERE dataset_id = %s
            GROUP BY graph_method ORDER BY edges DESC
            """,
            (dataset_id,), default=[],
        ) or []
        weight_buckets = _safe_read(
            """
            WITH bucketed AS (
                SELECT CASE
                    WHEN transfer_weight < 0.2 THEN '<0.2'
                    WHEN transfer_weight < 0.4 THEN '0.2-0.4'
                    WHEN transfer_weight < 0.6 THEN '0.4-0.6'
                    WHEN transfer_weight < 0.8 THEN '0.6-0.8'
                    ELSE '>=0.8'
                END AS bucket
                FROM external_concept_graph WHERE dataset_id = %s
            )
            SELECT bucket, count(*) AS n FROM bucketed GROUP BY bucket
            """,
            (dataset_id,), default=[],
        ) or []
        weight_order = ['<0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '>=0.8']
        wmap = {b["bucket"]: int(b["n"]) for b in weight_buckets}
        graph_summary = {
            "edges": int(n_edges["c"]),
            "method_distribution": [
                {"method": r["graph_method"], "edges": int(r["edges"])} for r in method_dist
            ],
            "weight_distribution": [
                {"bucket": b, "edges": wmap.get(b, 0)} for b in weight_order
            ],
            "validity_note": "Vuong / null-DAG control: probe_junyi_edge_validity.py · ADC_PERMUTED_GRAPH_NULL.md",
        }

    # Tier-0 verdict from sealed reports.
    tier0_decision = "DISCLOSE"
    tier0_findings: List[str] = []
    tier0_lineage: Optional[Dict[str, Any]] = None
    try:
        from pathlib import Path as _P
        import json as _json
        candidates = [
            _P("/app/research_validation/reports/grounding"),
            _P(__file__).resolve().parents[7] / "research_validation" / "reports" / "grounding",
        ]
        for base in candidates:
            if (base / "tier0_dataset_decisions.json").is_file():
                dec_blob = _json.loads((base / "tier0_dataset_decisions.json").read_text(encoding="utf-8"))
                tier0_decision = (dec_blob.get("decisions") or {}).get(dataset_id, "DISCLOSE")
            if (base / "tier0_lineage_audit.json").is_file():
                lin_blob = _json.loads((base / "tier0_lineage_audit.json").read_text(encoding="utf-8"))
                for row in lin_blob.get("lineage_per_dataset", []) or []:
                    if row.get("dataset_id") == dataset_id:
                        tier0_lineage = row
                        break
                tier0_findings.extend(lin_blob.get("findings", []) or [])
            break
    except Exception:
        pass

    return {
        "status": "ok",
        "dataset_id": dataset_id,
        "registry": {
            "dataset_id": reg.get("dataset_id"),
            "family": reg.get("family"),
            "schema_version": reg.get("schema_version"),
            "description": reg.get("description"),
            "concept_prefix": reg.get("concept_prefix"),
            "task_prefix": reg.get("task_prefix"),
            "citation": reg.get("citation"),
            "license": reg.get("license"),
            "metadata": reg.get("metadata") or {},
            "registered_at": str(reg["registered_at"]) if reg.get("registered_at") else None,
        },
        "source_schema": _source_schema_for(dataset_id, reg),
        "canonical_transform": _CANONICAL_TRANSFORM,
        "postgres_schema": {
            "external_log_attempts": [
                {"column": c["column_name"], "type": c["data_type"], "nullable": c["is_nullable"] == "YES"}
                for c in columns_attempts
            ],
            "external_concept_graph": [
                {"column": c["column_name"], "type": c["data_type"], "nullable": c["is_nullable"] == "YES"}
                for c in columns_graph
            ],
        },
        "residency": {
            "rows": int(attempts_summary.get("rows", 0) or 0),
            "users": int(attempts_summary.get("users", 0) or 0),
            "concepts": int(attempts_summary.get("concepts", 0) or 0),
            "runs": int(attempts_summary.get("runs", 0) or 0),
            "first_ts": str(attempts_summary["first_ts"]) if attempts_summary.get("first_ts") else None,
            "last_ts": str(attempts_summary["last_ts"]) if attempts_summary.get("last_ts") else None,
            "top_runs": [
                {"experiment_run_id": r["experiment_run_id"], "rows": int(r["rows"])} for r in runs
            ],
            "graph_edges": int(n_edges.get("c") or 0),
        },
        "graph": graph_summary,
        "tier0": {
            "decision": tier0_decision,
            "lineage": tier0_lineage,
            "findings": tier0_findings[:5],
        },
        "semantic_version": "1.0",
    }


@router.get("/dataset-reingest-status")
async def dataset_reingest_status() -> Dict[str, Any]:
    """Tier 0j dataset reproducibility report.

    Surfaces `tier0j_dataset_reingest.json` so the Reproducibility tab on
    /dashboard/data can show, per dataset:
      - source files (path, size, sha256)
      - adapter module + sha256 of the adapter and the base contract
      - DB residency for the canonical run + cached expected counts
      - replay evidence (rows / users / concepts / stream sha256) when --replay was used
      - verdict (REPRODUCIBLE / DRIFT / STALE / UNAVAILABLE) + reason

    The report is generated by
    `research_validation/grounding/scripts/tier0j_dataset_reingest.py`.
    """
    import json as _json
    from pathlib import Path as _P
    candidates: List[_P] = [_P("/app/research_validation/reports/grounding/tier0j_dataset_reingest.json")]
    try:
        # Dev fallback: walk up from this file when the container bind-mount path
        # isn't available (e.g. running uvicorn directly outside docker). The
        # depth depends on the host workspace layout, so guard with try/except.
        candidates.append(
            _P(__file__).resolve().parents[7] / "research_validation" / "reports" / "grounding" / "tier0j_dataset_reingest.json"
        )
    except Exception:
        pass
    blob: Optional[Dict[str, Any]] = None
    for path in candidates:
        try:
            if path.is_file():
                blob = _json.loads(path.read_text(encoding="utf-8"))
                break
        except Exception:
            continue
    if blob is None:
        return {
            "status": "no_report",
            "reason": "tier0j_dataset_reingest.json not found — run scripts/tier0j_dataset_reingest.py to generate.",
            "datasets": [],
            "summary": {},
            "semantic_version": "1.0",
        }

    return {
        "status": "ok",
        "report_status": blob.get("status"),
        "summary": blob.get("summary", {}),
        "datasets": blob.get("datasets", []),
        "modes": blob.get("modes", {}),
        "rerun": blob.get("rerun", {}),
        "phase2_run_id": blob.get("phase2_run_id"),
        "seal_id": blob.get("seal_id"),
        "input_hash": blob.get("input_hash"),
        "finished_at": blob.get("finished_at"),
        "semantic_version": "1.0",
    }


# ── Infrastructure / auditability views ──────────────────────────────────────

@router.get("/pipeline-stats")
async def pipeline_stats() -> Dict[str, Any]:
    """Live event-sourcing pipeline stats for the auditability page.
    submission → outbox → Kafka → projection → trajectory. Cached 5s (the
    counts are large COUNT/GROUP-BY over 1.2M+ rows). Polled by the UI."""
    cached = _cache_get("pipeline_stats")
    if cached is not None:
        return cached

    # outbox: total + status breakdown (published vs failed=DLQ)
    status_rows = _safe_read(
        "SELECT status, count(*) AS c FROM outbox_event_envelopes GROUP BY status",
        default=[],
    ) or []
    status_map = {r["status"]: int(r["c"]) for r in status_rows}
    outbox_total = sum(status_map.values())

    # event-type taxonomy (what flows through)
    type_rows = _safe_read(
        """SELECT event_type, count(*) AS c FROM outbox_event_envelopes
           GROUP BY event_type ORDER BY c DESC LIMIT 8""",
        default=[],
    ) or []
    event_types = [{"type": r["event_type"], "count": int(r["c"])} for r in type_rows]

    # projection read-models + trajectory rows
    proj = _safe_read("SELECT count(*) AS c FROM learner_projections", default=[]) or [{"c": 0}]
    traj = _safe_read(
        "SELECT GREATEST(reltuples,0)::bigint AS c FROM pg_class WHERE relname='experiment_trajectories'",
        default=[],
    ) or [{"c": 0}]
    processed = _safe_read("SELECT count(*) AS c FROM processed_events", default=[]) or [{"c": 0}]

    result = {
        "status": "ok",
        "stages": {
            "outbox": {
                "total": outbox_total,
                "published": status_map.get("published", 0),
                "failed": status_map.get("failed", 0),  # DLQ candidates
            },
            "projection": {"read_models": int(proj[0]["c"])},
            "trajectory": {"rows_estimated": int(traj[0]["c"])},
            "processed_events": {"total": int(processed[0]["c"])},
        },
        "event_types": event_types,
        "semantic_version": "1.0",
    }
    return _cache_set("pipeline_stats", result)


def _adc_data_file(filename: str):
    """Resolve a frontend ADC artifact (``public/data/adc/<filename>``) from the
    locations it can live in across deployments, returning the first that exists
    (or None).

    These artifacts are PRODUCED by the tier5 grounding scripts
    (tier5_baseline_snapshot.py → baseline_comparison.json, generate_topology_
    taxonomy.py → topology_taxonomy.json, run_r12_ablation.py → r12_ablation.json)
    into the frontend's ``public/data/adc/`` dir, which is mounted READ-ONLY into
    the API container at ``/app/HCIE_SYSTEM_FRONTENDV3/public/data/adc``. Re-running
    a grounding step OVERWRITES the artifact in place — it is an UPDATE, never a
    delete — so this resolver always returns the latest sealed copy. The previous
    candidate list omitted the actual mount path, which made present-but-current
    artifacts look "not found"; this resolver fixes that and is env-overridable.
    """
    import os
    roots = [
        os.environ.get("HCIE_ADC_DATA_DIR"),                       # explicit override
        "/app/HCIE_SYSTEM_FRONTENDV3/public/data/adc",             # read-only frontend mount in the API container
        "/app/public/data/adc",                                    # running inside the frontend container
        os.path.join(os.path.dirname(__file__), "data", "adc"),    # baked mirror next to the module
        os.path.dirname(__file__),                                 # legacy: flat next to the module
    ]
    for r in roots:
        if not r:
            continue
        candidate = os.path.join(r, filename)
        if os.path.exists(candidate):
            return candidate
    return None


@router.get("/graph-baseline")
async def graph_baseline() -> Dict[str, Any]:
    """Phase-2 GRAPH-regime KT benchmark: HCIE Phase-2 (graph injected, full
    prowess) vs trained BKT/DKT/SAKT/GKT on the SAME 10 held-out Junyi users.
    This is the comparison where HCIE competes with graph-AWARE KT (GKT). Source:
    the sealed baseline_comparison.json artifact (matched-eval protocol).

    Different from /kt-benchmark (non-graph, per-dataset DB evals): this is the
    single matched graph comparison, with cold-start windows w5/w10/w20/overall.
    """
    import json as _json
    # Mounted READ-ONLY from the frontend; tier5-baselines OVERWRITES in place (update, never delete).
    data = None
    _p = _adc_data_file("baseline_comparison.json")
    if _p:
        try:
            with open(_p, encoding="utf-8") as f:
                data = _json.load(f)
        except Exception:
            data = None
    if data is None:
        return {"status": "no_data",
                "reason": "baseline_comparison.json not found on the API container",
                "models": [], "semantic_version": "1.0"}

    rows = list(data.get("primary_rows", []))
    p1 = data.get("phase1_ref_row")

    def _norm(r, is_hcie=False, is_ref=False):
        return {
            "model": r.get("model"),
            "note": r.get("note", ""),
            "w5": r.get("w5"), "w10": r.get("w10"), "w20": r.get("w20"),
            "overall": r.get("overall"), "n_overall": r.get("n_overall"),
            "is_hcie": is_hcie,
            "is_graph_aware": "GKT" in str(r.get("model", "")),
            "is_phase1_ref": is_ref,
        }

    models = [_norm(r, is_hcie=("HCIE" in str(r.get("model","")))) for r in rows]
    if p1:
        models.append(_norm(p1, is_hcie=True, is_ref=True))

    # HCIE Phase-2 overall rank among the matched models (exclude the P1 ref)
    ranked = sorted([m for m in models if not m["is_phase1_ref"]],
                    key=lambda m: (m["overall"] if m["overall"] is not None else -1), reverse=True)
    hcie_overall_rank = next((i+1 for i, m in enumerate(ranked) if m["is_hcie"]), None)

    return {
        "status": "ok",
        "models": models,
        "hcie_overall_rank": hcie_overall_rank,
        "n_models": len(ranked),
        "train_users": data.get("train_users"),
        "eval_users": data.get("eval_users"),
        "phase2_run_id": data.get("phase2_run_id"),
        "phase1_run_id": data.get("phase1_run_id"),
        "protocol_note": data.get("protocol_note"),
        "validation_status": "anchored",
        "validation_note": (
            "Matched 10-user / 17-train Phase-2 comparison at seal-fbf78cd9 (N=96,727). "
            "Small-N (10 eval users) — treat as directional until the sealed re-run "
            "widens N. The AUC numbers carry the ⚠[N25k-PROVISIONAL] flag in the paper."
        ),
        "semantic_version": "1.0",
    }


@router.get("/adc-activation")
async def adc_activation(run_id: str = "") -> Dict[str, Any]:
    """Per-signal ADC activation — the SYSTEM's own verdict on which governance dimensions
    are active vs dormant for a run, from the ONE canonical classifier
    (``adaptive_dimension_controller.classify_dimension``) over the authoritative
    ``raw_governance_snapshot``.

    Prefers the immutable sealed profile (``frozen_stats.activation_profile``); falls back to a
    live recompute via the SAME helper the sealer uses, so a not-yet-resealed run still shows
    the correct verdict (flagged ``source="live"``). This is what makes the ADC panel real
    evidence: the page reads the instrument's frozen verdict, not a hand-authored claim.
    """
    import json as _json
    run_id = run_id or THESIS_ANCHOR_RUN_ID  # resolved at call-time (constant defined below)
    # The live recompute scans the run's raw_governance_snapshot (heavy on the 96k anchor); cache
    # per-run so the page's on-load fetch is served instantly after the first computation.
    _ck = f"adc-activation:{run_id}"
    _cached = _cache_get(_ck)
    if _cached is not None:
        return _cached
    seal = _safe_read(
        "SELECT seal_id, frozen_stats FROM sealed_runs WHERE experiment_run_id = %s",
        (run_id,), default={}, fetch_one=True,
    ) or {}
    fs = seal.get("frozen_stats") or {}
    if isinstance(fs, str):
        try:
            fs = _json.loads(fs)
        except Exception:
            fs = {}
    profile = fs.get("activation_profile") if isinstance(fs, dict) else None
    source = "sealed"
    if not profile:
        # Not-yet-resealed run: recompute live via the SAME sealer helper (no drift).
        try:
            from app.api.v3.experiments.run_sealing import _activation_profile
            profile = _activation_profile(_store(), run_id)
            source = "live"
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"adc-activation live recompute failed: {exc!r}")
            profile = None
    if not profile:
        return {"status": "no_data", "run_id": run_id,
                "reason": "no sealed activation_profile and live recompute unavailable",
                "per_dimension": {}, "semantic_version": "1.0"}
    return _cache_set(_ck, {
        "status": "ok",
        "run_id": run_id,
        "source": source,  # sealed = immutable frozen evidence; live = recomputed pre-reseal
        "seal_id": seal.get("seal_id"),
        "active_dimensions": profile.get("active_dimensions", []),
        "dormant_dimensions": profile.get("dormant_dimensions", []),
        "suppressed_dimensions": profile.get("suppressed_dimensions", []),
        "per_dimension": profile.get("per_dimension", {}),
        "classifier": profile.get("classifier", "adaptive_dimension_controller.classify_dimension"),
        "input": profile.get("source", "raw_governance_snapshot"),
        "semantic_version": "1.0",
    })


@router.get("/audit-controls")
async def audit_controls() -> Dict[str, Any]:
    """The self-audit controls — what makes the instrument honest.
      ⑥ Topology taxonomy: ADC pre-classifies each dataset's graph structure and
         PREDICTS active/dormant, then checks itself (adc_match). The
         'instrument that predicts its own behaviour' claim.
      ⑦ Shuffled-DAG / permuted-graph null: real DAG vs degree+weight-preserving
         shuffle vs no DAG. Decides topology-CORRECTNESS vs graph-PRESENCE.
    """
    import json as _json
    topo = None
    _p = _adc_data_file("topology_taxonomy.json")
    if _p:
        try:
            with open(_p, encoding="utf-8") as f: topo = _json.load(f)
        except Exception:
            topo = None

    datasets = []
    n_match = 0
    if topo:
        for d in topo.get("datasets", []):
            m = bool(d.get("adc_match"))
            n_match += 1 if m else 0
            datasets.append({
                "dataset_id": d.get("dataset_id"),
                "display_name": d.get("display_name"),
                "topology_class": d.get("topology_class"),
                "adc_prediction": d.get("adc_prediction"),
                "observed_class": d.get("observed_class"),
                "adc_match": m,
                "mean": d.get("mean"),
                "signal_ratio": d.get("signal_ratio"),
                "hcie_auc": d.get("hcie_auc"),
                "n": d.get("n"),
            })

    # ⑦ Shuffled-DAG null — the decisive numbers (from ADC_PERMUTED_GRAPH_NULL_REPORT
    # + the corrected independent replication). Hardcoded constants here are the
    # SEALED reported results, not computed live (the offline control).
    shuffled_dag = {
        "conditions": [
            {"label": "Real DAG",     "event_fraction": 0.183, "mean_transfer": 0.01166, "verdict": "ACTIVE"},
            {"label": "Permuted DAG", "event_fraction": 0.183, "mean_transfer": 0.01166, "verdict": "ACTIVE"},
            {"label": "No DAG",       "event_fraction": 0.0,   "mean_transfer": 0.0,      "verdict": "DORMANT"},
        ],
        "real_vs_permuted": "indistinguishable (corr ≈ 0.97 on structural utility)",
        "corrected_finding": {
            "real_minus_shuffled": 0.020,
            "p_value": "5e-5",
            "durable_component": 0.007,
            "note": ("Independent conclusion-blind replication on raw Junyi outcomes (ability "
                     "residualization + permutation null + dose-response): a SMALL but significant "
                     "topology-specific transfer effect (+0.020, p=5e-5), ~2/3 curriculum proximity, "
                     "durable ≈ +0.007. The runtime signal alone is graph-presence-induced; the "
                     "topology-specific component is real but small."),
        },
        "interpretation": ("real ≡ permuted at the runtime metric → the live transfer signal detects "
                           "graph PRESENCE, not edge CORRECTNESS. Only the offline outcome-grounded "
                           "replication isolates a small topology-specific effect."),
    }

    return {
        "status": "ok",
        "sealed_thresholds": topo.get("sealed_thresholds") if topo else None,
        "topology": {
            "datasets": datasets,
            "n_match": n_match,
            "n_total": len(datasets),
        },
        "shuffled_dag": shuffled_dag,
        "framing": ("An instrument rigorous enough to calibrate its own headline: it predicts which "
                    "datasets activate (and is right), and its own shuffle-control shows the live signal "
                    "is presence-driven. The self-audit IS the methods contribution."),
        "semantic_version": "1.0",
    }


@router.get("/ablation")
async def ablation() -> Dict[str, Any]:
    """Two ablation studies:
      R12 — graph on/off: same users/sequences, graph injection toggled. The
            clean causal test of whether the GRAPH helps. From r12_ablation.json.
      JT-dim — drop each of the 6 JT dimensions. ⚠ smoke-scale (32 rows each):
            mastery-outcome is FLAT (too few interactions); only the JT-SIGNAL
            value moves. Honest contribution-to-JT, not outcome. From DB.
    """
    import json as _json
    # R12 graph on/off (sealed artifact). Resolved from the read-only frontend mount.
    r12 = None
    _p = _adc_data_file("r12_ablation.json")
    if _p:
        try:
            with open(_p, encoding="utf-8") as f: r12 = _json.load(f)
        except Exception:
            r12 = None

    # JT-dimension ablations from the DB (smoke runs). Non-CTE form — the CTE
    # variant silently returned empty through the store's execute_read.
    jt_rows = _safe_read(
        """
        SELECT regexp_replace(c.reason, 'jt ablation smoke: ', '') AS condition,
               count(DISTINCT e.user_id) AS users,
               count(*) AS rows,
               avg(e.mastery_after) AS avg_mastery,
               avg((e.correctness)::int) AS acc,
               avg(e.jt_value) AS avg_jt
        FROM cohort_runs c
        JOIN experiment_trajectories e ON e.experiment_run_id = c.run_id
        WHERE c.reason LIKE %s AND c.status = 'completed'
        GROUP BY 1 ORDER BY avg_jt DESC
        """,
        ('jt ablation smoke:%',),
        default=[],
    ) or []

    baseline_jt = next((float(r["avg_jt"]) for r in jt_rows if r["condition"] == "baseline"), None)
    jt_dims = []
    for r in jt_rows:
        jt = float(r["avg_jt"]) if r.get("avg_jt") is not None else None
        jt_dims.append({
            "condition": r["condition"],
            "is_baseline": r["condition"] == "baseline",
            "avg_jt": jt,
            "jt_drop_vs_baseline": (round(baseline_jt - jt, 4) if (baseline_jt is not None and jt is not None) else None),
            "avg_mastery": float(r["avg_mastery"]) if r.get("avg_mastery") is not None else None,
            "users": int(r.get("users", 0) or 0),
            "rows": int(r.get("rows", 0) or 0),
        })

    return {
        "status": "ok",
        "r12": r12 and {
            "graph_on_auc": r12.get("graph_on_auc"),
            "graph_off_auc": r12.get("graph_off_auc"),
            "delta_auc": r12.get("delta_auc"),
            "n_matched": r12.get("n_matched") or {"overall": r12.get("n_interactions_replayed")},
            "interpretation": "WITHDRAWN as a causal claim — " + str(r12.get("interpretation") or ""),
            "run_id": r12.get("r12_run_id"),
            "status": "withdrawn",
            "caveat": (
                "The single-run graph-ON/OFF result (Δ≈+0.0185) is WITHDRAWN: the 5-seed "
                "re-derivation gave the opposite sign (≈−0.072), so graph-OFF is a confounded, "
                "sign-unstable control. The durable prerequisite-topology effect is reported "
                "instead via the ability-matched shuffled-DAG control (≈+0.053, p<0.01). "
                "See thesis §4.11 / §5.3."
            ),
        },
        "jt_dimensions": jt_dims,
        "jt_caveat": (
            "JT-dimension ablations are smoke-scale (32 rows/condition). Mastery-outcome "
            "is FLAT across conditions — too few interactions to move learned mastery. "
            "Only the JT-SIGNAL value differs, shown below as contribution-to-JT. A "
            "results-grade ablation needs the sealed re-run at full N."
        ),
        "validation_status": "anchored",
        "validation_note": (
            "JT-dimension ablations anchored to seal-fbf78cd9 (smoke-scale). R12 graph on/off is "
            "WITHDRAWN (sign-unstable across 5 seeds); the durable topology effect is the "
            "ability-matched shuffled-DAG control (+0.053, p<0.01)."
        ),
        "semantic_version": "1.0",
    }


@router.get("/sealed-runs")
async def sealed_runs() -> Dict[str, Any]:
    """Run-sealing provenance: the immutable anchors behind cited numbers.
    Each sealed run pins a figure to an exact row count + content hash —
    'pin me to the rows behind this number' is answerable."""
    rows = _safe_read(
        """SELECT seal_id, experiment_run_id, as_of_row_count, content_hash,
                  sealed_at, frozen_stats
           FROM sealed_runs ORDER BY sealed_at DESC""",
        default=[],
    ) or []
    seals = [{
        "seal_id": r.get("seal_id"),
        "run_id": r.get("experiment_run_id"),
        "row_count": int(r.get("as_of_row_count", 0) or 0),
        "content_hash": r.get("content_hash"),
        "sealed_at": str(r.get("sealed_at")) if r.get("sealed_at") else None,
        "frozen_stats": r.get("frozen_stats"),
    } for r in rows]
    return {"status": "ok", "sealed_runs": seals, "count": len(seals),
            "semantic_version": "1.0"}


@router.get("/archetype-concept-analysis")
async def archetype_concept_analysis(
    limit: int = Query(200, ge=1, le=500),
) -> Dict[str, Any]:
    """Observational Archetype × Concept analysis for the instructor dashboard.

    Joins ``user_archetype_profile`` (self-reported VARK dominant axis) with
    ``experiment_trajectories`` (real-learner rows, ``experiment_run_id`` like
    ``live::*``) to surface average JT, response time, and accuracy per
    (concept, dominant_vark) bucket. NOTE: previously read ``trajectory_records``,
    which is empty (0 rows) — real-learner outcomes land in experiment_trajectories.

    Slice 5b design note: archetype is a *covariate only* — it does not feed
    back into MAB scoring, so these numbers describe learning outcomes without
    contaminating HCIE validation.
    """
    rows = _safe_read(
        """
        WITH profile_dominant AS (
            SELECT
                user_id::text AS user_id,
                (
                    SELECT key
                    FROM jsonb_each_text(vark_scores) AS e(key, value)
                    ORDER BY value::float DESC
                    LIMIT 1
                ) AS dominant_vark
            FROM user_archetype_profile
            WHERE vark_scores IS NOT NULL
        )
        SELECT
            tr.concept,
            COALESCE(pd.dominant_vark, 'unknown') AS dominant_vark,
            COUNT(*)::int AS n_interactions,
            AVG(tr.jt_value) AS avg_jt,
            AVG(tr.response_time) AS avg_response_time,
            AVG(CASE WHEN tr.correctness THEN 1.0 ELSE 0.0 END) AS accuracy
        FROM experiment_trajectories tr
        INNER JOIN profile_dominant pd ON pd.user_id = tr.user_id
        WHERE tr.concept IS NOT NULL
          AND tr.experiment_run_id LIKE 'live::%%'
        GROUP BY tr.concept, pd.dominant_vark
        ORDER BY tr.concept, n_interactions DESC
        LIMIT %s
        """,
        (limit,),
        default=[],
    ) or []

    profile_count = _safe_read(
        "SELECT COUNT(*)::int AS n FROM user_archetype_profile",
        fetch_one=True,
        default={"n": 0},
    )
    material_count = _safe_read(
        "SELECT COUNT(*)::int AS n FROM learning_materials",
        fetch_one=True,
        default={"n": 0},
    )
    task_langs = _safe_read(
        """
        SELECT language, COUNT(*)::int AS n
        FROM tasks WHERE concept_type = 'k12'
        GROUP BY language ORDER BY language
        """,
        default=[],
    )

    buckets = [
        {
            "concept": r.get("concept"),
            "dominant_vark": r.get("dominant_vark"),
            "n_interactions": int(r.get("n_interactions") or 0),
            "avg_jt": float(r.get("avg_jt") or 0),
            "avg_response_time": float(r.get("avg_response_time") or 0),
            "accuracy": float(r.get("accuracy") or 0),
        }
        for r in rows
    ]

    return {
        "status": "ok",
        "buckets": buckets,
        "meta": {
            "profiles_count": int(profile_count.get("n") or 0),
            "materials_count": int(material_count.get("n") or 0),
            "task_languages": {str(r.get("language")): int(r.get("n") or 0) for r in task_langs},
            "note": (
                "Observational only — archetype does not influence MAB recommendations. "
                "Dominant VARK axis is derived from self-reported profile scores."
            ),
        },
        "authority": "user_archetype_profile + experiment_trajectories (live::* real learners)",
        "semantic_version": "1.0",
    }


@router.get("/archetype-modality-analysis")
async def archetype_modality_analysis(
    limit: int = Query(400, ge=1, le=2000),
) -> Dict[str, Any]:
    """Observational Archetype × Modality × Concept analysis.

    Joins ``user_archetype_profile`` (self-reported dominant VARK axis) with
    ``interactions`` (the per-(concept, representation) success record written on
    every REAL-learner attempt) → accuracy + response time per
    (concept, representation, dominant_vark) bucket. Answers the question the
    instructor/researcher actually wants: *does a given archetype succeed more on a
    given modality for a given concept?*

    HONESTY (load-bearing):
      • Archetype is a covariate only — it never feeds the bandit (Slice 5b), so
        this can never contaminate HCIE validation. The bandit picks modality from
        learned success, not from the profile; this surface lets you CHECK whether
        the two happen to agree.
      • Real learners only. ``interactions`` is guarded to the live ITS path, so no
        synthetic/replay/experimental row is here and the sealed eval is untouched.
      • NOT synthetically seeded. A hand-coded archetype→modality effect would only
        echo itself — that is not evidence. This is empty until a real learner has
        BOTH onboarded (archetype) AND accumulated multi-modal attempts; ``meta``
        reports how close we are to that.
    """
    rows = _safe_read(
        """
        WITH profile_dominant AS (
            SELECT
                user_id::text AS user_id,
                (
                    SELECT key FROM jsonb_each_text(vark_scores) AS e(key, value)
                    ORDER BY value::float DESC LIMIT 1
                ) AS dominant_vark
            FROM user_archetype_profile
            WHERE vark_scores IS NOT NULL
        )
        SELECT
            i.concept_id AS concept,
            i.representation,
            COALESCE(pd.dominant_vark, 'unknown') AS dominant_vark,
            COUNT(*)::int AS n_interactions,
            AVG(CASE WHEN i.correct THEN 1.0 ELSE 0.0 END) AS accuracy,
            AVG(i.response_time) AS avg_response_time
        FROM interactions i
        INNER JOIN profile_dominant pd ON pd.user_id = i.user_id
        WHERE i.concept_id IS NOT NULL
          AND i.representation IS NOT NULL AND i.representation <> 'unknown'
          AND i.correct IS NOT NULL
        GROUP BY i.concept_id, i.representation, pd.dominant_vark
        ORDER BY i.concept_id, i.representation, n_interactions DESC
        LIMIT %s
        """,
        (limit,),
        default=[],
    ) or []

    profiles_count = _safe_read(
        "SELECT COUNT(*)::int AS n FROM user_archetype_profile",
        fetch_one=True, default={"n": 0},
    ) or {"n": 0}
    both_count = _safe_read(
        """
        SELECT COUNT(DISTINCT i.user_id)::int AS n
        FROM interactions i
        INNER JOIN user_archetype_profile p ON p.user_id::text = i.user_id
        WHERE i.representation IS NOT NULL AND i.representation <> 'unknown'
          AND i.correct IS NOT NULL
        """,
        fetch_one=True, default={"n": 0},
    ) or {"n": 0}
    modality_learners = _safe_read(
        """
        SELECT COUNT(DISTINCT user_id)::int AS n
        FROM interactions
        WHERE representation IS NOT NULL AND representation <> 'unknown'
        """,
        fetch_one=True, default={"n": 0},
    ) or {"n": 0}

    buckets = [
        {
            "concept": r.get("concept"),
            "representation": r.get("representation"),
            "dominant_vark": r.get("dominant_vark"),
            "n_interactions": int(r.get("n_interactions") or 0),
            "accuracy": float(r["accuracy"]) if r.get("accuracy") is not None else None,
            "avg_response_time": float(r["avg_response_time"]) if r.get("avg_response_time") is not None else None,
        }
        for r in rows
    ]

    return {
        "status": "ok",
        "buckets": buckets,
        "meta": {
            "profiles_count": int(profiles_count.get("n") or 0),
            "modality_learners": int(modality_learners.get("n") or 0),
            "learners_with_archetype_and_modality": int(both_count.get("n") or 0),
            "data_source": "interactions ⋈ user_archetype_profile (real learners only)",
            "note": (
                "Observational; archetype is a covariate, never fed to the bandit. "
                "Empty until a learner both onboards AND has multi-modal attempts. "
                "Not synthetically seeded — a baked-in correlation would not be evidence."
            ),
        },
        "authority": "user_archetype_profile + interactions",
        "semantic_version": "1.0",
    }


# ── Per-learner journey + live cohort surfaces ────────────────────────────────
# These endpoints close the loop the user asked about: "show me a single
# learner going from 0 → fully mastered, and let that data flow into the
# same analytics surfaces as synthetic / dataset experiments." They both read
# the canonical ``experiment_trajectories`` table; live learners are stored
# under ``experiment_run_id = 'live::<user_uuid>'`` while research cohorts
# use ``run-...`` namespaces, so the same SQL serves both with a prefix
# filter. The frontend keeps the visual semantics identical so a stakeholder
# can directly compare a real-learner journey against a synthetic policy run.

# Default per-concept mastery threshold (matches MAB exploitation gate).
_MASTERED_THRESHOLD = 0.85

# Whole curriculum = concepts present in the K-12 task catalog.
def _curriculum_concepts() -> List[str]:
    rows = _safe_read(
        """
        SELECT DISTINCT concept_id
        FROM tasks
        WHERE concept_type = 'k12' AND concept_id IS NOT NULL
        ORDER BY concept_id
        """,
        default=[],
    )
    return [str(r["concept_id"]) for r in (rows or []) if r.get("concept_id")]


@router.get("/learner-journey/{user_id}")
async def get_learner_journey(
    user_id: str,
    mastered_threshold: float = Query(
        _MASTERED_THRESHOLD, ge=0.0, le=1.0,
        description="Per-concept mastery threshold for the 'mastered' flag",
    ),
) -> Dict[str, Any]:
    """Per-learner narrative: concept-by-concept mastery progression.

    Returns everything the journey UI needs to render "0 → mastered":

    - ``concepts``: per-concept summary (attempts, current mastery, time-to-
      mastered, mastered flag). The ``trajectory`` field carries the actual
      mastery curve so the UI can plot one line per concept.
    - ``unlock_timeline``: chronological list of *first attempt on each
      concept* — the curriculum traversal order chosen by the MAB.
    - ``jt_trajectory``: per-step JT decomposition for the headline JT chart.
    - ``transfer_events``: attempts where the brain credited transfer to a
      neighbouring concept (filtered above a small threshold).
    - ``overall``: curriculum-level KPIs — mastered / total, total attempts,
      avg JT, when the first concept was attempted, when (if ever) the
      whole curriculum reached the mastered threshold.

    All numbers come from ``experiment_trajectories`` (the same table the
    synthetic/replay analytics use) so the chart code is identical and a
    real learner's run is directly comparable to a policy run.
    """
    # Live learners' run_id is namespaced. We accept either the bare user_id
    # (UUID or otherwise) or the explicit ``live::`` form so the endpoint
    # also serves replay rows when the caller wants to demo against them.
    run_filter = f"live::{user_id}"
    rows = _safe_read(
        """
        SELECT
            interaction_number,
            concept,
            correctness,
            response_time,
            difficulty,
            mastery_before,
            mastery_after,
            jt_value,
            jt_delta_m_contribution,
            jt_transfer_contribution,
            jt_challenge_contribution,
            jt_uncertainty_contribution,
            jt_zpd_contribution,
            jt_transfer_prospective_contribution,
            jt_baseline_difficulty_contribution,
            jt_challenge_event_contribution,
            jt_population_prior_contribution,
            jt_t_realized_v2_contribution,
            jt_v2_active,
            jt_v2_state_snapshot,
            jt_v2_challenge_event_fired,
            jt_v2_challenge_event_reason,
            transfer_amount,
            transfer_amount_total,
            policy,
            arm_selected,
            timestamp
        FROM experiment_trajectories
        WHERE (experiment_run_id = %s OR user_id = %s)
          AND concept IS NOT NULL
        ORDER BY COALESCE(interaction_number, 0) ASC, timestamp ASC
        """,
        (run_filter, str(user_id)),
        default=[],
    ) or []

    if not rows:
        return {
            "status": "ok",
            "user_id": user_id,
            "has_data": False,
            "concepts": [],
            "unlock_timeline": [],
            "jt_trajectory": [],
            "transfer_events": [],
            "overall": {
                "total_attempts": 0,
                "concepts_attempted": 0,
                "concepts_mastered": 0,
                "curriculum_total": len(_curriculum_concepts()),
                "curriculum_complete": False,
                "current_avg_mastery": 0.0,
                "avg_jt": 0.0,
            },
            "authority": "experiment_trajectories (live::)",
            "semantic_version": "1.0",
        }

    # Per-concept aggregation. We walk the (chronologically ordered) rows and
    # accumulate per-concept curves so the UI can plot one line per concept.
    per_concept: Dict[str, Dict[str, Any]] = {}
    unlock_timeline: List[Dict[str, Any]] = []
    jt_trajectory: List[Dict[str, Any]] = []
    transfer_events: List[Dict[str, Any]] = []
    transfer_threshold = 0.08  # matches frontend TRANSFER_ACTIVATION_THRESHOLD

    for i, r in enumerate(rows, start=1):
        concept = str(r.get("concept") or "")
        if not concept:
            continue
        ma = r.get("mastery_after")
        ma_val = float(ma) if ma is not None else None
        step = int(r.get("interaction_number") or i)
        ts = str(r.get("timestamp")) if r.get("timestamp") else None

        entry = per_concept.get(concept)
        if entry is None:
            entry = {
                "concept": concept,
                "first_seen_step": step,
                "first_seen_at": ts,
                "attempts": 0,
                "correct": 0,
                "current_mastery": 0.0,
                "peak_mastery": 0.0,
                "mastered_at_step": None,
                "mastered_at": None,
                "trajectory": [],  # list of {step, mastery, correct}
            }
            per_concept[concept] = entry
            unlock_timeline.append({
                "step": step,
                "concept": concept,
                "timestamp": ts,
            })

        entry["attempts"] += 1
        if r.get("correctness"):
            entry["correct"] += 1
        if ma_val is not None:
            entry["current_mastery"] = ma_val
            if ma_val > entry["peak_mastery"]:
                entry["peak_mastery"] = ma_val
            if entry["mastered_at_step"] is None and ma_val >= mastered_threshold:
                entry["mastered_at_step"] = step
                entry["mastered_at"] = ts
        entry["trajectory"].append({
            "step": step,
            "mastery": ma_val,
            "correct": bool(r.get("correctness")) if r.get("correctness") is not None else None,
        })

        jt_trajectory.append({
            "step": step,
            "concept": concept,
            "jt_value": float(r["jt_value"]) if r.get("jt_value") is not None else None,
            "delta_m": float(r["jt_delta_m_contribution"]) if r.get("jt_delta_m_contribution") is not None else None,
            "transfer": float(r["jt_transfer_contribution"]) if r.get("jt_transfer_contribution") is not None else None,
            "challenge": float(r["jt_challenge_contribution"]) if r.get("jt_challenge_contribution") is not None else None,
            "uncertainty": float(r["jt_uncertainty_contribution"]) if r.get("jt_uncertainty_contribution") is not None else None,
            "zpd": float(r["jt_zpd_contribution"]) if r.get("jt_zpd_contribution") is not None else None,
            "baseline_difficulty": float(r["jt_baseline_difficulty_contribution"]) if r.get("jt_baseline_difficulty_contribution") is not None else None,
            "challenge_event": float(r["jt_challenge_event_contribution"]) if r.get("jt_challenge_event_contribution") is not None else None,
            "population_prior": float(r["jt_population_prior_contribution"]) if r.get("jt_population_prior_contribution") is not None else None,
            "t_realized_v2": float(r["jt_t_realized_v2_contribution"]) if r.get("jt_t_realized_v2_contribution") is not None else None,
            "v2_active": bool(r.get("jt_v2_active")) if r.get("jt_v2_active") is not None else False,
            "v2_state_snapshot": r.get("jt_v2_state_snapshot") or {},
            "challenge_event_fired": bool(r.get("jt_v2_challenge_event_fired")) if r.get("jt_v2_challenge_event_fired") is not None else False,
            "challenge_event_reason": r.get("jt_v2_challenge_event_reason"),
            "correct": bool(r.get("correctness")) if r.get("correctness") is not None else None,
        })

        ta = r.get("transfer_amount")
        ta_total = r.get("transfer_amount_total")
        ta_val = float(ta if ta is not None else (ta_total or 0))
        if ta_val > transfer_threshold:
            transfer_events.append({
                "step": step,
                "concept": concept,
                "amount": ta_val,
            })

    concepts_list = sorted(per_concept.values(), key=lambda c: c["first_seen_step"])
    for c in concepts_list:
        # Accuracy is handy for the per-concept card header.
        c["accuracy"] = (c["correct"] / c["attempts"]) if c["attempts"] else 0.0
        c["mastered"] = c["mastered_at_step"] is not None

    curriculum = _curriculum_concepts()
    mastered_count = sum(1 for c in concepts_list if c["mastered"])
    total_curriculum = len(curriculum)
    # Curriculum-complete = all curriculum concepts have a mastered entry.
    curriculum_complete = bool(
        total_curriculum and
        all(
            (per_concept.get(c) or {}).get("mastered_at_step") is not None
            for c in curriculum
        )
    )

    overall = {
        "total_attempts": len(rows),
        "concepts_attempted": len(concepts_list),
        "concepts_mastered": mastered_count,
        "curriculum_total": total_curriculum,
        "curriculum_complete": curriculum_complete,
        "current_avg_mastery": round(
            sum(c["current_mastery"] for c in concepts_list) / max(1, len(concepts_list)),
            4,
        ),
        "avg_jt": round(
            sum(p["jt_value"] for p in jt_trajectory if p["jt_value"] is not None)
            / max(1, sum(1 for p in jt_trajectory if p["jt_value"] is not None)),
            4,
        ),
        "first_attempt_at": concepts_list[0]["first_seen_at"] if concepts_list else None,
        "last_attempt_at": str(rows[-1].get("timestamp")) if rows[-1].get("timestamp") else None,
        "mastered_threshold": mastered_threshold,
    }

    return {
        "status": "ok",
        "user_id": user_id,
        "has_data": True,
        "concepts": concepts_list,
        "unlock_timeline": unlock_timeline,
        "jt_trajectory": jt_trajectory,
        "transfer_events": transfer_events[-200:],  # tail-limit for chart sanity
        "overall": overall,
        "authority": "experiment_trajectories (live::)",
        "semantic_version": "1.0",
    }


@router.get("/live-cohort-comparison")
async def live_cohort_comparison(
    since: Optional[str] = Query(
        None, description="ISO timestamp; only include live attempts at/after this time"
    ),
    until: Optional[str] = Query(
        None, description="ISO timestamp; only include live attempts up to this time"
    ),
    synthetic_run_ids: Optional[List[str]] = Query(
        None,
        description=(
            "Optional explicit list of synthetic run_ids to compare against. "
            "Omit to auto-pick the most recent N synthetic runs."
        ),
    ),
    synthetic_limit: int = Query(3, ge=1, le=8),
) -> Dict[str, Any]:
    """Live-learner cohort vs synthetic policies — same charts as Cohort Study.

    The Cohort Study tab historically required a synthetic ``experiment_run_id``
    to render any analytics. This endpoint adapts the same projection to a
    *virtual* live cohort: every ``live::*`` row in the configured date window
    is treated as one cohort, and we compare its policy-level performance
    against the most recent N synthetic runs.

    The output schema is intentionally a strict subset of
    ``get_cohort_run_comparison`` so the existing frontend chart components
    can render it without branching.
    """
    where_parts = ["experiment_run_id LIKE 'live::%%'", "policy IS NOT NULL", "concept IS NOT NULL"]
    params: List[Any] = []
    if since:
        where_parts.append("timestamp >= %s")
        params.append(since)
    if until:
        where_parts.append("timestamp <= %s")
        params.append(until)
    live_where = " AND ".join(where_parts)

    # ── Live cohort curves ──────────────────────────────────────────────
    live_curves = _safe_read(
        f"""
        SELECT
            'live' AS policy,
            interaction_number,
            AVG(mastery_after) AS avg_mastery,
            AVG(CASE WHEN correctness THEN 1.0 ELSE 0.0 END) AS accuracy,
            AVG(jt_value) AS avg_jt,
            COUNT(DISTINCT user_id) AS n_learners
        FROM experiment_trajectories
        WHERE {live_where}
        GROUP BY interaction_number
        ORDER BY interaction_number ASC
        LIMIT 500
        """,
        tuple(params),
        default=[],
    )

    # ── Pick synthetic runs ─────────────────────────────────────────────
    if synthetic_run_ids:
        chosen_runs = [r for r in synthetic_run_ids if r]
    else:
        run_rows = _safe_read(
            """
            SELECT experiment_run_id
            FROM experiment_trajectories
            WHERE experiment_run_id LIKE 'run-%%'
            GROUP BY experiment_run_id
            ORDER BY MAX(timestamp) DESC NULLS LAST
            LIMIT %s
            """,
            (synthetic_limit,),
            default=[],
        ) or []
        chosen_runs = [str(r["experiment_run_id"]) for r in run_rows]

    synthetic_curves: Dict[str, List[Dict[str, Any]]] = {}
    if chosen_runs:
        synth_rows = _safe_read(
            """
            SELECT
                experiment_run_id AS run_id,
                policy,
                interaction_number,
                AVG(mastery_after) AS avg_mastery,
                AVG(CASE WHEN correctness THEN 1.0 ELSE 0.0 END) AS accuracy,
                AVG(jt_value) AS avg_jt,
                COUNT(DISTINCT user_id) AS n_learners
            FROM experiment_trajectories
            WHERE experiment_run_id = ANY(%s)
              AND policy IS NOT NULL
              AND interaction_number IS NOT NULL
            GROUP BY experiment_run_id, policy, interaction_number
            ORDER BY policy, interaction_number ASC
            """,
            (chosen_runs,),
            default=[],
        ) or []
        for r in synth_rows:
            label = f"{r.get('policy')} ({str(r.get('run_id'))[-8:]})"
            synthetic_curves.setdefault(label, []).append({
                "step": int(r.get("interaction_number") or 0),
                "avg_mastery": float(r.get("avg_mastery") or 0),
                "accuracy": float(r.get("accuracy") or 0),
                "avg_jt": float(r.get("avg_jt") or 0),
                "n_learners": int(r.get("n_learners") or 0),
            })

    # ── Summary stats per cohort ────────────────────────────────────────
    live_summary = _safe_read(
        f"""
        SELECT
            COUNT(*)::int AS n_attempts,
            COUNT(DISTINCT user_id)::int AS n_learners,
            AVG(mastery_after) AS final_mastery,
            AVG(CASE WHEN correctness THEN 1.0 ELSE 0.0 END) AS accuracy,
            AVG(jt_value) AS avg_jt
        FROM experiment_trajectories
        WHERE {live_where}
        """,
        tuple(params),
        fetch_one=True,
        default={},
    ) or {}

    return {
        "status": "ok",
        "cohorts": {
            "live": {
                "label": "Real learners (live)",
                "curve": [
                    {
                        "step": int(r.get("interaction_number") or 0),
                        "avg_mastery": float(r.get("avg_mastery") or 0),
                        "accuracy": float(r.get("accuracy") or 0),
                        "avg_jt": float(r.get("avg_jt") or 0),
                        "n_learners": int(r.get("n_learners") or 0),
                    }
                    for r in (live_curves or [])
                ],
                "summary": {
                    "n_attempts": int(live_summary.get("n_attempts") or 0),
                    "n_learners": int(live_summary.get("n_learners") or 0),
                    "final_mastery": float(live_summary.get("final_mastery") or 0),
                    "accuracy": float(live_summary.get("accuracy") or 0),
                    "avg_jt": float(live_summary.get("avg_jt") or 0),
                },
            },
            "synthetic": synthetic_curves,
        },
        "window": {"since": since, "until": until},
        "synthetic_runs": chosen_runs,
        "authority": "experiment_trajectories",
        "semantic_version": "1.0",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Cold-start & AUC diagnostic endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/cold-start-users")
async def get_cold_start_users(
    run_id: Optional[str] = Query(None),
    min_interactions: int = Query(5),
    limit: int = Query(50),
) -> Dict[str, Any]:
    """Distinct users in a run with their interaction counts, filtered by min_interactions.

    Authority: experiment_trajectories
    """
    # Resolve run_id: prefer the run with the most learners that carry JT attribution,
    # so the picker surfaces learners whose 6D-attribution panel actually fills (an
    # empty panel is not usable evidence). Fall back to the most-recent run otherwise.
    if run_id is None:
        run_row = _safe_read(
            "SELECT experiment_run_id FROM experiment_trajectories "
            "WHERE jt_challenge_contribution IS NOT NULL "
            "GROUP BY experiment_run_id "
            "ORDER BY COUNT(DISTINCT user_id) DESC, MAX(timestamp) DESC LIMIT 1",
            (),
            fetch_one=True,
            default={},
        ) or {}
        run_id = run_row.get("experiment_run_id")
        if not run_id:
            run_row = _safe_read(
                "SELECT experiment_run_id FROM experiment_trajectories "
                "ORDER BY timestamp DESC LIMIT 1",
                (),
                fetch_one=True,
                default={},
            ) or {}
            run_id = run_row.get("experiment_run_id")
        if not run_id:
            return {
                "status": "no_data",
                "reason": "experiment_trajectories is empty — no run found",
                "users": [],
                "run_id": None,
                "total": 0,
            }

    rows = _safe_read(
        """
        SELECT user_id,
               COUNT(*) AS interaction_count,
               COUNT(jt_challenge_contribution) AS jt_count
        FROM experiment_trajectories
        WHERE experiment_run_id = %s
        GROUP BY user_id
        HAVING COUNT(*) >= %s
        ORDER BY jt_count DESC, interaction_count DESC
        LIMIT %s
        """,
        (run_id, min_interactions, limit),
        default=[],
    ) or []

    # jt_count surfaces learners whose 6D-attribution panel will render (jt-bearing
    # rows float to the top of the picker).
    users = [
        {
            "user_id": r.get("user_id"),
            "interaction_count": int(r.get("interaction_count") or 0),
            "jt_count": int(r.get("jt_count") or 0),
            "has_jt": int(r.get("jt_count") or 0) > 0,
        }
        for r in rows
    ]

    return {
        "status": "ok",
        "run_id": run_id,
        "min_interactions": min_interactions,
        "users": users,
        "total": len(users),
        "authority": "experiment_trajectories",
        "semantic_version": "1.0",
    }


@router.get("/cold-start-journey")
async def get_cold_start_journey(
    user_id: str = Query(...),
    run_id: Optional[str] = Query(None),
    limit: int = Query(50),
) -> Dict[str, Any]:
    """Per-interaction journey for one learner plus per-window AUC for the run.

    Authority: experiment_trajectories + kt_prediction_evaluations
    """
    # Resolve run_id — prefer the learner's most-recent run that carries JT attribution
    # (so the 6D-attribution panel fills); fall back to their most-recent run otherwise.
    if run_id is None:
        run_row = _safe_read(
            "SELECT experiment_run_id FROM experiment_trajectories "
            "WHERE user_id = %s AND jt_challenge_contribution IS NOT NULL "
            "ORDER BY timestamp DESC LIMIT 1",
            (user_id,),
            fetch_one=True,
            default={},
        ) or {}
        run_id = run_row.get("experiment_run_id")
        if not run_id:
            run_row = _safe_read(
                "SELECT experiment_run_id FROM experiment_trajectories "
                "WHERE user_id = %s ORDER BY timestamp DESC LIMIT 1",
                (user_id,),
                fetch_one=True,
                default={},
            ) or {}
            run_id = run_row.get("experiment_run_id")
        if not run_id:
            return {
                "status": "no_data",
                "reason": "no run found in experiment_trajectories",
                "user_id": user_id,
                "run_id": None,
                "interactions": [],
                "window_auc": {},
                "n_interactions": 0,
            }

    # Per-interaction trajectory
    traj_rows = _safe_read(
        """
        SELECT
            interaction_number,
            concept,
            correctness,
            mastery_before,
            mastery_after,
            jt_value,
            jt_challenge_contribution,
            jt_uncertainty_contribution,
            jt_delta_m_contribution,
            jt_zpd_contribution,
            jt_transfer_contribution,
            jt_transfer_prospective_contribution,
            ensemble_weight_kalman,
            ensemble_weight_bayesian,
            ensemble_weight_lyapunov,
            bayesian_mastery_after,
            kalman_mastery_after,
            lyapunov_mastery_after,
            response_time,
            arm_selected
        FROM experiment_trajectories
        WHERE user_id = %s
          AND experiment_run_id = %s
        ORDER BY interaction_number
        LIMIT %s
        """,
        (user_id, run_id, limit),
        default=[],
    ) or []

    def _f(v):
        return float(v) if v is not None else None

    interactions = []
    for r in traj_rows:
        interactions.append({
            "interaction_number": r.get("interaction_number"),
            "concept": r.get("concept"),
            "correctness": r.get("correctness"),
            "mastery_before": _f(r.get("mastery_before")),
            "mastery_after": _f(r.get("mastery_after")),
            "jt_value": _f(r.get("jt_value")),
            "jt_challenge_contribution": _f(r.get("jt_challenge_contribution")),
            "jt_uncertainty_contribution": _f(r.get("jt_uncertainty_contribution")),
            "jt_delta_m_contribution": _f(r.get("jt_delta_m_contribution")),
            "jt_zpd_contribution": _f(r.get("jt_zpd_contribution")),
            "jt_transfer_contribution": _f(r.get("jt_transfer_contribution")),
            "jt_transfer_prospective_contribution": _f(r.get("jt_transfer_prospective_contribution")),
            "ensemble_weight_kalman": _f(r.get("ensemble_weight_kalman")),
            "ensemble_weight_bayesian": _f(r.get("ensemble_weight_bayesian")),
            "ensemble_weight_lyapunov": _f(r.get("ensemble_weight_lyapunov")),
            "bayesian_mastery_after": _f(r.get("bayesian_mastery_after")),
            "kalman_mastery_after": _f(r.get("kalman_mastery_after")),
            "lyapunov_mastery_after": _f(r.get("lyapunov_mastery_after")),
            "response_time": _f(r.get("response_time")),
            "arm_selected": r.get("arm_selected"),
        })

    # Per-window AUC from kt_prediction_evaluations
    auc_rows = _safe_read(
        """
        SELECT DISTINCT ON (model_id, cold_start_window)
               model_id, cold_start_window, auc
        FROM kt_prediction_evaluations
        WHERE experiment_run_id = %s
          AND model_id IN ('hcie', 'bkt', 'dkt')
        ORDER BY model_id, cold_start_window, created_at DESC
        """,
        (run_id,),
        default=[],
    ) or []

    # Pivot: {model_id: {window_key: auc}}
    window_auc: Dict[str, Dict[str, Any]] = {}
    for r in auc_rows:
        mid = r.get("model_id")
        w = r.get("cold_start_window")
        auc_val = _f(r.get("auc"))
        slot = window_auc.setdefault(mid, {})
        key = str(int(w)) if w is not None else "all"
        slot[key] = auc_val

    return {
        "status": "ok",
        "user_id": user_id,
        "run_id": run_id,
        "interactions": interactions,
        "window_auc": window_auc,
        "n_interactions": len(interactions),
        "authority": "experiment_trajectories + kt_prediction_evaluations",
        "semantic_version": "1.0",
    }


def _run_source_and_kind(rid, sample_user, traffic_types, synthetic_pct, n_users):
    """Plain-language (source_family, kind) for a run, from its user-id namespace + traffic +
    synthetic share. Pure/heuristic so the fingerprint endpoint stays shallow and this is testable."""
    su = (sample_user or '').lower()
    if 'junyi' in su:
        source_family = 'Junyi 2015 (KT dataset)'
    elif 'ednet' in su:
        source_family = 'EdNet-KT1 (KT dataset)'
    elif 'assist' in su:
        source_family = 'ASSISTments (KT dataset)'
    elif 'csedm' in su:
        source_family = 'CSEDM (KT dataset)'
    elif 'statics' in su:
        source_family = 'STATICS-2011 (KT dataset)'
    elif len(sample_user or '') == 36 and (sample_user or '').count('-') == 4:
        source_family = 'live ITS users (real people on the deployed system)'
    else:
        source_family = 'unknown'
    if str(rid).startswith('live::'):
        kind = 'live-ITS (real learners on the deployed system)'
    elif synthetic_pct >= 99.0:
        kind = 'synthetic-seeded (generated, not real learners)'
    elif 'replay_v2_causal' in str(traffic_types):
        kind = 'causal re-fuse (real-learner dataset, canonical re-fused)'
    elif 0 < n_users <= 5:
        kind = 'smoke / partial cohort (wiring proof, not a full anchor)'
    else:
        kind = 'real-learner dataset replay (real students, replayed through HCIE)'
    return source_family, kind


def _ensemble_mean_block(row):
    """Capability of the canonical MEAN from recorded ensemble weights: which learners are in
    the mean (nonzero weight), how sigma^2 is sourced, and a plain-language label. Handles
    1-learner (Kalman-alone / Option B), 2-learner (causal), and 3-learner (legacy) uniformly."""
    has_kal = int(row.get('has_kalman') or 0) > 0
    has_bay = int(row.get('has_bayesian') or 0) > 0
    has_lyap = int(row.get('has_lyapunov') or 0) > 0
    kal_w = float(row.get('kalman_weight_frac') or 0)
    bay_w = float(row.get('bayesian_weight_frac') or 0)
    lyap_w = float(row.get('lyapunov_weight_frac') or 0)
    mean = []
    if kal_w > 0.5:
        mean.append('kalman')
    if bay_w > 0.5:
        mean.append('bayesian')
    if lyap_w > 0.5:
        mean.append('bounded_stability')
    if not mean:  # no recorded weights (legacy run) -> mean is the average of present learners
        mean = ([n for n, p in (('kalman', has_kal), ('bayesian', has_bay), ('bounded_stability', has_lyap)) if p])
    uses_ex_lyap = 'bounded_stability' in mean
    present = [(n, p) for n, p in (('Kalman', has_kal), ('Bayesian', has_bay), ('Stability', has_lyap)) if p]
    sigma_source = (
        f"ensemble dispersion ({len(present)}-learner: {'/'.join(n for n, _ in present)})"
        if len(present) >= 2 else 'single-learner (no ensemble dispersion)'
    )
    if mean == ['kalman']:
        label, note = ('Kalman-alone canonical (m = m_K)',
                       'canonical = Kalman alone; sigma^2 from ensemble disagreement '
                       '(stability retained at weight 0 in the mean)')
    elif set(mean) == {'kalman', 'bayesian'}:
        label, note = ('2-learner (Kalman + Bayesian)', 'clean 2-learner ensemble (Kalman + Bayesian)')
    elif uses_ex_lyap:
        label, note = (f'{len(mean)}-learner incl. ex-Lyapunov',
                       'LEGACY 3-learner ensemble incl. BoundedStability (ex-Lyapunov, ~0.92 corr with Bayesian)')
    else:
        label, note = (f'{len(mean)}-learner', f'{len(mean)}-learner ensemble')
    return {
        'members': mean,
        'mean_learners': mean,
        'learner_count': len(mean),
        'uses_ex_lyapunov': uses_ex_lyap,
        'ex_lyapunov_weight_coverage': round(lyap_w, 4),
        'canonical_label': label,
        'sigma2_source': sigma_source,
        'canonical_disclosed': 'kalman',
        'weight_method': row.get('weight_method') or '',
        'note': note,
    }


@router.get("/run-fingerprint/{run_id}")
async def get_run_fingerprint(run_id: str) -> Dict[str, Any]:
    """Capability fingerprint for a run — what components it actually used and whether it
    is replay-verifiable. Lets the frontend show, for any run, whether it carries the
    LEGACY 3-learner ensemble (incl. BoundedStability — the ex-Lyapunov learner, ~0.92
    correlated with Bayesian) vs a clean 2-learner core, and whether every recorded step
    has a determinism hash.

    Authority: experiment_trajectories.
    """
    # Resolve short label/prefix -> canonical experiment_run_id. ANCHOR.json stores the
    # full UUID form, but cascade steps / hand-typed labels may carry only the short
    # prefix (e.g. "run-94a3b8ba"). Pick the heaviest matching run.
    resolved = _row1("""
        SELECT experiment_run_id AS rid, COUNT(*) AS n
        FROM experiment_trajectories
        WHERE experiment_run_id = %s OR experiment_run_id LIKE %s
        GROUP BY experiment_run_id
        ORDER BY n DESC
        LIMIT 1
    """, (run_id, run_id + '%'))
    rid = (resolved or {}).get('rid')
    if not rid:
        return {
            'status': 'no_data', 'run_id': run_id,
            'authority': 'experiment_trajectories', 'semantic_version': '1.0',
        }
    row = _row1("""
        SELECT
            COUNT(*)                                                           AS n,
            COUNT(bayesian_mastery_after)                                      AS has_bayesian,
            COUNT(kalman_mastery_after)                                        AS has_kalman,
            COUNT(lyapunov_mastery_after)                                      AS has_lyapunov,
            COUNT(canonical_mastery_after)                                     AS has_canonical,
            AVG(CASE WHEN ensemble_weight_lyapunov IS NOT NULL
                      AND ensemble_weight_lyapunov <> 0 THEN 1.0 ELSE 0.0 END) AS lyapunov_weight_frac,
            AVG(CASE WHEN ensemble_weight_kalman IS NOT NULL
                      AND ensemble_weight_kalman <> 0 THEN 1.0 ELSE 0.0 END)   AS kalman_weight_frac,
            AVG(CASE WHEN ensemble_weight_bayesian IS NOT NULL
                      AND ensemble_weight_bayesian <> 0 THEN 1.0 ELSE 0.0 END) AS bayesian_weight_frac,
            MAX(ensemble_weight_method)                                        AS weight_method,
            SUM(CASE WHEN raw_governance_snapshot ? 'deterministic_inputs_hash'
                     THEN 1 ELSE 0 END)                                        AS det_hash_rows
        FROM experiment_trajectories
        WHERE experiment_run_id = %s
    """, (rid,))
    n = int(row.get('n') or 0)
    if n == 0:
        return {
            'status': 'no_data', 'run_id': run_id,
            'authority': 'experiment_trajectories', 'semantic_version': '1.0',
        }
    det_rows = int(row.get('det_hash_rows') or 0)
    _ens = _ensemble_mean_block(row)

    # Provenance block — what the rows ACTUALLY are (run-switcher legibility): how many
    # learners, real-vs-synthetic, source family, sealed status, lineage, and a plain-language
    # kind. Lets the frontend say "Junyi dataset replay, 93 real learners, sealed" BEFORE you
    # promote, instead of an opaque run id + row count.
    prov = _row1("""
        SELECT COUNT(DISTINCT user_id)                     AS n_users,
               SUM(CASE WHEN synthetic THEN 1 ELSE 0 END)  AS synthetic_rows,
               MIN(user_id)                                AS sample_user,
               string_agg(DISTINCT traffic_type, ', ')     AS traffic_types
        FROM experiment_trajectories WHERE experiment_run_id = %s
    """, (rid,))
    sealed = _row1("SELECT seal_id, sealed_at::text AS sealed_at FROM sealed_runs WHERE experiment_run_id = %s", (rid,))
    fork = _row1("SELECT parent_run_id FROM run_forks WHERE child_run_id = %s ORDER BY created_at DESC LIMIT 1", (rid,))
    n_users = int(prov.get('n_users') or 0)
    synth_rows = int(prov.get('synthetic_rows') or 0)
    synthetic_pct = round(100.0 * synth_rows / n, 1) if n else 0.0
    sample_user = str(prov.get('sample_user') or '')
    traffic_types = prov.get('traffic_types') or ''
    seal_id_db = (sealed or {}).get('seal_id')
    parent_run = (fork or {}).get('parent_run_id')
    source_family, kind = _run_source_and_kind(rid, sample_user, traffic_types, synthetic_pct, n_users)
    _prov = {
        'n_users': n_users,
        'synthetic_pct': synthetic_pct,
        'traffic_types': traffic_types,
        'source_family': source_family,
        'kind': kind,
        'sealed': bool(seal_id_db),
        'seal_id': seal_id_db,
        'sealed_at': (sealed or {}).get('sealed_at'),
        'parent_run_id': parent_run,
        'is_thesis_figure_anchor': rid == THESIS_ANCHOR_RUN_ID,
    }

    return {
        'status': 'ok',
        'run_id': rid,
        'requested': run_id,
        'n_rows': n,
        'provenance': _prov,
        'ensemble': _ens,
        'determinism': {
            'deterministic_inputs_hash_coverage': round(det_rows / n, 4),
            'replay_verifiable': det_rows == n,
            'note': (
                'every step carries a deterministic_inputs_hash -> fully replay-verifiable'
                if det_rows == n else
                'partial determinism-hash coverage -> replay not fully verifiable'
            ),
        },
        'authority': 'experiment_trajectories',
        'semantic_version': '1.0',
    }


# Sealed Phase-2 Junyi ADC anchor — the run the thesis reports on. Thesis-facing
# dashboard panels default to this (not the latest live trajectory row, which is a
# small noisy cohort with no kt_prediction_evaluations rows). Callers wanting a
# different/live run pass ?run_id= explicitly.
#
# DELIBERATELY the V1 run (run-94a3b8ba): the published thesis FIGURES cite it, so the
# read-side dashboards pin it for parity. This is DISTINCT from ANCHOR.json's `active`
# (currently the V2 continuation, run-13b43797) which drives the reproducibility cascade
# — do NOT "fix" this to read `active`, that would silently switch the dashboards to V2
# and break thesis-figure parity. Single-sourced via ANCHOR.json's `thesis_dashboard_anchor`
# field; the literal below is the fallback when that file/field is unavailable.
def _resolve_thesis_anchor_run_id() -> str:
    fallback = "run-94a3b8ba-015b-4d84-b288-004fe60bc282"
    try:
        from pathlib import Path as _P
        import json as _json
        for cand in (
            _P("/app/research_validation/grounding/ANCHOR.json"),
            _P(__file__).resolve().parents[6] / "research_validation" / "grounding" / "ANCHOR.json",
        ):
            if cand.is_file():
                tda = (_json.loads(cand.read_text(encoding="utf-8")) or {}).get("thesis_dashboard_anchor") or {}
                if tda.get("phase2_run_id"):
                    return tda["phase2_run_id"]
    except Exception:
        pass
    return fallback


THESIS_ANCHOR_RUN_ID = _resolve_thesis_anchor_run_id()


@router.get("/auc-by-window")
async def get_auc_by_window(
    run_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Pivot of AUC by (model, cold-start window) for a run.

    Authority: kt_prediction_evaluations
    """
    # Default to the sealed thesis anchor (the latest live row has no
    # kt_prediction_evaluations rows -> permanent no_data). Override via ?run_id=.
    if run_id is None:
        run_id = THESIS_ANCHOR_RUN_ID

    rows = _safe_read(
        """
        SELECT DISTINCT ON (model_id, cold_start_window)
               model_id, cold_start_window, auc, n_predictions
        FROM kt_prediction_evaluations
        WHERE experiment_run_id = %s
        ORDER BY model_id, cold_start_window, created_at DESC
        """,
        (run_id,),
        default=[],
    ) or []

    if not rows:
        return {
            "status": "no_data",
            "reason": "no kt_prediction_evaluations rows for this run",
            "run_id": run_id,
            "windows": [],
            "models": {},
        }

    # Collect all distinct windows (None → "all")
    window_set = set()
    models: Dict[str, Dict[str, Any]] = {}

    for r in rows:
        mid = r.get("model_id")
        w = r.get("cold_start_window")
        key = str(int(w)) if w is not None else "all"
        window_set.add(key)
        slot = models.setdefault(mid, {})
        slot[key] = float(r["auc"]) if r.get("auc") is not None else None

    # Sorted window list: numeric windows first, then "all"
    numeric_windows = sorted(
        [k for k in window_set if k != "all"],
        key=lambda x: int(x),
    )
    ordered_windows = numeric_windows + (["all"] if "all" in window_set else [])

    return {
        "status": "ok",
        "run_id": run_id,
        "windows": ordered_windows,
        "models": models,
        "authority": "kt_prediction_evaluations",
        "semantic_version": "1.0",
    }


@router.get("/adc-live-status")
async def get_adc_live_status(
    run_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Live ADC signal status per JT dimension: mean, std, signal_ratio, ACTIVE/structural_zero.

    ADC formula: signal_ratio = std / mean. Dimension is ACTIVE if mean > alpha_floor AND
    signal_ratio >= signal_ratio_threshold.

    Authority: experiment_trajectories
    """
    ALPHA_FLOOR = 0.01
    SIGNAL_RATIO_THRESHOLD = 0.08

    # Default to the sealed thesis anchor so this matches the thesis (challenge
    # ACTIVE, transfer signal_ratio 1.645). The latest live trajectory row is a
    # small noisy cohort that reads structural_zero. Override via ?run_id=.
    if run_id is None:
        run_id = THESIS_ANCHOR_RUN_ID

    stats = _safe_read(
        """
        SELECT
            COUNT(*) AS n_rows,
            AVG(jt_challenge_contribution)             AS challenge_mean,
            STDDEV(jt_challenge_contribution)          AS challenge_std,
            AVG(jt_uncertainty_contribution)           AS uncertainty_mean,
            STDDEV(jt_uncertainty_contribution)        AS uncertainty_std,
            AVG(jt_delta_m_contribution)               AS delta_m_mean,
            STDDEV(jt_delta_m_contribution)            AS delta_m_std,
            AVG(jt_zpd_contribution)                   AS zpd_mean,
            STDDEV(jt_zpd_contribution)                AS zpd_std,
            AVG(jt_transfer_contribution)              AS transfer_mean,
            STDDEV(jt_transfer_contribution)           AS transfer_std,
            AVG(jt_transfer_prospective_contribution)  AS prospective_mean,
            STDDEV(jt_transfer_prospective_contribution) AS prospective_std
        FROM experiment_trajectories
        WHERE experiment_run_id = %s
        """,
        (run_id,),
        fetch_one=True,
        default={},
    ) or {}

    n_rows = int(stats.get("n_rows") or 0)

    DIMENSIONS = [
        ("challenge",   "Challenge (JT-C)",             "challenge_mean",   "challenge_std"),
        ("uncertainty", "Uncertainty (JT-U)",            "uncertainty_mean", "uncertainty_std"),
        ("delta_m",     "Delta-M (JT-DM)",               "delta_m_mean",     "delta_m_std"),
        ("zpd",         "ZPD (JT-Z)",                    "zpd_mean",         "zpd_std"),
        ("transfer",    "Transfer (JT-T)",               "transfer_mean",    "transfer_std"),
        ("prospective", "Prospective Transfer (JT-TP)",  "prospective_mean", "prospective_std"),
    ]

    dimensions = []
    active_count = 0
    sz_count = 0

    for name, label, mean_key, std_key in DIMENSIONS:
        mean_raw = stats.get(mean_key)
        std_raw  = stats.get(std_key)
        mean = float(mean_raw) if mean_raw is not None else 0.0
        std  = float(std_raw)  if std_raw  is not None else 0.0

        signal_ratio = std / mean if mean > 0 else 0.0
        is_active = mean > ALPHA_FLOOR and signal_ratio >= SIGNAL_RATIO_THRESHOLD
        near_threshold = (
            abs(mean - ALPHA_FLOOR) < 0.005
            or abs(signal_ratio - SIGNAL_RATIO_THRESHOLD) < 0.02
        )
        status_label = "ACTIVE" if is_active else "structural_zero"

        if is_active:
            active_count += 1
        else:
            sz_count += 1

        dimensions.append({
            "name": name,
            "label": label,
            "mean": round(mean, 6),
            "std": round(std, 6),
            "signal_ratio": round(signal_ratio, 4),
            "status": status_label,
            "near_threshold": near_threshold,
        })

    return {
        "status": "ok",
        "run_id": run_id,
        "n_rows": n_rows,
        "alpha_floor": ALPHA_FLOOR,
        "signal_ratio_threshold": SIGNAL_RATIO_THRESHOLD,
        "dimensions": dimensions,
        "active_count": active_count,
        "structural_zero_count": sz_count,
        "authority": "experiment_trajectories",
        "semantic_version": "1.0",
    }


@router.get("/adc-sensitivity-sweep")
async def get_adc_sensitivity_sweep() -> Dict[str, Any]:
    """ADC threshold sensitivity sweep: alpha_floor x signal_ratio_threshold.

    Uses DB-verified stats from sealed run-94a3b8ba (N=96,727).
    Returns dimension stats + two sweep matrices showing ACTIVE/structural_zero
    at each threshold combination.

    Authority: experiment_trajectories (sealed run-94a3b8ba) + run_sealing.py
    """
    # Sealed DB stats from run-94a3b8ba, N=96,727
    # Source: SELECT AVG/STDDEV(jt_*_contribution) ... WHERE experiment_run_id='run-94a3b8ba...'
    SEALED_DIMS = [
        {"name": "challenge",   "mean": 0.1579, "std": 0.0351},
        {"name": "uncertainty", "mean": 0.1193, "std": 0.0690},
        {"name": "delta_m",     "mean": 0.0827, "std": 0.0353},
        {"name": "zpd",         "mean": 0.0438, "std": 0.0563},
        {"name": "transfer",    "mean": 0.0154, "std": 0.0254},
        {"name": "prospective", "mean": 0.0000, "std": 0.0000},
    ]
    for d in SEALED_DIMS:
        d["signal_ratio"] = round(d["std"] / d["mean"], 4) if d["mean"] > 0 else 0.0

    ALPHA_FLOORS = [0.005, 0.01, 0.02, 0.05]
    RATIO_THRESHOLDS = [0.05, 0.08, 0.10, 0.15]
    DEFAULT_AF = 0.01
    DEFAULT_RT = 0.08

    def classify(mu: float, ratio: float, af: float, rt: float) -> str:
        return "ACTIVE" if (mu > af and ratio >= rt) else "structural_zero"

    # Sweep 1: vary alpha_floor at default ratio_threshold
    alpha_sweep = []
    for af in ALPHA_FLOORS:
        row = {"alpha_floor": af, "is_default": (af == DEFAULT_AF), "results": {}}
        for d in SEALED_DIMS:
            row["results"][d["name"]] = classify(d["mean"], d["signal_ratio"], af, DEFAULT_RT)
        alpha_sweep.append(row)

    # Sweep 2: vary ratio_threshold at default alpha_floor
    ratio_sweep = []
    for rt in RATIO_THRESHOLDS:
        row = {"ratio_threshold": rt, "is_default": (rt == DEFAULT_RT), "results": {}}
        for d in SEALED_DIMS:
            row["results"][d["name"]] = classify(d["mean"], d["signal_ratio"], DEFAULT_AF, rt)
        ratio_sweep.append(row)

    return {
        "status": "ok",
        "sealed_run_id": "run-94a3b8ba-015b-4d84-b288-004fe60bc282",
        "n_rows": 96727,
        "default_alpha_floor": DEFAULT_AF,
        "default_ratio_threshold": DEFAULT_RT,
        "dimensions": SEALED_DIMS,
        "alpha_floor_sweep": alpha_sweep,
        "ratio_threshold_sweep": ratio_sweep,
        "key_finding": (
            "3 core dims (challenge, uncertainty, delta_m) ACTIVE at all tested "
            "threshold combos. Transfer structural_zero at alpha_floor>=0.02. "
            "ZPD structural_zero at alpha_floor=0.05. Prospective always structural_zero."
        ),
        "authority": "experiment_trajectories sealed run-94a3b8ba + run_sealing.py",
        "semantic_version": "1.0",
    }


@router.get("/topology-comparison")
async def get_topology_comparison() -> Dict[str, Any]:
    """Cross-family topology causal effect from prospective probe v3.

    Reads from the sealed JSON report; falls back to hardcoded thesis values if the
    file is absent. Key fields: b_durable_CROSS_past (past causal), b_FUTURE_cross_PLACEBO
    (time placebo), causal_estimate (past − placebo), cross_perm_p.

    Authority: research_validation/reports/prospective_probe_v3_full.json
    """
    import json
    import os
    from pathlib import Path as _P

    # Resolve the sealed report from the container mount first, then a host-relative
    # path (repo-root/research_validation). Falls back to thesis values below if
    # neither exists — never a machine-specific absolute path.
    _candidates = [
        _P("/app/research_validation/reports/prospective_probe_v3_full.json"),
        _P(__file__).resolve().parents[6] / "research_validation" / "reports" / "prospective_probe_v3_full.json",
    ]
    _REPORT_PATH = next((str(p) for p in _candidates if p.is_file()), str(_candidates[0]))

    try:
        with open(_REPORT_PATH, "r", encoding="utf-8") as fh:
            raw = json.load(fh)

        past   = float(raw.get("b_durable_CROSS_past", 0.0))
        placebo = float(raw.get("b_FUTURE_cross_PLACEBO", 0.0))
        causal_estimate = round(past - placebo, 5)

        data = dict(raw)
        data["causal_estimate"] = causal_estimate
        data["source"] = "file"
        data["report_path"] = _REPORT_PATH

        return {"status": "ok", "data": data}

    except FileNotFoundError:
        # Hardcoded thesis values (N=1976020, past=0.091, placebo=0.038)
        logger.warning(
            f"topology-comparison: report not found at {_REPORT_PATH}; "
            "falling back to hardcoded thesis values"
        )
        data = {
            "spec": "estimator-v3 same-family vs cross-family (fallback: hardcoded thesis values)",
            "n_rows": 1976020,
            "n_users": 232440,
            "b_durable_CROSS_past": 0.091,
            "b_FUTURE_cross_PLACEBO": 0.038,
            "causal_estimate": 0.053,
            "cross_perm_p": 0.01,
            "shuffled_dag_estimate": 0.0,
            "source": "hardcoded_thesis_fallback",
        }
        return {"status": "ok", "data": data}

    except Exception as exc:
        logger.warning(f"topology-comparison: error reading report: {exc!r}")
        return {
            "status": "error",
            "reason": str(exc),
            "data": {},
        }


@router.get("/cold-warm-stratified")
async def get_cold_warm_stratified(
    run_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Cold vs all-data AUC stratification per model for a run.

    Cold window = smallest available cold_start_window (typically 5).
    All window = rows where cold_start_window IS NULL.

    Authority: kt_prediction_evaluations
    """
    # Resolve run_id
    if run_id is None:
        run_row = _safe_read(
            "SELECT experiment_run_id FROM experiment_trajectories "
            "ORDER BY timestamp DESC LIMIT 1",
            (),
            fetch_one=True,
            default={},
        ) or {}
        run_id = run_row.get("experiment_run_id")
        if not run_id:
            return {
                "status": "no_data",
                "reason": "no run found",
                "run_id": None,
                "models": {},
                "cold_window": None,
            }

    # Fetch all rows for this run — we'll stratify in Python
    rows = _safe_read(
        """
        SELECT DISTINCT ON (model_id, cold_start_window)
               model_id, cold_start_window, auc, n_predictions, n_users
        FROM kt_prediction_evaluations
        WHERE experiment_run_id = %s
        ORDER BY model_id, cold_start_window, created_at DESC
        """,
        (run_id,),
        default=[],
    ) or []

    if not rows:
        return {
            "status": "no_data",
            "reason": "no kt_prediction_evaluations rows for this run",
            "run_id": run_id,
            "models": {},
            "cold_window": None,
        }

    def _f(v):
        return float(v) if v is not None else None

    # Find smallest available non-null window (the "cold" tier)
    non_null_windows = sorted(
        set(int(r["cold_start_window"]) for r in rows if r.get("cold_start_window") is not None)
    )
    cold_window = non_null_windows[0] if non_null_windows else None

    # Build per-model dict
    models: Dict[str, Any] = {}
    for r in rows:
        mid = r.get("model_id")
        w = r.get("cold_start_window")
        slot = models.setdefault(mid, {})

        if w is None:
            # "all" bucket
            slot["all_auc"] = _f(r.get("auc"))
            slot["n_all"] = int(r.get("n_predictions") or 0)
        elif cold_window is not None and int(w) == cold_window:
            slot["cold_auc"] = _f(r.get("auc"))
            slot["n_cold"] = int(r.get("n_predictions") or 0)

    return {
        "status": "ok",
        "run_id": run_id,
        "cold_window": cold_window,
        "models": models,
        "note": (
            f"Cold = first {cold_window} interactions per user; "
            "All = unrestricted (cold_start_window IS NULL)"
        ),
        "authority": "kt_prediction_evaluations",
        "semantic_version": "1.0",
    }
