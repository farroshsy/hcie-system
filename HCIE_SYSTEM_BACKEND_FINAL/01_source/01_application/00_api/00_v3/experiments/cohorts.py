"""Slice 4a cohort lifecycle endpoints."""

from __future__ import annotations

import asyncio
import csv
import io
import json
import math
import os
import random as _rng_module
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.api.dependencies.rbac import require_researcher_or_admin
from app.services.auth.jwt_service import JWTService
from storage.postgres_store.interaction_store import PostgresInteractionStore


router = APIRouter(prefix="/experiments/cohorts", tags=["v3-experiment-cohorts"])

_RUN_LOCK = threading.Semaphore(int(os.getenv("MAX_CONCURRENT_COHORT_RUNS", "1")))
DEFAULT_COHORT_CONCEPTS = ["k2_algorithms"]

# Policies whose names map 1:1 to ``ItsRuntimeService.SUPPORTED_POLICIES``.
# Any other value (e.g. legacy ``"hcie"``) is treated as the canonical default
# selector and ``policy`` is omitted from the recommend payload so the
# runtime keeps current behaviour.
_CANONICAL_POLICIES = {
    "hcie",
    "bandit",
    "thompson",
    "ucb",
    "epsilon_greedy",
    "mastery_greedy",
    "zpd_aligned",
    "uncertainty_reduction",
    "random",
    "static",
}


def _post_with_backoff(
    url: str,
    *,
    json_payload: Dict[str, Any],
    headers: Dict[str, str],
    timeout: float = 10.0,
    attempts: int = 6,
) -> requests.Response:
    """POST with bounded 429 backoff for synthetic cohort orchestration.

    The public learner API should keep its rate limiter. Cohort research runs
    are bulk synthetic clients, so they retry politely instead of globally
    bypassing operational protection.
    """
    last_response: Optional[requests.Response] = None
    for attempt in range(attempts):
        response = requests.post(url, json=json_payload, headers=headers, timeout=timeout)
        last_response = response
        if response.status_code != 429:
            return response
        retry_after = response.headers.get("Retry-After")
        try:
            sleep_s = float(retry_after) if retry_after else 0.0
        except ValueError:
            sleep_s = 0.0
        if sleep_s <= 0:
            sleep_s = min(8.0, 1.0 + attempt * 1.5)
        time.sleep(sleep_s)
    assert last_response is not None
    return last_response


