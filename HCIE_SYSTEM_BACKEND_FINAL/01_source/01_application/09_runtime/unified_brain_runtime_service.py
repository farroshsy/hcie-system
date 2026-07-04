from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class RuntimeMode(str, Enum):
    """Phase 14g (Slice 0a): only CANONICAL_WRITE is canonical.

    `READ_ONLY`, `SHADOW`, and `REPLAY` were declared but never implemented
    (they returned metadata-only placeholders). Per the Semantic Honesty Law
    they have been removed from the public runtime API to prevent fake
    authority surfaces. Read paths go through `ItsRuntimeService.recommend`
    / `get_progress` (which read the Slice 2 `learner_projections` read model);
    shadow/replay paths go through `ReplayEngine` on demand (Slice 4c).
    """

    CANONICAL_WRITE = "canonical_write"


@dataclass(frozen=True)
class ConceptScope:
    primary_concept: Optional[str] = None
    candidate_concepts: List[str] = field(default_factory=list)
    working_set_policy: str = "top_k_governance"


@dataclass
class RuntimeResult:
    user_id: str
    concept_id: Optional[str]
    mode: RuntimeMode
    payload: Dict[str, Any]
    semantic_version: str = "1.0"


class UnifiedBrainRuntimeService:
    def __init__(
        self,
        *,
        role,
        settings,
        unified_brain=None,
        postgres_store=None,
        outbox=None,
        idempotency_manager=None,
        ownership=None,
        transaction_factory=None,
    ):
        self.role = role
        self.settings = settings
        self.unified_brain = unified_brain
        self.postgres_store = postgres_store
        self.outbox = outbox
        self.idempotency_manager = idempotency_manager
        self.ownership = ownership
        self.transaction_factory = transaction_factory

    def get_runtime_authority_state(self) -> Dict[str, Any]:
        return {
            "service": "UnifiedBrainRuntimeService",
            "role": str(self.role.value if hasattr(self.role, "value") else self.role),
            "semantic_version": "1.0",
            "authority": "converging",
        }

    def _set_ownership_writer(self) -> None:
        if not self.ownership:
            return
        try:
            from core.ownership.ownership_enforcement import CognitionWriter

            self.ownership.set_writer(CognitionWriter.UNIFIED_BRAIN)
        except Exception:
            self.ownership.set_writer("UNIFIED_BRAIN")

    def _clear_ownership_writer(self) -> None:
        if self.ownership:
            self.ownership.clear_writer()

    def _transaction(self):
        if self.transaction_factory:
            return self.transaction_factory()
        if self.postgres_store:
            from app.infrastructure.unit_of_work import get_transaction

            return get_transaction(self.postgres_store)
        from contextlib import nullcontext

        return nullcontext()

    def _save_cognition_outbox_event(self, tx, event_id: str, user_id: str, concept_id: str, payload: Dict[str, Any], event_data: Optional[Dict[str, Any]] = None) -> None:
        if not self.outbox:
            return
        manifest = getattr(self.unified_brain, "capability_manifest", None)
        manifest_fingerprint = getattr(manifest, "fingerprint", None)
        if manifest_fingerprint:
            payload.setdefault("capability_manifest_fingerprint", manifest_fingerprint)
        timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
        
        # 🔥 TRAFFIC CLASSIFICATION: Determine traffic type from user_id and event_data
        # This ensures human traffic is correctly classified in the outbox for proper governance field extraction
        traffic_type = "human"  # default to human for real users
        if str(user_id).startswith("run-") or str(user_id).startswith("synthetic:") or str(user_id).startswith("ex_"):
            traffic_type = "research"
        if event_data and event_data.get("traffic_type"):
            traffic_type = event_data.get("traffic_type")
        
        outbox_payload = {
            "event_id": f"{event_id}_cognition",
            "event_type": "CognitionUpdated",
            "source": "unified_brain_runtime_service",
            "timestamp": timestamp,
            "user_id": user_id,
            "concept_id": concept_id,
            "interaction_id": event_id,  # 🔥 Fix: Set interaction_id to base event_id for trajectory deduplication
            "capability_manifest_fingerprint": manifest_fingerprint,
            "result": payload,
            "traffic_type": traffic_type,  # 🔥 Add traffic_type to ensure proper classification
        }
        event = self.outbox.create_event(
            event_id=outbox_payload["event_id"],
            event_type=outbox_payload["event_type"],
            topic="learning_analytics",
            payload=outbox_payload,
        )
        self.outbox.save_event(event, transaction=tx)

    def process_interaction(
        self,
        *,
        user_id: str,
        concept_id: str,
        interaction: Dict[str, Any],
        event_id: str,
        event_data: Optional[Dict[str, Any]] = None,
        mode: RuntimeMode = RuntimeMode.CANONICAL_WRITE,
    ) -> RuntimeResult:
        if mode != RuntimeMode.CANONICAL_WRITE:
            raise NotImplementedError(
                f"RuntimeMode={mode!r} is not implemented in FINAL runtime topology. "
                f"Only CANONICAL_WRITE is canonical (Phase 14g Slice 0a). "
                f"For replay, use ReplayEngine via /v3/experiments/.../replay. "
                f"For read paths, use ItsRuntimeService.recommend / get_progress."
            )

        if self.idempotency_manager and self.idempotency_manager.is_processed(event_id):
            return RuntimeResult(
                user_id=user_id,
                concept_id=concept_id,
                mode=mode,
                payload=self.idempotency_manager.get_cached_result(event_id),
            )

        lock_acquired = True
        if self.idempotency_manager:
            lock_acquired = self.idempotency_manager.acquire_lock(event_id)
        if not lock_acquired:
            raise RuntimeError(f"Could not acquire idempotency lock for {event_id}")

        try:
            with self._transaction() as tx:
                self._set_ownership_writer()
                try:
                    if not self.unified_brain:
                        raise RuntimeError("UnifiedBrain is not configured for this runtime service")
                    result = self.unified_brain.process_event(
                        user_id=user_id,
                        concept=concept_id,
                        interaction=interaction,
                        mode="write",
                        event_id=event_id,
                        interaction_id=event_id,
                        write_enabled=True,
                        event_data=event_data or {},
                    )
                    # Extract full governance payload from real UnifiedBrain result
                    payload = {
                        "event_id": getattr(result, "event_id", None) or event_id,
                        # 6D Governance Components
                        "delta_m": getattr(result, "mastery_delta", None),  # Mastery gain
                        "transfer_realized": getattr(result, "transfer_efficiency", None),
                        "transfer_prospective": getattr(result, "transfer_prospective", None),
                        "challenge": getattr(result, "challenge", None),
                        "uncertainty": getattr(result, "uncertainty", None),
                        "zpd": getattr(result, "zpd_score", None),
                        # Core learning metrics
                        "mastery": getattr(result, "mastery", None),
                        "ensemble_variance": getattr(result, "ensemble_variance", None),
                        "confidence": getattr(result, "confidence", None),
                        # JT governance
                        "J_value": getattr(result, "J_value", None),
                        # ZPD details
                        "zpd_score": getattr(result, "zpd_score", None),
                        "zpd_target": getattr(result, "zpd_target", None),
                        "zpd_alignment_error": getattr(result, "zpd_alignment_error", None),
                        "zpd_delta_signal": getattr(result, "zpd_delta_signal", None),
                        # Learner states
                        "lyapunov_mastery": getattr(result, "lyapunov_mastery", None),
                        "bayesian_alpha": getattr(result, "bayesian_alpha", None),
                        "bayesian_beta": getattr(result, "bayesian_beta", None),
                        "bayesian_gamma": getattr(result, "bayesian_gamma", None),
                        "kalman_mastery": getattr(result, "kalman_mastery", None),
                        "kalman_covariance": getattr(result, "kalman_covariance", None),
                        "kalman_process_noise": getattr(result, "kalman_process_noise", None),
                        "kalman_measurement_noise": getattr(result, "kalman_measurement_noise", None),
                        # Ensemble configuration
                        "ensemble_weights": getattr(result, "ensemble_weights", None),
                        # Policy
                        "policy": getattr(result, "policy", None),
                        "policy_multiplier": getattr(result, "policy_multiplier", None),
                        # Adaptive learning
                        "adaptive_rate": getattr(result, "adaptive_rate", None),
                        # Transfer learning
                        "transfer_amounts": getattr(result, "transfer_amounts", None),
                        # Processing metadata
                        "processing_mode": getattr(result, "processing_mode", None),
                        "timestamp": getattr(result, "timestamp", None),
                        # 🔥 PHASE A / Tier-2 audit: surface normalized 6D
                        # decomposition, attribution share, weight snapshot and
                        # governance observability so the cohort writer can persist
                        # them as explicit FLOAT/JSONB columns rather than recover
                        # them via JSON archaeology.
                        "jt_delta_m_contribution": getattr(result, "jt_delta_m_contribution", None),
                        "jt_transfer_contribution": getattr(result, "jt_transfer_contribution", None),
                        "jt_transfer_prospective_contribution": getattr(
                            result, "jt_transfer_prospective_contribution", None
                        ),
                        "jt_challenge_contribution": getattr(result, "jt_challenge_contribution", None),
                        "jt_uncertainty_contribution": getattr(result, "jt_uncertainty_contribution", None),
                        "jt_zpd_contribution": getattr(result, "jt_zpd_contribution", None),
                        "jt_unclamped": getattr(result, "jt_unclamped", None),
                        "jt_clamped": getattr(result, "jt_clamped", None),
                        "jt_attribution": getattr(result, "jt_attribution", None),
                        "weights_snapshot": getattr(result, "weights_snapshot", None),
                        # Tier 2.5 V2 dims (nullable unless HCIE_REDESIGN_V2=1).
                        "jt_baseline_difficulty_contribution": getattr(result, "jt_baseline_difficulty_contribution", None),
                        "jt_challenge_event_contribution": getattr(result, "jt_challenge_event_contribution", None),
                        "jt_population_prior_contribution": getattr(result, "jt_population_prior_contribution", None),
                        "jt_t_realized_v2_contribution": getattr(result, "jt_t_realized_v2_contribution", None),
                        "jt_v2_active": getattr(result, "jt_v2_active", None),
                        "jt_v2_state_snapshot": getattr(result, "jt_v2_state_snapshot", None),
                        "jt_v2_challenge_event_fired": getattr(result, "jt_v2_challenge_event_fired", None),
                        "jt_v2_challenge_event_reason": getattr(result, "jt_v2_challenge_event_reason", None),
                        "jt_volatility": getattr(result, "jt_volatility", None),
                        "exploration_pressure": getattr(result, "exploration_pressure", None),
                        "stability_index": getattr(result, "stability_index", None),
                        "effective_learning_rate": getattr(result, "effective_learning_rate", None),
                        "mastery_delta": getattr(result, "mastery_delta", None),
                        # Ensemble-semantics evidence (migration 019). Kept
                        # semantically distinct from the JT 6D attribution
                        # above so the math audit treats them as separate
                        # layers.
                        "ensemble_mastery_estimate": getattr(result, "ensemble_mastery_estimate", None),
                        "canonical_mastery_after": getattr(result, "canonical_mastery_after", None),
                        "ensemble_variance_after": getattr(result, "ensemble_variance_after", None),
                        "bayesian_mastery_after": getattr(result, "bayesian_mastery_after", None),
                        "bayesian_variance_after": getattr(result, "bayesian_variance_after", None),
                        "kalman_gain_after": getattr(result, "kalman_gain_after", None),
                        "kalman_R_after": getattr(result, "kalman_R_after", None),
                        "ensemble_weight_lyapunov": getattr(result, "ensemble_weight_lyapunov", None),
                        "ensemble_weight_bayesian": getattr(result, "ensemble_weight_bayesian", None),
                        "ensemble_weight_kalman": getattr(result, "ensemble_weight_kalman", None),
                        "learner_jt_contribution_lyapunov": getattr(result, "learner_jt_contribution_lyapunov", None),
                        "learner_jt_contribution_bayesian": getattr(result, "learner_jt_contribution_bayesian", None),
                        "learner_jt_contribution_kalman": getattr(result, "learner_jt_contribution_kalman", None),
                        "ensemble_weight_method": getattr(result, "ensemble_weight_method", None),
                        "ensemble_ema_alpha": getattr(result, "ensemble_ema_alpha", None),
                        "ensemble_softmax_temperature": getattr(result, "ensemble_softmax_temperature", None),
                        "mastery_delta_direct": getattr(result, "mastery_delta_direct", None),
                        "transfer_amount_total": getattr(result, "transfer_amount_total", None),
                        # zpd_delta_signal is already on the result but
                        # not in the payload yet — promote.
                        "zpd_delta_signal_value": getattr(result, "zpd_delta_signal", None),
                        # Interaction correctness — carried through from the learner request
                        # so that experiment_trajectories.correctness is populated.
                        "correct":     interaction.get("correct"),
                        "correctness": interaction.get("correct"),
                    }
                    manifest = getattr(self.unified_brain, "capability_manifest", None)
                    manifest_fingerprint = getattr(manifest, "fingerprint", None)
                    if manifest_fingerprint:
                        payload["capability_manifest_fingerprint"] = manifest_fingerprint
                    self._save_cognition_outbox_event(tx, event_id, user_id, concept_id, payload, event_data)
                finally:
                    self._clear_ownership_writer()

            if self.idempotency_manager:
                self.idempotency_manager.mark_processed(event_id, payload)
            return RuntimeResult(user_id=user_id, concept_id=concept_id, mode=mode, payload=payload)
        finally:
            if self.idempotency_manager:
                self.idempotency_manager.release_lock(event_id)