class CohortSpecRequest(BaseModel):
    name: str
    archetypes: List[str] = Field(default_factory=lambda: ["novice"])
    policies: List[str] = Field(default_factory=lambda: ["hcie"])
    ablations: List[str] = Field(default_factory=list)
    seeds: List[int] = Field(default_factory=lambda: [42])
    concepts: List[str] = Field(default_factory=lambda: DEFAULT_COHORT_CONCEPTS.copy(), min_length=1)
    learners_per_cell: int = Field(default=1, ge=1, le=100)
    interactions_per_learner: int = Field(default=3, ge=1, le=1000)
    step_throttle_seconds: float = Field(default=0.0, ge=0.0, le=10.0)
    free_concept_selection: bool = Field(
        default=False,
        description=(
            "When True the concept_filter is omitted from each recommend call so "
            "the policy's bandit selects both concept and task freely from `concepts`. "
            "This allows HCIE to demonstrate ZPD-driven concept traversal vs random."
        ),
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LaunchRequest(BaseModel):
    reason: str = "cohort launch"


def _store() -> PostgresInteractionStore:
    return PostgresInteractionStore()


def _manifest_fingerprint() -> Optional[str]:
    try:
        from core.learning.unified_brain import get_latest_capability_manifest

        manifest = get_latest_capability_manifest()
        return manifest.get("fingerprint") if manifest else None
    except Exception:
        return None


def _ensure_tables(store: PostgresInteractionStore) -> None:
    store.execute_write(
        """
        CREATE TABLE IF NOT EXISTS cohort_specs (
            cohort_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            spec JSONB NOT NULL,
            created_by TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        (),
    )
    store.execute_write(
        """
        CREATE TABLE IF NOT EXISTS cohort_runs (
            run_id TEXT PRIMARY KEY,
            cohort_id TEXT NOT NULL REFERENCES cohort_specs(cohort_id),
            status TEXT NOT NULL,
            reason TEXT,
            capability_manifest_fingerprint TEXT,
            seed_set JSONB NOT NULL DEFAULT '[]'::jsonb,
            synthetic_user_prefix TEXT NOT NULL,
            progress JSONB NOT NULL DEFAULT '{}'::jsonb,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        (),
    )
    store.execute_write(
        """
        CREATE TABLE IF NOT EXISTS cohort_run_progress (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id TEXT NOT NULL REFERENCES cohort_runs(run_id),
            synthetic_user_id TEXT NOT NULL,
            step INTEGER NOT NULL,
            concept_id TEXT,
            task_id TEXT,
            status TEXT NOT NULL,
            event_id TEXT,
            detail JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        (),
    )
    store.execute_write(
        """
        ALTER TABLE learner_projections
        ADD COLUMN IF NOT EXISTS synthetic BOOLEAN NOT NULL DEFAULT FALSE
        """,
        (),
    )
    store.execute_write(
        """
        CREATE TABLE IF NOT EXISTS experiment_trajectories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            experiment_run_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            concept TEXT NOT NULL,
            interaction_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            interaction_number INTEGER NOT NULL,
            mastery_before FLOAT,
            uncertainty_before FLOAT,
            confidence_before FLOAT,
            correctness BOOLEAN,
            response_time FLOAT,
            difficulty FLOAT,
            policy TEXT,
            arm_selected TEXT,
            mastery_after FLOAT,
            uncertainty_after FLOAT,
            confidence_after FLOAT,
            lyapunov_mastery_after FLOAT,
            bayesian_alpha_after FLOAT,
            bayesian_beta_after FLOAT,
            kalman_mastery_after FLOAT,
            kalman_covariance_after FLOAT,
            jt_value FLOAT,
            transfer_amount FLOAT,
            zpd_target FLOAT,
            zpd_alignment_error FLOAT,
            zpd_score FLOAT,
            ensemble_weights JSONB,
            capability_manifest_fingerprint TEXT,
            synthetic BOOLEAN NOT NULL DEFAULT FALSE,
            processing_time FLOAT,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        (),
    )
    store.execute_write(
        """
        ALTER TABLE experiment_trajectories
        ADD COLUMN IF NOT EXISTS mastery_before FLOAT,
        ADD COLUMN IF NOT EXISTS uncertainty_before FLOAT,
        ADD COLUMN IF NOT EXISTS confidence_before FLOAT,
        ADD COLUMN IF NOT EXISTS correctness BOOLEAN,
        ADD COLUMN IF NOT EXISTS response_time FLOAT,
        ADD COLUMN IF NOT EXISTS difficulty FLOAT,
        ADD COLUMN IF NOT EXISTS policy TEXT,
        ADD COLUMN IF NOT EXISTS arm_selected TEXT,
        ADD COLUMN IF NOT EXISTS mastery_after FLOAT,
        ADD COLUMN IF NOT EXISTS uncertainty_after FLOAT,
        ADD COLUMN IF NOT EXISTS confidence_after FLOAT,
        ADD COLUMN IF NOT EXISTS lyapunov_mastery_after FLOAT,
        ADD COLUMN IF NOT EXISTS bayesian_alpha_after FLOAT,
        ADD COLUMN IF NOT EXISTS bayesian_beta_after FLOAT,
        ADD COLUMN IF NOT EXISTS kalman_mastery_after FLOAT,
        ADD COLUMN IF NOT EXISTS kalman_covariance_after FLOAT,
        ADD COLUMN IF NOT EXISTS jt_value FLOAT,
        ADD COLUMN IF NOT EXISTS transfer_amount FLOAT,
        ADD COLUMN IF NOT EXISTS zpd_target FLOAT,
        ADD COLUMN IF NOT EXISTS zpd_alignment_error FLOAT,
        ADD COLUMN IF NOT EXISTS zpd_score FLOAT,
        ADD COLUMN IF NOT EXISTS ensemble_weights JSONB,
        ADD COLUMN IF NOT EXISTS capability_manifest_fingerprint TEXT,
        ADD COLUMN IF NOT EXISTS synthetic BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS processing_time FLOAT
        """,
        (),
    )
    # 🔥 Tier-2 mathematical identifiability: explicit normalized columns for
    # the 6D JT decomposition + attribution + weights + governance metrics +
    # selector evidence. The migration 018_normalized_trajectory_signals
    # ships the same DDL via alembic for fresh installs; the idempotent
    # ALTER here keeps long-lived dev databases in sync without forcing a
    # migration cycle.
    store.execute_write(
        """
        ALTER TABLE experiment_trajectories
        ADD COLUMN IF NOT EXISTS jt_delta_m_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_transfer_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_transfer_prospective_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_challenge_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_uncertainty_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_zpd_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_unclamped FLOAT,
        ADD COLUMN IF NOT EXISTS jt_clamped FLOAT,
        ADD COLUMN IF NOT EXISTS jt_attribution JSONB,
        ADD COLUMN IF NOT EXISTS weights_snapshot JSONB,
        ADD COLUMN IF NOT EXISTS governance_volatility FLOAT,
        ADD COLUMN IF NOT EXISTS governance_exploration_pressure FLOAT,
        ADD COLUMN IF NOT EXISTS governance_stability_index FLOAT,
        ADD COLUMN IF NOT EXISTS policy_multiplier FLOAT,
        ADD COLUMN IF NOT EXISTS effective_learning_rate FLOAT,
        ADD COLUMN IF NOT EXISTS adaptive_rate FLOAT,
        ADD COLUMN IF NOT EXISTS mastery_delta FLOAT,
        ADD COLUMN IF NOT EXISTS policy_selector TEXT,
        ADD COLUMN IF NOT EXISTS policy_score FLOAT,
        ADD COLUMN IF NOT EXISTS candidates_count INTEGER,
        ADD COLUMN IF NOT EXISTS selection_metrics JSONB,
        ADD COLUMN IF NOT EXISTS candidate_arm_scores JSONB,
        ADD COLUMN IF NOT EXISTS attribution_scores JSONB,
        ADD COLUMN IF NOT EXISTS raw_governance_snapshot JSONB,
        ADD COLUMN IF NOT EXISTS jt_baseline_difficulty_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_challenge_event_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_population_prior_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_t_realized_v2_contribution FLOAT,
        ADD COLUMN IF NOT EXISTS jt_v2_active BOOLEAN,
        ADD COLUMN IF NOT EXISTS jt_v2_state_snapshot JSONB,
        ADD COLUMN IF NOT EXISTS jt_v2_challenge_event_fired BOOLEAN,
        ADD COLUMN IF NOT EXISTS jt_v2_challenge_event_reason TEXT
        """,
        (),
    )
    # 🔥 Tier-2 ensemble-semantics evidence (migration 019). Persists the
    # per-learner ensemble layer SEPARATELY from the JT 6D governance
    # layer above, so the math audit can analyse them as distinct
    # semantic families.
    store.execute_write(
        """
        ALTER TABLE experiment_trajectories
        ADD COLUMN IF NOT EXISTS ensemble_mastery_estimate FLOAT,
        ADD COLUMN IF NOT EXISTS canonical_mastery_after FLOAT,
        ADD COLUMN IF NOT EXISTS ensemble_variance_after FLOAT,
        ADD COLUMN IF NOT EXISTS bayesian_mastery_after FLOAT,
        ADD COLUMN IF NOT EXISTS bayesian_variance_after FLOAT,
        ADD COLUMN IF NOT EXISTS kalman_gain_after FLOAT,
        ADD COLUMN IF NOT EXISTS kalman_R_after FLOAT,
        ADD COLUMN IF NOT EXISTS ensemble_weight_lyapunov FLOAT,
        ADD COLUMN IF NOT EXISTS ensemble_weight_bayesian FLOAT,
        ADD COLUMN IF NOT EXISTS ensemble_weight_kalman FLOAT,
        ADD COLUMN IF NOT EXISTS learner_jt_contribution_lyapunov FLOAT,
        ADD COLUMN IF NOT EXISTS learner_jt_contribution_bayesian FLOAT,
        ADD COLUMN IF NOT EXISTS learner_jt_contribution_kalman FLOAT,
        ADD COLUMN IF NOT EXISTS ensemble_weight_method TEXT,
        ADD COLUMN IF NOT EXISTS ensemble_ema_alpha FLOAT,
        ADD COLUMN IF NOT EXISTS ensemble_softmax_temperature FLOAT,
        ADD COLUMN IF NOT EXISTS mastery_delta_direct FLOAT,
        ADD COLUMN IF NOT EXISTS transfer_amount_total FLOAT,
        ADD COLUMN IF NOT EXISTS transfer_amounts_json JSONB,
        ADD COLUMN IF NOT EXISTS zpd_delta_signal FLOAT
        """,
        (),
    )
    store.execute_write(
        "CREATE INDEX IF NOT EXISTS idx_experiment_trajectories_run ON experiment_trajectories(experiment_run_id)",
        (),
    )
    store.execute_write(
        "CREATE INDEX IF NOT EXISTS idx_experiment_trajectories_user ON experiment_trajectories(user_id)",
        (),
    )


def _actor(user: Dict[str, Any]) -> str:
    return str(user.get("email") or user.get("id") or user.get("user_id") or "researcher")


def _validate_task_backed_concepts(store: PostgresInteractionStore, concepts: List[str]) -> None:
    # Allow both the original k12 CT catalog and the external-KT
    # adapters (ASSISTments / EdNet / Junyi) introduced in migration 020.
    # The validator stays generic: any concept_id that has at least one
    # row in `tasks` qualifies as task-backed regardless of which
    # adapter seeded it.
    rows = store.execute_read(
        """
        SELECT concept_id, COUNT(*) AS task_count
        FROM tasks
        WHERE concept_type IN ('k12', 'external_kt')
        GROUP BY concept_id
        """,
        (),
    ) or []
    available = {row["concept_id"]: int(row["task_count"]) for row in rows}
    missing = [concept for concept in concepts if concept not in available]
    if missing:
        raise HTTPException(
            status_code=422,
            detail={
                "reason": "cohort_concepts_not_task_backed",
                "missing": missing,
                "available": sorted(available),
            },
        )


def _latest_learning_state(
    store: PostgresInteractionStore,
    user_id: str,
    concept_id: str,
) -> Dict[str, Any]:
    row = store.execute_read(
        """
        SELECT state_data
        FROM learning_state
        WHERE user_id::text = %s AND concept = %s
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (user_id, concept_id),
        fetch_one=True,
    )
    state = (row or {}).get("state_data") or {}
    if isinstance(state, str):
        try:
            return json.loads(state)
        except json.JSONDecodeError:
            return {}
    return state if isinstance(state, dict) else {}


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _update_run(store: PostgresInteractionStore, run_id: str, status: str, progress: Dict[str, Any]) -> None:
    store.execute_write(
        """
        UPDATE cohort_runs
        SET status = %s, progress = %s::jsonb, updated_at = NOW(),
            started_at = COALESCE(started_at, NOW()),
            completed_at = CASE WHEN %s IN ('completed', 'completed_with_errors', 'failed', 'cancelled') THEN NOW() ELSE completed_at END
        WHERE run_id = %s
        """,
        (status, json.dumps(progress, default=str), status, run_id),
    )


def _record_progress(
    store: PostgresInteractionStore,
    *,
    run_id: str,
    synthetic_user_id: str,
    step: int,
    status: str,
    concept_id: Optional[str] = None,
    task_id: Optional[str] = None,
    event_id: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    store.execute_write(
        """
        INSERT INTO cohort_run_progress (
            run_id, synthetic_user_id, step, concept_id, task_id, status, event_id, detail
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (
            run_id,
            synthetic_user_id,
            step,
            concept_id,
            task_id,
            status,
            event_id,
            json.dumps(detail or {}, default=str),
        ),
    )


_GOVERNANCE_SNAPSHOT_KEYS = (
    # Selector / candidate evidence is captured separately in
    # selection_metrics / candidate_arm_scores. Everything else from the
    # attempt payload that does not have an explicit column lands here so
    # the audit pipeline never has to reach into ``cohort_run_progress``.
    "delta_m",
    "transfer_realized",
    "transfer_prospective",
    "challenge",
    "uncertainty",
    "zpd",
    "baseline_difficulty",
    "challenge_event",
    "population_prior",
    "t_realized_v2",
    "jt_v2_state_snapshot",
    "jt_v2_challenge_event_fired",
    "jt_v2_challenge_event_reason",
    "ensemble_variance",
    "zpd_delta_signal",
    "bayesian_gamma",
    "kalman_process_noise",
    "kalman_measurement_noise",
    "deterministic_inputs_hash",
)


def _governance_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Snapshot the residual attempt payload for forward-compat replay."""
    return {key: payload.get(key) for key in _GOVERNANCE_SNAPSHOT_KEYS if key in payload}


def _record_trajectory(
    store: PostgresInteractionStore,
    *,
    run_id: str,
    user_id: str,
    concept_id: str,
    interaction_id: str,
    event_id: str,
    interaction_number: int,
    state_before: Dict[str, Any],
    attempt_response: Dict[str, Any],
    recommendation: Dict[str, Any],
    policy_label: str,
    selected_arm: str,
    correctness: bool,
    response_time: float,
    difficulty: Optional[float],
) -> None:
    """Persist a single experiment trajectory row.

    The writer is intentionally **wide and normalized**: every Tier-2
    signal (6D JT decomposition, attribution share, weight snapshot,
    governance metrics, selector evidence) lands in an explicit
    FLOAT/TEXT/JSONB column so SQL analytics, attribution plots,
    correlation matrices, ablation tooling, and replay diffs can
    consume the table directly. The opaque side-car
    ``raw_governance_snapshot`` only carries forward-compat residue and
    must never be the primary source for an audit.
    """
    payload = attempt_response.get("payload") or {}
    transfer_amounts = payload.get("transfer_amounts") or {}
    selection_metrics = recommendation.get("selection_metrics") or {}
    candidate_arm_scores = selection_metrics.get("candidate_arm_scores") or []
    attribution = payload.get("jt_attribution") or {}
    weights_snapshot = payload.get("weights_snapshot") or {}

    store.execute_write(
        """
        INSERT INTO experiment_trajectories (
            experiment_run_id, user_id, concept, interaction_id, event_id, interaction_number,
            mastery_before, uncertainty_before, confidence_before,
            correctness, response_time, difficulty, policy, arm_selected,
            mastery_after, uncertainty_after, confidence_after,
            lyapunov_mastery_after, bayesian_alpha_after, bayesian_beta_after,
            kalman_mastery_after, kalman_covariance_after,
            jt_value, transfer_amount, zpd_target, zpd_alignment_error, zpd_score,
            ensemble_weights, capability_manifest_fingerprint, synthetic, processing_time,
            jt_delta_m_contribution, jt_transfer_contribution,
            jt_transfer_prospective_contribution, jt_challenge_contribution,
            jt_uncertainty_contribution, jt_zpd_contribution,
            jt_unclamped, jt_clamped,
            jt_attribution, weights_snapshot,
            governance_volatility, governance_exploration_pressure, governance_stability_index,
            policy_multiplier, effective_learning_rate, adaptive_rate, mastery_delta,
            policy_selector, policy_score, candidates_count,
            selection_metrics, candidate_arm_scores, attribution_scores,
            raw_governance_snapshot,
            jt_baseline_difficulty_contribution, jt_challenge_event_contribution,
            jt_population_prior_contribution, jt_t_realized_v2_contribution,
            jt_v2_active, jt_v2_state_snapshot,
            jt_v2_challenge_event_fired, jt_v2_challenge_event_reason,
            ensemble_mastery_estimate, canonical_mastery_after, ensemble_variance_after,
            bayesian_mastery_after, bayesian_variance_after,
            kalman_gain_after, kalman_R_after,
            ensemble_weight_lyapunov, ensemble_weight_bayesian, ensemble_weight_kalman,
            learner_jt_contribution_lyapunov, learner_jt_contribution_bayesian, learner_jt_contribution_kalman,
            ensemble_weight_method, ensemble_ema_alpha, ensemble_softmax_temperature,
            mastery_delta_direct, transfer_amount_total, transfer_amounts_json,
            zpd_delta_signal
        )
        SELECT
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s, %s, %s, %s,
            %s::jsonb, %s, %s, %s,
            %s, %s,
            %s, %s,
            %s, %s,
            %s, %s,
            %s::jsonb, %s::jsonb,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s::jsonb, %s::jsonb, %s::jsonb,
            %s::jsonb,
            %s, %s,
            %s, %s,
            %s, %s::jsonb,
            %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s::jsonb,
            %s
        WHERE NOT EXISTS (
            SELECT 1 FROM experiment_trajectories
            WHERE experiment_run_id = %s AND user_id = %s AND interaction_id = %s
        )
        """,
        (
            run_id,
            user_id,
            concept_id,
            interaction_id,
            event_id,
            interaction_number,
            _safe_float(state_before.get("mastery")),
            _safe_float(state_before.get("uncertainty")),
            _safe_float(state_before.get("confidence")),
            correctness,
            response_time,
            difficulty,
            policy_label,
            selected_arm,
            _safe_float(payload.get("mastery") or attempt_response.get("mastery")),
            _safe_float(payload.get("uncertainty")),
            _safe_float(payload.get("confidence")),
            _safe_float(payload.get("lyapunov_mastery")),
            _safe_float(payload.get("bayesian_alpha")),
            _safe_float(payload.get("bayesian_beta")),
            _safe_float(payload.get("kalman_mastery")),
            _safe_float(payload.get("kalman_covariance")),
            _safe_float(payload.get("J_value")),
            _safe_float(transfer_amounts.get("total_transfer") or payload.get("transfer_realized")),
            _safe_float(payload.get("zpd_target")),
            _safe_float(payload.get("zpd_alignment_error")),
            _safe_float(payload.get("zpd_score")),
            json.dumps(payload.get("ensemble_weights") or {}),
            payload.get("capability_manifest_fingerprint"),
            str(user_id).startswith("synthetic:"),
            _safe_float(payload.get("processing_time")),
            # 6D JT decomposition + clamping
            _safe_float(payload.get("jt_delta_m_contribution")),
            _safe_float(payload.get("jt_transfer_contribution")),
            _safe_float(payload.get("jt_transfer_prospective_contribution")),
            _safe_float(payload.get("jt_challenge_contribution")),
            _safe_float(payload.get("jt_uncertainty_contribution")),
            _safe_float(payload.get("jt_zpd_contribution")),
            _safe_float(payload.get("jt_unclamped")),
            _safe_float(payload.get("jt_clamped")),
            json.dumps(attribution if isinstance(attribution, dict) else {}),
            json.dumps(weights_snapshot if isinstance(weights_snapshot, dict) else {}),
            # F-031 governance metrics
            _safe_float(payload.get("jt_volatility")),
            _safe_float(payload.get("exploration_pressure")),
            _safe_float(payload.get("stability_index")),
            # Learning dynamics
            _safe_float(payload.get("policy_multiplier")),
            _safe_float(payload.get("effective_learning_rate")),
            _safe_float(payload.get("adaptive_rate")),
            _safe_float(payload.get("mastery_delta")),
            # Selector evidence (scalar + JSONB)
            selection_metrics.get("policy_selector"),
            _safe_float(selection_metrics.get("policy_score")),
            (
                int(selection_metrics["candidates_count"])
                if selection_metrics.get("candidates_count") is not None
                else None
            ),
            json.dumps(selection_metrics, default=str),
            json.dumps(candidate_arm_scores, default=str),
            json.dumps(attribution if isinstance(attribution, dict) else {}),
            # Side-car: residual payload for forward-compat archaeology only.
            json.dumps(_governance_snapshot(payload), default=str),
            # Tier 2.5 V2 signals (nullable unless HCIE_REDESIGN_V2=1).
            _safe_float(payload.get("jt_baseline_difficulty_contribution")),
            _safe_float(payload.get("jt_challenge_event_contribution")),
            _safe_float(payload.get("jt_population_prior_contribution")),
            _safe_float(payload.get("jt_t_realized_v2_contribution")),
            bool(payload.get("jt_v2_active")) if payload.get("jt_v2_active") is not None else None,
            json.dumps(payload.get("jt_v2_state_snapshot") or {}, default=str),
            bool(payload.get("jt_v2_challenge_event_fired"))
            if payload.get("jt_v2_challenge_event_fired") is not None
            else None,
            payload.get("jt_v2_challenge_event_reason"),
            # Ensemble-semantics layer (migration 019). Distinct family.
            _safe_float(payload.get("ensemble_mastery_estimate")),
            _safe_float(payload.get("canonical_mastery_after")),
            _safe_float(payload.get("ensemble_variance_after")),
            _safe_float(payload.get("bayesian_mastery_after")),
            _safe_float(payload.get("bayesian_variance_after")),
            _safe_float(payload.get("kalman_gain_after")),
            _safe_float(payload.get("kalman_R_after")),
            _safe_float(payload.get("ensemble_weight_lyapunov")),
            _safe_float(payload.get("ensemble_weight_bayesian")),
            _safe_float(payload.get("ensemble_weight_kalman")),
            _safe_float(payload.get("learner_jt_contribution_lyapunov")),
            _safe_float(payload.get("learner_jt_contribution_bayesian")),
            _safe_float(payload.get("learner_jt_contribution_kalman")),
            payload.get("ensemble_weight_method"),
            _safe_float(payload.get("ensemble_ema_alpha")),
            _safe_float(payload.get("ensemble_softmax_temperature")),
            _safe_float(payload.get("mastery_delta_direct")),
            _safe_float(payload.get("transfer_amount_total")),
            json.dumps(transfer_amounts if isinstance(transfer_amounts, dict) else {}),
            _safe_float(payload.get("zpd_delta_signal_value")),
            run_id,
            user_id,
            interaction_id,
        ),
    )


def _token_for_synthetic_user(user_id: str) -> str:
    return JWTService().create_access_token(
        {
            "sub": user_id,
            "email": f"{user_id.replace(':', '_')}@synthetic.hcie.local",
            "role": "student",
        }
    )


def _run_cohort(run_id: str, cohort_id: str) -> None:
    if not _RUN_LOCK.acquire(blocking=False):
        store = _store()
        _update_run(store, run_id, "failed", {"error": "max_concurrent_cohort_runs_reached"})
        return

    store = _store()
    try:
        # Stage 0 backstop (defense-in-depth): never write into a sealed run. The
        # replay endpoint already 409s + hands off a continuation; resume of a
        # sealed run lands here, so fail it loudly rather than mutate the seal.
        from app.api.v3.experiments.run_sealing import _seal_id, is_sealed
        if is_sealed(store, run_id):
            _update_run(store, run_id, "failed", {
                "error": "run_sealed",
                "seal_id": _seal_id(store, run_id),
                "message": "cohort run targets a sealed run_id; start a continuation run instead",
            })
            return
        row = store.execute_read(
            "SELECT spec, synthetic_user_prefix FROM cohort_specs JOIN cohort_runs USING (cohort_id) WHERE run_id = %s",
            (run_id,),
            fetch_one=True,
        )
        if not row:
            raise RuntimeError("cohort_run_not_found")
        spec = row["spec"]
        prefix = row["synthetic_user_prefix"]
        base_url = os.getenv("HCIE_INTERNAL_BASE_URL", "http://127.0.0.1:8000")

        # Resume support: skip (synthetic_user_id, step) pairs that already have
        # a 'completed' cohort_run_progress row. Lets a run that died mid-flight
        # (API crash, container restart) pick up where it left off without
        # re-doing already-recorded interactions.
        resume_rows = store.execute_read(
            "SELECT synthetic_user_id, step FROM cohort_run_progress "
            "WHERE run_id = %s AND status = 'completed'",
            (run_id,),
        ) or []
        completed_keys = {
            (r["synthetic_user_id"], int(r["step"])) for r in resume_rows
        }
        resumed = len(completed_keys) > 0

        # Replay determinism: reset the brain's cold-start population prior to
        # its fixed warm-started baseline at the start of a FRESH synthetic run
        # (not a resume — a resumed run must keep the prior it already grew from
        # the completed portion). Best-effort; never blocks the run.
        if not resumed:
            try:
                from app.infrastructure.di.get_container import get_container
                _brain = get_container().unified_brain()
                if hasattr(_brain, "reset_coldstart_prior"):
                    _brain.reset_coldstart_prior()
            except Exception as _exc:  # pragma: no cover - defensive
                print(f"⚠️ coldstart_prior_reset_skipped run_id={run_id} err={_exc}")

        total = 0
        completed = len(completed_keys)
        errors = 0
        _update_run(
            store,
            run_id,
            "running",
            {"completed": completed, "errors": errors, "resumed": resumed},
        )
        throttle_s = float(
            spec.get(
                "step_throttle_seconds",
                os.getenv("HCIE_COHORT_STEP_THROTTLE_SECONDS", "0"),
            )
            or 0
        )

        for seed in spec.get("seeds", [42]):
            for archetype in spec.get("archetypes", ["novice"]):
                for policy in spec.get("policies", ["hcie"]):
                    for learner_index in range(int(spec.get("learners_per_cell", 1))):
                        synthetic_user_id = (
                            f"{prefix}:{policy}:{archetype}:{seed}:{learner_index}"
                        )
                        token = _token_for_synthetic_user(synthetic_user_id)
                        base_headers = {
                            "Authorization": f"Bearer {token}",
                            "X-HCIE-Deterministic": "true",
                        }
                        concepts = spec.get("concepts", ["loops"])
                        free_concept = bool(spec.get("free_concept_selection", False))
                        for step in range(1, int(spec.get("interactions_per_learner", 1)) + 1):
                            total += 1
                            # Resume: skip step if already recorded as completed.
                            if (synthetic_user_id, step) in completed_keys:
                                continue
                            # In locked-concept mode cycle through spec concepts in order.
                            # In free-concept mode the policy's bandit picks freely.
                            concept = concepts[(step - 1) % len(concepts)]
                            # Per-step deterministic seed: encodes (cell_seed, step)
                            # so RNG-driven baselines like ``random`` produce
                            # within-session diversity while staying replay-deterministic.
                            step_seed = int(seed) * 1000 + int(step)
                            headers = {
                                **base_headers,
                                "X-HCIE-Deterministic-Seed": str(step_seed),
                            }
                            try:
                                recommend_payload: Dict[str, Any] = {
                                    "deterministic": True,
                                    "seed": step_seed,
                                }
                                if not free_concept:
                                    # Constrain task selection to this step's concept.
                                    recommend_payload["concept_filter"] = [concept]
                                else:
                                    # Expose all spec concepts so the policy selects freely.
                                    recommend_payload["concept_filter"] = concepts
                                if policy in _CANONICAL_POLICIES:
                                    recommend_payload["policy"] = policy
                                rec = _post_with_backoff(
                                    f"{base_url}/v3/learner/recommend",
                                    json_payload=recommend_payload,
                                    headers=headers,
                                    timeout=10,
                                )
                                rec.raise_for_status()
                                recommendation = rec.json()
                                task_id = recommendation.get("task_id")
                                concept_id = recommendation.get("concept_id") or concept
                                event_id = f"{run_id}:{synthetic_user_id}:{step}"
                                state_before = _latest_learning_state(store, synthetic_user_id, concept_id)
                                # IRT-based correctness: P(correct) = sigmoid(a*(θ - b + zpd_bias))
                                # where θ = learner mastery, b = task difficulty, a = discrimination.
                                # ZPD bias (+0.1) ensures that a perfectly ZPD-matched task gives
                                # ~60% P(correct) — the Vygotsky sweet spot for learning gain.
                                # Using step_seed makes outcomes deterministic and replay-safe
                                # while letting difficulty and mastery drive the distribution.
                                _mastery = float(state_before.get("mastery") or 0.3)
                                _diff = float(recommendation.get("difficulty") or 0.5)
                                _logit = 3.0 * (_mastery - _diff + 0.1)
                                _p = max(0.05, min(0.95, 1.0 / (1.0 + math.exp(-_logit))))
                                is_correct = _rng_module.Random(step_seed).random() < _p
                                response_time = 5.0
                                attempt = _post_with_backoff(
                                    f"{base_url}/v3/learner/attempt",
                                    json_payload={
                                        "task_id": task_id,
                                        "concept_id": concept_id,
                                        "answer": "synthetic",
                                        "correct": is_correct,
                                        "response_time": response_time,
                                        "event_id": event_id,
                                    },
                                    headers=headers,
                                    timeout=10,
                                )
                                attempt.raise_for_status()
                                attempt_json = attempt.json()
                                _record_trajectory(
                                    store,
                                    run_id=run_id,
                                    user_id=synthetic_user_id,
                                    concept_id=concept_id,
                                    interaction_id=event_id,
                                    event_id=attempt_json.get("event_id") or event_id,
                                    interaction_number=step,
                                    state_before=state_before,
                                    attempt_response=attempt_json,
                                    recommendation=recommendation,
                                    policy_label=policy,
                                    selected_arm=task_id,
                                    correctness=is_correct,
                                    response_time=response_time,
                                    difficulty=_safe_float(recommendation.get("difficulty")),
                                )
                                completed += 1
                                _record_progress(
                                    store,
                                    run_id=run_id,
                                    synthetic_user_id=synthetic_user_id,
                                    step=step,
                                    status="completed",
                                    concept_id=concept_id,
                                    task_id=task_id,
                                    event_id=event_id,
                                    detail={
                                        "policy": policy,
                                        "archetype": archetype,
                                        "seed": seed,
                                        "recommendation": recommendation,
                                        "attempt": attempt_json,
                                    },
                                )
                            except Exception as exc:
                                errors += 1
                                _record_progress(
                                    store,
                                    run_id=run_id,
                                    synthetic_user_id=synthetic_user_id,
                                    step=step,
                                    status="failed",
                                    concept_id=concept,
                                    detail={"error": str(exc), "policy": policy, "seed": seed},
                                )
                            _update_run(
                                store,
                                run_id,
                                "running",
                                {"total": total, "completed": completed, "errors": errors},
                            )
                            if throttle_s > 0:
                                time.sleep(throttle_s)

        final_status = "completed" if errors == 0 else "completed_with_errors"
        _update_run(
            store,
            run_id,
            final_status,
            {"total": total, "completed": completed, "errors": errors},
        )
    except Exception as exc:
        _update_run(store, run_id, "failed", {"error": str(exc)})
    finally:
        _RUN_LOCK.release()


def resume_pending_runs() -> int:
    """Re-spawn cohort runs left in 'queued' or 'running' after an API restart.

    Why: ``_run_cohort`` runs as an in-process background task; if the API
    crashes or is redeployed mid-run, the task dies but the DB still shows the
    run as ``running``. This reaper finds those orphans on startup and re-spawns
    them. Resume logic in ``_run_cohort`` skips already-completed steps via
    ``cohort_run_progress``, so re-spawning is safe and picks up where the
    previous run died.
    """
    try:
        store = _store()
        _ensure_tables(store)
        rows = store.execute_read(
            "SELECT run_id, cohort_id FROM cohort_runs "
            "WHERE status IN ('queued', 'running') "
            "ORDER BY created_at ASC",
        ) or []
        for row in rows:
            t = threading.Thread(
                target=_run_cohort,
                args=(row["run_id"], row["cohort_id"]),
                daemon=True,
                name=f"cohort-resume-{row['run_id'][:8]}",
            )
            t.start()
        return len(rows)
    except Exception:
        return 0


@router.get("")
async def list_cohorts(
    _user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Dict[str, Any]:
    """List cohort specs for the instructor dashboard launcher dropdown."""
    store = _store()
    _ensure_tables(store)
    rows = store.execute_read(
        "SELECT cohort_id, name, created_at, "
        "spec->'policies' as policies, "
        "spec->'archetypes' as archetypes "
        "FROM cohort_specs ORDER BY created_at DESC LIMIT 100",
    ) or []
    return {"status": "ok", "cohorts": rows, "semantic_version": "1.0"}


@router.post("")
async def create_cohort(
    body: CohortSpecRequest,
    user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Dict[str, Any]:
    store = _store()
    _ensure_tables(store)
    _validate_task_backed_concepts(store, body.concepts)
    cohort_id = f"cohort-{uuid.uuid4()}"
    store.execute_write(
        """
        INSERT INTO cohort_specs (cohort_id, name, spec, created_by)
        VALUES (%s, %s, %s::jsonb, %s)
        """,
        (cohort_id, body.name, body.model_dump_json(), _actor(user)),
    )
    return {"status": "created", "cohort_id": cohort_id, "semantic_version": "1.0"}


@router.get("/{cohort_id}")
async def get_cohort(
    cohort_id: str,
    _user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Dict[str, Any]:
    store = _store()
    _ensure_tables(store)
    spec = store.execute_read(
        "SELECT * FROM cohort_specs WHERE cohort_id = %s",
        (cohort_id,),
        fetch_one=True,
    )
    if not spec:
        raise HTTPException(status_code=404, detail="cohort_not_found")
    runs = store.execute_read(
        "SELECT * FROM cohort_runs WHERE cohort_id = %s ORDER BY created_at DESC LIMIT 10",
        (cohort_id,),
    )
    return {"status": "ok", "cohort": spec, "runs": runs or [], "semantic_version": "1.0"}


@router.post("/{cohort_id}/launch")
async def launch_cohort(
    cohort_id: str,
    body: LaunchRequest,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Dict[str, Any]:
    store = _store()
    _ensure_tables(store)
    spec = store.execute_read(
        "SELECT spec FROM cohort_specs WHERE cohort_id = %s",
        (cohort_id,),
        fetch_one=True,
    )
    if not spec:
        raise HTTPException(status_code=404, detail="cohort_not_found")
    run_id = f"run-{uuid.uuid4()}"
    prefix = f"synthetic:{cohort_id}:{run_id}"
    store.execute_write(
        """
        INSERT INTO cohort_runs (
            run_id, cohort_id, status, reason, capability_manifest_fingerprint,
            seed_set, synthetic_user_prefix, progress
        )
        VALUES (%s, %s, 'queued', %s, %s, %s::jsonb, %s, '{}'::jsonb)
        """,
        (
            run_id,
            cohort_id,
            body.reason,
            _manifest_fingerprint(),
            json.dumps(spec["spec"].get("seeds", []), default=str),
            prefix,
        ),
    )
    background_tasks.add_task(_run_cohort, run_id, cohort_id)
    return {
        "status": "queued",
        "cohort_id": cohort_id,
        "run_id": run_id,
        "synthetic_user_prefix": prefix,
        "launched_by": _actor(user),
        "semantic_version": "1.0",
    }


@router.get("/{cohort_id}/runs/{run_id}")
async def get_run(
    cohort_id: str,
    run_id: str,
    _user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Dict[str, Any]:
    store = _store()
    _ensure_tables(store)
    run = store.execute_read(
        "SELECT * FROM cohort_runs WHERE cohort_id = %s AND run_id = %s",
        (cohort_id, run_id),
        fetch_one=True,
    )
    if not run:
        raise HTTPException(status_code=404, detail="run_not_found")
    return {"status": "ok", "run": run, "semantic_version": "1.0"}


@router.get("/{cohort_id}/runs/{run_id}/stats.csv")
async def stats_csv(
    cohort_id: str,
    run_id: str,
    _user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Response:
    store = _store()
    rows = store.execute_read(
        """
        SELECT detail, status
        FROM cohort_run_progress
        WHERE run_id = %s
        ORDER BY created_at ASC
        """,
        (run_id,),
    ) or []
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["policy", "archetype", "seed", "attempts", "completed"])
    writer.writeheader()
    buckets: Dict[tuple, Dict[str, Any]] = {}
    for row in rows:
        detail = row.get("detail") or {}
        key = (detail.get("policy", ""), detail.get("archetype", ""), detail.get("seed", ""))
        bucket = buckets.setdefault(key, {"attempts": 0, "completed": 0})
        bucket["attempts"] += 1
        if row.get("status") == "completed":
            bucket["completed"] += 1
    for (policy, archetype, seed), bucket in buckets.items():
        writer.writerow({"policy": policy, "archetype": archetype, "seed": seed, **bucket})
    return Response(content=output.getvalue(), media_type="text/csv")


@router.get("/{cohort_id}/runs/{run_id}/trajectories.csv")
async def trajectories_csv(
    cohort_id: str,
    run_id: str,
    _user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Response:
    store = _store()
    rows = store.execute_read(
        """
        SELECT *
        FROM experiment_trajectories
        WHERE experiment_run_id = %s OR user_id LIKE %s
        ORDER BY timestamp ASC, interaction_number ASC
        """,
        (run_id, f"synthetic:{cohort_id}:{run_id}%"),
    ) or []
    fields = [
        "timestamp", "experiment_run_id", "interaction_number", "user_id",
        "concept", "policy", "arm_selected", "correctness", "mastery_before",
        "mastery_after", "jt_value", "capability_manifest_fingerprint",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field) for field in fields})
    return Response(content=output.getvalue(), media_type="text/csv")


@router.get("/{cohort_id}/runs/{run_id}/gates")
async def gates(
    cohort_id: str,
    run_id: str,
    _user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Dict[str, Any]:
    store = _store()
    run = store.execute_read("SELECT * FROM cohort_runs WHERE run_id = %s", (run_id,), fetch_one=True)
    progress = store.execute_read(
        "SELECT status, COUNT(*) AS count FROM cohort_run_progress WHERE run_id = %s GROUP BY status",
        (run_id,),
    ) or []
    passed = bool(run and run.get("capability_manifest_fingerprint"))
    return {
        "status": "ok",
        "gates": {
            "runtime_topology": passed,
            "trajectory_integrity": all(row["status"] != "failed" for row in progress),
            "capability_manifest_present": passed,
        },
        "progress": progress,
        "semantic_version": "1.0",
    }


@router.post("/{cohort_id}/runs/{run_id}/replay")
async def replay_run(
    cohort_id: str,
    run_id: str,
    _user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Dict[str, Any]:
    from app.api.v3.experiments.run_sealing import is_sealed, mint_continuation, _seal_id
    from app.api.v3.service.router import _batch_replay

    # Stage 0 (reject + assisted handoff): a sealed run is immutable. Don't write
    # to it — hand the caller a fresh continuation run linked to the sealed parent
    # and let them replay into that explicitly (no silent redirect).
    store = _store()
    if is_sealed(store, run_id):
        continue_with = mint_continuation(store, run_id)
        # Return a structured JSONResponse (not raise HTTPException): the global
        # http_exception_handler str()s a dict detail into a Python-repr string,
        # which would make continue_with/seal_id unparseable. Returned Responses
        # bypass the handlers. Shape mirrors the house error envelope; the machine
        # fields live in error.context so callers can read them as real JSON.
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "run_sealed",
                    "message": (
                        f"Run {run_id} is sealed and cannot accept new writes. "
                        f"Re-issue the replay against {continue_with}."
                    ),
                    "context": {
                        "run_id": run_id,
                        "seal_id": _seal_id(store, run_id),
                        "continue_with": continue_with,
                    },
                },
                "status": 409,
            },
        )

    result = _batch_replay(run_id, num_users=100)
    return {"status": "ok", "run_id": run_id, "result": result, "semantic_version": "1.0"}


@router.post("/{cohort_id}/runs/{run_id}/seal")
async def seal_cohort_run(
    cohort_id: str,
    run_id: str,
    note: Optional[str] = None,
    _user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Dict[str, Any]:
    """Stage 0: freeze a run into an immutable, citable manifest (idempotent).

    After sealing, replay/resume writes to this run are rejected (409); the
    caller is handed a fresh continuation run_id to write to instead (see
    run_sealing), so the sealed manifest can never change. Cite ``seal_id``.
    """
    from app.api.v3.experiments.run_sealing import seal_run

    manifest = seal_run(_store(), run_id, sealed_by="api", note=note)
    return {"status": "ok", "run_id": run_id, "seal": manifest, "semantic_version": "1.0"}


# ---------------------------------------------------------------------------
# External-log source (Contribution C, prediction surface)
# ---------------------------------------------------------------------------
#
# These endpoints let an external orchestrator (e.g. an ASSISTments /
# EdNet / Junyi adapter under research_validation/external_datasets/)
# feed real KT-log attempts through the SAME runtime path the synthetic
# cohort uses: /v3/learner/attempt → ITS submit_attempt → Kafka outbox →
# downstream consumers + audit stack. The orchestrator drives the loop;
# the API owns the run_id lifecycle and the trajectory write.
#
# Design contract:
#   1. ``external_run_create`` allocates a cohort_runs row for the
#      external source. The cohort spec MUST already exist (the
#      orchestrator creates it via the standard POST endpoint).
#   2. ``external_run_attempt`` is the per-attempt hot path. It is
#      semantically equivalent to one iteration of the synthetic loop:
#      issue a synthetic-learner token, POST /v3/learner/attempt with
#      the dataset's task/concept/correct, then call _record_trajectory
#      AND mirror to ``external_log_attempts`` for the dataset-level
#      audit surface.
#   3. ``external_run_finalize`` sets the terminal status.
#
# Concept/task IDs MUST already be seeded in the HCIE catalog tables
# (see research_validation/scripts/seed_external_concepts.py). The
# orchestrator is responsible for that pre-step.


def _ensure_graph_table(store: "PostgresInteractionStore") -> None:
    """Lightweight idempotent check that migration 021 has run."""
    store.execute_write(
        """
        CREATE TABLE IF NOT EXISTS external_concept_graph (
            id                BIGSERIAL PRIMARY KEY,
            experiment_run_id TEXT NOT NULL,
            dataset_id        TEXT NOT NULL,
            source_concept_id TEXT NOT NULL,
            target_concept_id TEXT NOT NULL,
            transfer_weight   DOUBLE PRECISION NOT NULL,
            graph_method      TEXT NOT NULL,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (experiment_run_id, source_concept_id, target_concept_id)
        )
        """,
        (),
    )
    store.execute_write(
        """
        CREATE INDEX IF NOT EXISTS idx_external_concept_graph_run
            ON external_concept_graph (experiment_run_id)
        """,
        (),
    )
    store.execute_write(
        """
        CREATE INDEX IF NOT EXISTS idx_external_concept_graph_source
            ON external_concept_graph (experiment_run_id, source_concept_id)
        """,
        (),
    )


def _ensure_external_tables(store: "PostgresInteractionStore") -> None:
    """Lightweight idempotent check that migration 020 has run."""
    store.execute_write(
        """
        CREATE TABLE IF NOT EXISTS external_dataset_registry (
            dataset_id TEXT PRIMARY KEY,
            family TEXT NOT NULL,
            schema_version TEXT NOT NULL DEFAULT '1.0',
            description TEXT,
            concept_prefix TEXT NOT NULL,
            task_prefix TEXT NOT NULL,
            citation TEXT,
            license TEXT,
            metadata JSONB,
            registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        (),
    )
    store.execute_write(
        """
        CREATE TABLE IF NOT EXISTS external_log_attempts (
            id BIGSERIAL PRIMARY KEY,
            experiment_run_id TEXT NOT NULL,
            dataset_id TEXT NOT NULL,
            source_user_id TEXT NOT NULL,
            source_skill_id TEXT NOT NULL,
            source_problem_id TEXT,
            user_id TEXT NOT NULL,
            concept_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            attempt_index INTEGER NOT NULL,
            correct BOOLEAN NOT NULL,
            response_time DOUBLE PRECISION,
            raw_timestamp TIMESTAMPTZ,
            submitted_event_id TEXT,
            api_status INTEGER,
            metadata JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        (),
    )


class ExternalDatasetRegistration(BaseModel):
    dataset_id: str
    family: str
    description: str = ""
    concept_prefix: str
    task_prefix: str
    citation: str = ""
    license: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("/external_datasets")
async def register_external_dataset(
    body: ExternalDatasetRegistration,
    _user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Dict[str, Any]:
    """Register a KT dataset in the dataset registry (idempotent upsert)."""
    store = _store()
    _ensure_external_tables(store)
    store.execute_write(
        """
        INSERT INTO external_dataset_registry (
            dataset_id, family, schema_version, description,
            concept_prefix, task_prefix, citation, license, metadata
        ) VALUES (%s, %s, '1.0', %s, %s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (dataset_id) DO UPDATE SET
            family = EXCLUDED.family,
            description = EXCLUDED.description,
            concept_prefix = EXCLUDED.concept_prefix,
            task_prefix = EXCLUDED.task_prefix,
            citation = EXCLUDED.citation,
            license = EXCLUDED.license,
            metadata = EXCLUDED.metadata
        """,
        (
            body.dataset_id, body.family, body.description,
            body.concept_prefix, body.task_prefix,
            body.citation, body.license,
            json.dumps(body.metadata),
        ),
    )
    return {"status": "registered", "dataset_id": body.dataset_id}


class ExternalRunRequest(BaseModel):
    dataset_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("/{cohort_id}/external_run")
async def external_run_create(
    cohort_id: str,
    body: ExternalRunRequest,
    user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Dict[str, Any]:
    """Allocate a cohort_runs row for an external-log source.

    Mirrors the lifecycle of ``/launch`` but does **not** spawn the
    synthetic background loop. The caller (research_validation
    orchestrator) drives the per-attempt loop via
    ``/external_attempt``.
    """
    store = _store()
    _ensure_tables(store)
    _ensure_external_tables(store)
    _ensure_graph_table(store)
    spec = store.execute_read(
        "SELECT * FROM cohort_specs WHERE cohort_id = %s",
        (cohort_id,),
        fetch_one=True,
    )
    if not spec:
        raise HTTPException(status_code=404, detail="cohort_not_found")
    registry_row = store.execute_read(
        "SELECT dataset_id FROM external_dataset_registry WHERE dataset_id = %s",
        (body.dataset_id,),
        fetch_one=True,
    )
    if not registry_row:
        raise HTTPException(
            status_code=400,
            detail=f"unregistered_dataset:{body.dataset_id}",
        )
    run_id = f"run-{uuid.uuid4()}"
    prefix = f"external:{body.dataset_id}:{run_id}"
    fingerprint = _manifest_fingerprint()
    store.execute_write(
        """
        INSERT INTO cohort_runs (
            run_id, cohort_id, status, reason, capability_manifest_fingerprint,
            seed_set, synthetic_user_prefix, progress, started_at
        )
        VALUES (%s, %s, 'running', %s, %s, '[]'::jsonb, %s, %s::jsonb, NOW())
        """,
        (
            run_id, cohort_id,
            f"external_log:{body.dataset_id}",
            fingerprint, prefix,
            json.dumps({
                "source": {
                    "kind": "external_log",
                    "dataset_id": body.dataset_id,
                    **body.metadata,
                },
                "total": 0, "completed": 0, "errors": 0,
            }),
        ),
    )
    # Replay determinism: reset the brain's cold-start population prior to its
    # fixed warm-started baseline at the START of this external run, so the run
    # does not inherit prior state accumulated by earlier runs in this
    # long-lived API process. The within-run online accumulation stays
    # deterministic (event-ordered, O(1), no RNG). Best-effort; never blocks
    # run creation. See unified_brain.reset_coldstart_prior.
    try:
        from app.infrastructure.di.get_container import get_container
        _brain = get_container().unified_brain()
        if hasattr(_brain, "reset_coldstart_prior"):
            _brain.reset_coldstart_prior()
    except Exception as _exc:  # pragma: no cover - defensive
        print(f"⚠️ coldstart_prior_reset_skipped run_id={run_id} err={_exc}")
    return {
        "status": "running",
        "run_id": run_id,
        "cohort_id": cohort_id,
        "dataset_id": body.dataset_id,
        "synthetic_user_prefix": prefix,
    }


@router.post("/{cohort_id}/runs/{run_id}/external_load_graph")
async def external_load_graph(
    cohort_id: str,
    run_id: str,
    user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Dict[str, Any]:
    """Phase 2: Load concept-graph edges from ``external_concept_graph`` into
    the live ``TransferLearningEngine.dependencies`` dict.

    Called once by the orchestrator after ``external_run_create`` and after the
    graph has been persisted by ``_build_and_persist_concept_graph()``.  The
    injection makes ``transfer_realized`` activatable for external concept IDs
    that have DAG edges (primarily Junyi 2015).

    Replay-determinism note: this call changes the ``governance_bounded`` tier
    for subsequent attempts on this run.  It does NOT affect ``decision_exact``
    (mastery state is driven by the Bayesian/Kalman/Lyapunov ensemble, which
    does not read transfer weight directly).  See GRAPH_INTEGRATION_REPLAY_SAFETY.md
    §"What Phase 2 will change".
    """
    store = _store()
    rows = store.execute_read(
        "SELECT source_concept_id, target_concept_id, transfer_weight "
        "FROM external_concept_graph WHERE experiment_run_id = %s "
        "ORDER BY source_concept_id",
        (run_id,),
    )
    if not rows:
        return {"status": "ok", "injected": 0, "run_id": run_id,
                "detail": "no_edges_found"}

    edges = [
        (r["source_concept_id"], r["target_concept_id"], float(r["transfer_weight"]))
        for r in rows
    ]

    try:
        from app.infrastructure.di.get_container import get_container
        brain = get_container().unified_brain()
        injected = brain.transfer_engine.inject_external_dependencies(edges)
    except Exception as exc:
        return {"status": "error", "run_id": run_id, "detail": str(exc)}

    return {"status": "ok", "injected": injected, "run_id": run_id}


class ExternalAttemptRequest(BaseModel):
    synthetic_user_id: str
    concept_id: str
    task_id: str
    correct: bool
    response_time: float = 5.0
    attempt_index: int
    dataset_id: str
    source_user_id: Optional[str] = None
    source_skill_id: Optional[str] = None
    source_problem_id: Optional[str] = None
    raw_timestamp: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


def _normalize_raw_timestamp(raw: Optional[str]) -> Optional[datetime]:
    """Best-effort parser for external-dataset timestamp strings.

    Different KT datasets ship timestamps in different formats:
      * ASSISTments / CSEDM → ISO-8601 (or an empty string).
      * Junyi → Unix microseconds since epoch as a decimal string.
      * EdNet KT1 → Unix milliseconds since epoch.

    We coerce them all into ``datetime`` UTC. If we cannot parse, return
    ``None`` and the column stays NULL — better than silently exploding
    the entire INSERT (which would also lose the row from the audit
    surface).
    """
    if raw is None:
        return None
    stripped = raw.strip()
    if not stripped:
        return None
    if stripped.isdigit() or (stripped.startswith("-") and stripped[1:].isdigit()):
        value = int(stripped)
        # Heuristic for unit detection. Anything <1e12 is seconds,
        # 1e12..1e15 is milliseconds, ≥1e15 is microseconds. This is
        # consistent with how the rest of HCIE handles epoch values.
        abs_v = abs(value)
        if abs_v >= 10 ** 15:
            ts_s = value / 1_000_000.0
        elif abs_v >= 10 ** 12:
            ts_s = value / 1_000.0
        else:
            ts_s = float(value)
        try:
            return datetime.fromtimestamp(ts_s, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    try:
        return datetime.fromisoformat(stripped.replace("Z", "+00:00"))
    except ValueError:
        return None


@router.post("/{cohort_id}/runs/{run_id}/external_attempt")
async def external_run_attempt(
    cohort_id: str,
    run_id: str,
    body: ExternalAttemptRequest,
    user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Dict[str, Any]:
    """Apply one external-log attempt to the runtime.

    Semantically equal to one synthetic-loop iteration: issue a
    synthetic-learner JWT, POST /v3/learner/attempt internally, record
    the trajectory row, and mirror to ``external_log_attempts``. The
    Kafka outbox fires inside ITS.submit_attempt as usual, so all
    downstream consumers (projection, trajectory recorder, replay,
    audit) see this attempt as a first-class event.
    """
    store = _store()
    base_url = os.getenv("HCIE_INTERNAL_BASE_URL", "http://127.0.0.1:8000")
    token = _token_for_synthetic_user(body.synthetic_user_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-HCIE-Deterministic": "true",
        "X-HCIE-Deterministic-Seed": str(body.attempt_index + 1),
    }
    event_id = f"{run_id}:{body.synthetic_user_id}:{body.attempt_index}"
    state_before = _latest_learning_state(store, body.synthetic_user_id, body.concept_id)
    raw_ts = _normalize_raw_timestamp(body.raw_timestamp)

    # IMPORTANT: ``_post_with_backoff`` is sync (``requests.post``); running it
    # inline on this ``async def`` would block the event loop and prevent
    # uvicorn from serving the inner ``/v3/learner/attempt`` call, producing a
    # self-deadlock. Hand it to a worker thread so the loopback call lands.
    # Tier 2.5c2: forward V2 trigger fields (is_assessment / prereq_weights /
    # adaptation_context) from the producer-supplied metadata into
    # signal_detail so ITS lifts them onto event_data and jt_v2_signals.
    # ChallengeEventTrigger sees the assessment flag. Datasets that don't
    # tag assessments simply omit the key — trigger then defaults to False.
    _signal_detail: Dict[str, Any] = {}
    _meta_dict = body.metadata or {}
    for _v2_key in (
        "is_assessment",
        "assessment_flag",
        "assessment",
        "prereq_weights",
        "adaptation_context",
    ):
        if _v2_key in _meta_dict and _meta_dict[_v2_key] is not None:
            _signal_detail[_v2_key] = _meta_dict[_v2_key]

    attempt_response = await asyncio.to_thread(
        _post_with_backoff,
        f"{base_url}/v3/learner/attempt",
        json_payload={
            "task_id": body.task_id,
            "concept_id": body.concept_id,
            "answer": "external_log",
            "correct": body.correct,
            "response_time": body.response_time,
            "event_id": event_id,
            "signal_detail": _signal_detail,
        },
        headers=headers,
        timeout=30,
    )
    if attempt_response.status_code >= 400:
        # Mirror the failure into external_log_attempts so the audit
        # can attribute coverage gaps. Do NOT raise — the orchestrator
        # decides whether a partial run is acceptable.
        store.execute_write(
            """
            INSERT INTO external_log_attempts (
                experiment_run_id, dataset_id,
                source_user_id, source_skill_id, source_problem_id,
                user_id, concept_id, task_id,
                attempt_index, correct, response_time,
                raw_timestamp, submitted_event_id, api_status, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                run_id, body.dataset_id,
                body.source_user_id or "", body.source_skill_id or "",
                body.source_problem_id,
                body.synthetic_user_id, body.concept_id, body.task_id,
                body.attempt_index, body.correct, body.response_time,
                raw_ts, None, attempt_response.status_code,
                json.dumps({**body.metadata, "error": attempt_response.text[:512]}),
            ),
        )
        return {
            "status": "error",
            "run_id": run_id,
            "api_status": attempt_response.status_code,
            "detail": attempt_response.text[:512],
        }

    attempt_json = attempt_response.json()
    _record_trajectory(
        store,
        run_id=run_id,
        user_id=body.synthetic_user_id,
        concept_id=body.concept_id,
        interaction_id=event_id,
        event_id=attempt_json.get("event_id") or event_id,
        interaction_number=body.attempt_index + 1,
        state_before=state_before or {},
        attempt_response=attempt_json,
        recommendation={
            "task_id": body.task_id,
            "concept_id": body.concept_id,
            "selection_metrics": {},
        },
        policy_label=f"external_log:{body.dataset_id}",
        selected_arm=body.task_id,
        correctness=body.correct,
        response_time=body.response_time,
        difficulty=None,
    )

    store.execute_write(
        """
        INSERT INTO external_log_attempts (
            experiment_run_id, dataset_id,
            source_user_id, source_skill_id, source_problem_id,
            user_id, concept_id, task_id,
            attempt_index, correct, response_time,
            raw_timestamp, submitted_event_id, api_status, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (
            run_id, body.dataset_id,
            body.source_user_id or "", body.source_skill_id or "",
            body.source_problem_id,
            body.synthetic_user_id, body.concept_id, body.task_id,
            body.attempt_index, body.correct, body.response_time,
            raw_ts,
            attempt_json.get("event_id"),
            attempt_response.status_code,
            json.dumps(body.metadata),
        ),
    )

    return {
        "status": "ok",
        "run_id": run_id,
        "event_id": attempt_json.get("event_id"),
        "user_id": body.synthetic_user_id,
        "concept_id": body.concept_id,
        "task_id": body.task_id,
        "mastery_after": attempt_json.get("mastery"),
        "payload": attempt_json.get("payload") or {},
    }


class ExternalFinalizeRequest(BaseModel):
    status: str = "completed"
    progress: Dict[str, Any] = Field(default_factory=dict)


@router.post("/{cohort_id}/runs/{run_id}/external_finalize")
async def external_run_finalize(
    cohort_id: str,
    run_id: str,
    body: ExternalFinalizeRequest,
    _user: Dict[str, Any] = Depends(require_researcher_or_admin),
) -> Dict[str, Any]:
    """Set the terminal status for an external-log run."""
    store = _store()
    store.execute_write(
        """
        UPDATE cohort_runs
        SET status = %s,
            progress = %s::jsonb,
            completed_at = NOW(),
            updated_at = NOW()
        WHERE run_id = %s AND cohort_id = %s
        """,
        (body.status, json.dumps(body.progress), run_id, cohort_id),
    )
    return {"status": "ok", "run_id": run_id, "final_status": body.status}
