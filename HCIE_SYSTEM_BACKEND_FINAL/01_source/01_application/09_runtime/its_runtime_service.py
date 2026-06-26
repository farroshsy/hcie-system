"""
ItsRuntimeService — Phase 14e production ITS façade.

H2 ingress coordinator: routes reads through RecommendationProjection and
writes through UnifiedBrainRuntimeService (H1 mutation authority).
No synthetic mastery or fabricated selection metrics (final_intent §7).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.determinism.deterministic_config import (
    DeterministicModeConfig,
    set_global_deterministic_config,
)


def _load_runtime_mode():
    """Import RuntimeMode without pulling ``app.services`` package (TaskService chain)."""
    mod_name = "_hcie_unified_brain_runtime_service_isolated"
    if mod_name in sys.modules:
        return sys.modules[mod_name].RuntimeMode
    path = Path(__file__).resolve().parent / "unified_brain_runtime_service.py"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod.RuntimeMode


RuntimeMode = _load_runtime_mode()


class RuntimeDegraded(Exception):
    """Raised when the ITS spine cannot serve a request without synthetic cognition."""

    def __init__(self, reason: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(reason)
        self.reason = reason
        self.details = details or {}


@dataclass
class RecommendationView:
    """ITS recommendation view.

    Slice 0a (Phase 14g) removed ``policy_mode`` — the brain ignored it and
    only the OTel span recorded the value, contaminating telemetry. The
    field is gone from both the request and the response until policy
    filtering is canonical in ``ItsRuntimeService.recommend``.
    """

    user_id: str
    recommended_concept: str
    task_id: Optional[str]
    concept_id: Optional[str]
    representation: Optional[str]
    difficulty: Optional[float]
    question_text: Optional[str]
    choices: List[Any]
    selection_metrics: Dict[str, Any]
    recommendation_metadata: Dict[str, Any]
    kind: Optional[str] = None
    content: Dict[str, Any] = field(default_factory=dict)
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    transcript: Optional[str] = None
    governance: Dict[str, Any] = field(default_factory=dict)
    cold_start: Dict[str, Any] = field(default_factory=dict)
    deterministic_inputs_hash: Optional[str] = None
    semantic_version: str = "1.0"


@dataclass
class AttemptResult:
    user_id: str
    event_id: str
    concept_id: str
    correct: bool
    mastery: Optional[float]
    payload: Dict[str, Any]
    semantic_version: str = "1.0"


@dataclass
class ProgressView:
    user_id: str
    concepts: Dict[str, float]
    semantic_version: str = "1.0"


@dataclass
class SessionView:
    """Slice 0a (Phase 14g): ``policy_mode`` removed (see RecommendationView)."""

    user_id: str
    active_concept: Optional[str]
    semantic_version: str = "1.0"


class ItsRuntimeService:
    """Canonical ITS runtime façade (DI-driven)."""

    # K-12 CS Framework concepts that have seeded tasks in the catalog.
    # The MAB rotates across these for new learners; the prerequisite DAG
    # (k2 → k5 → k8 → k12) shapes natural progression as mastery climbs.
    DEFAULT_CONCEPTS = (
        "k2_algorithms", "k5_algorithms", "k8_algorithms", "k12_algorithms",
        "k2_control",    "k5_control",    "k8_control",    "k12_control",
    )

    SUPPORTED_POLICIES: Tuple[str, ...] = (
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
    )

    def __init__(
        self,
        *,
        spine: Any,
        projection: Any,
        personalizer: Any,
        rng: Any,
        logger: Any,
        metrics: Any,
        tracer: Any,
        postgres_store: Any,
        bandit: Optional[Any] = None,
        outbox: Optional[Any] = None,
    ) -> None:
        self.spine = spine
        self.projection = projection
        self.personalizer = personalizer
        self.rng = rng
        self.logger = logger
        self.metrics = metrics
        self.tracer = tracer
        self.postgres_store = postgres_store
        self.bandit = bandit
        self.outbox = outbox

    def _apply_deterministic_config(
        self, deterministic: Optional[DeterministicModeConfig]
    ) -> Optional[str]:
        if deterministic is None or not deterministic.deterministic:
            set_global_deterministic_config(None)
            return None
        set_global_deterministic_config(deterministic)
        if self.rng is not None and hasattr(self.rng, "base_seed"):
            self.rng.base_seed = deterministic.seed
            # Slice 4d: ``base_seed`` is mutated per request, but the
            # ``np.random.RandomState`` streams were only constructed once at
            # startup. Without a reset, deterministic replays inherit drift
            # from prior requests. Resetting only in experimental mode keeps
            # the live runtime sequence semantics intact.
            reset_all = getattr(self.rng, "reset_all", None)
            if callable(reset_all):
                try:
                    reset_all()
                except Exception as exc:  # pragma: no cover - defensive
                    self.logger.warning(
                        "rng_reset_failed",
                        seed=deterministic.seed,
                        error=str(exc),
                    )
        payload = {
            "seed": deterministic.seed,
            "deterministic": deterministic.deterministic,
            "trajectory_determinism": deterministic.trajectory_determinism,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _is_synthetic_user(user_id: str) -> bool:
        return str(user_id).startswith("synthetic:")

    def recommend(
        self,
        user_id: str,
        *,
        concept_filter: Optional[List[str]] = None,
        deterministic: Optional[DeterministicModeConfig] = None,
        policy: Optional[str] = None,
        language: Optional[List[str]] = None,
    ) -> RecommendationView:
        det_hash = self._apply_deterministic_config(deterministic)
        normalized_policy = self._normalize_policy(user_id, policy)
        with self.tracer.start_span("its.recommend", user_id=user_id):
            self.metrics.incr("hcie_its_recommend_total", user_id=user_id)
            try:
                # 🔥 P0 FIX: Single recommendation authority
                # Use bandit for concept selection instead of asking projection
                # Projection observes recommendations; it does not generate them
                raw_concepts = list(concept_filter) if concept_filter else list(self.DEFAULT_CONCEPTS)
                available_concepts = self._unlocked_concepts_for_user(user_id, raw_concepts)
                if not available_concepts:
                    if concept_filter:
                        raise RuntimeDegraded(
                            "concept_locked",
                            details={
                                "requested_concepts": raw_concepts,
                                "lock_states": self.get_concept_lock_states(user_id, raw_concepts),
                            },
                        )
                    available_concepts = self._foundation_concepts(raw_concepts)

                if self.bandit:
                    concept_id = self._select_concept_with_bandit(
                        user_id, available_concepts, normalized_policy
                    )
                else:
                    # Fallback to first available concept if bandit not available
                    concept_id = available_concepts[0]
                    self.logger.warning(
                        "hcie_recommendation_bandit_fallback",
                        user_id=user_id,
                        fallback_concept=concept_id,
                        reason="bandit_not_available"
                    )

                # 🔥 P0: Emit RecommendationGenerated event for single authority trace
                self._emit_recommendation_event(
                    user_id=user_id,
                    concept_id=concept_id,
                    policy=normalized_policy or "hcie",
                    deterministic_hash=det_hash,
                )

                # 🛡 Concept validation guard: the bandit can return a sentinel
                # like "unknown" (from a stale/cold-start projection row) or a
                # concept_id with no tasks in the K-12 catalog. Both cause
                # _pick_task → k12_task_not_found → 503 to the learner.
                # Validate against the active task catalog and fall back to a
                # known-good starter concept on any mismatch.
                if not concept_id or concept_id == "unknown" or concept_id not in available_concepts:
                    fallback = self._resolve_fallback_concept(available_concepts)
                    self.logger.warning(
                        "hcie_recommendation_invalid_concept_fallback",
                        user_id=user_id,
                        bandit_returned=concept_id,
                        fallback_to=fallback,
                        available_concepts=available_concepts,
                    )
                    concept_id = fallback

                if concept_filter and concept_id not in concept_filter:
                    concept_id = concept_filter[0]

                task, pick_meta = self._pick_task(
                    user_id,
                    concept_id,
                    deterministic,
                    policy=normalized_policy,
                    language=language,
                )
                cold_start_info = self._cold_start_view(user_id, concept_id)
                governance = self._governance_view(user_id, concept_id)
                metrics = {
                    "policy_type": "cold_start_its" if cold_start_info.get("active") else "its_runtime",
                    "policy_selector": pick_meta["policy_selector"],
                    "policy_score": pick_meta.get("policy_score"),
                    "candidates_count": pick_meta["candidates_count"],
                    "candidate_arm_scores": pick_meta.get("candidate_arm_scores") or [],
                    "selected_task_id": pick_meta.get("selected_task_id"),
                    "deterministic": bool(det_hash),
                }
                if det_hash:
                    metrics["deterministic_inputs_hash"] = det_hash

                # ── Archetype × Task covariate (observational only) ───────
                # We attach the learner's archetype profile and the selected
                # task's archetype tags to selection_metrics so the instructor
                # dashboard can do "Archetype × Concept" analysis. This is
                # deliberately NOT folded into the bandit score — that would
                # contaminate HCIE/JT validation (see Slice 5b design note).
                archetype_payload = self._archetype_covariate(
                    user_id, pick_meta.get("archetype_tags") or []
                )
                if archetype_payload is not None:
                    metrics["archetype_covariate"] = archetype_payload
                metrics["language"] = pick_meta.get("language")

                # ── Representation (modality) bandit decision (observational) ──
                # Surface which modality the representation bandit chose and the
                # per-arm Beta posteriors so the dashboard can show modality
                # adaptation. Absent until the learner has interaction history.
                if pick_meta.get("representation_selected") is not None:
                    metrics["representation_selected"] = pick_meta.get("representation_selected")
                    metrics["representation_candidates"] = pick_meta.get("representation_candidates") or []
                    metrics["representation_arms"] = pick_meta.get("representation_arms") or {}

                # 🔥 P0 FIX: Build recommendation metadata from single authority
                recommendation_metadata = {
                    "confidence": 0.7,  # Default confidence from bandit selection
                    "authority": "unified_brain_bandit",  # Single source of truth
                    "policy": normalized_policy or "hcie",
                    "reason": "bandit_concept_selection",
                }

                return RecommendationView(
                    user_id=user_id,
                    recommended_concept=concept_id,
                    task_id=task.get("task_id") or task.get("id"),
                    concept_id=task.get("concept_id") or concept_id,
                    representation=task.get("representation") or task.get("task_type", "text"),
                    difficulty=float(task.get("difficulty", 0.5)),
                    question_text=task.get("question_text"),
                    choices=task.get("choices") or [],
                    kind=task.get("kind") or task.get("representation") or task.get("task_type"),
                    content=task.get("content") or {},
                    media_url=task.get("media_url"),
                    media_type=task.get("media_type"),
                    transcript=task.get("transcript"),
                    selection_metrics=metrics,
                    recommendation_metadata=recommendation_metadata,
                    governance=governance,
                    cold_start=cold_start_info,
                    deterministic_inputs_hash=det_hash,
                )
            except RuntimeDegraded:
                raise
            except Exception as exc:
                self.logger.error(
                    "ITS recommend degraded",
                    user_id=user_id,
                    error=str(exc),
                )
                self.metrics.incr(
                    "hcie_its_degraded_total",
                    surface="recommend",
                    reason="recommend_failed",
                )
                raise RuntimeDegraded("recommend_failed", details={"error": str(exc)}) from exc

    def _resolve_fallback_concept(self, candidates: List[str]) -> str:
        """Return a concept_id that is guaranteed to have tasks in the catalog.

        Tried in order:
        1. First candidate in `candidates` that has tasks in `tasks` table.
        2. First DEFAULT_CONCEPTS entry that has tasks.
        3. Any K-12 concept with tasks (catalog-wide query).
        4. As a last resort, the first DEFAULT_CONCEPTS entry verbatim — this
           preserves call-site invariants even if the catalog is empty (in
           which case _pick_task will still raise, but with a more honest
           "catalog empty" rather than the misleading "concept=unknown").
        """
        for pool in (candidates, list(self.DEFAULT_CONCEPTS)):
            for c in pool:
                if not c or c == "unknown":
                    continue
                row = self.postgres_store.execute_read(
                    "SELECT 1 FROM tasks WHERE concept_id = %s AND concept_type = 'k12' LIMIT 1",
                    (c,),
                    fetch_one=True,
                )
                if row:
                    return c
        catalog = self.postgres_store.execute_read(
            "SELECT concept_id FROM tasks WHERE concept_type = 'k12' "
            "GROUP BY concept_id ORDER BY COUNT(*) DESC LIMIT 1",
            fetch_one=True,
        )
        if catalog and catalog.get("concept_id"):
            return catalog["concept_id"]
        return self.DEFAULT_CONCEPTS[0]

    def _task_catalog_concepts(self) -> List[str]:
        """Return K-12 concepts that currently have task rows."""
        try:
            rows = self.postgres_store.execute_read(
                """
                SELECT concept_id
                FROM tasks
                WHERE concept_type = 'k12' AND concept_id IS NOT NULL
                GROUP BY concept_id
                ORDER BY concept_id
                """
            )
            return [str(r["concept_id"]) for r in rows or [] if r.get("concept_id")]
        except Exception as exc:
            self.logger.warning("task_catalog_concepts_failed", error=str(exc))
            return list(self.DEFAULT_CONCEPTS)

    def _concept_prereq_map(self, concepts: List[str]) -> Dict[str, List[str]]:
        """Hard prerequisite map for target concepts.

        `concept_dependencies` also contains `advanced` and `related` edges used
        for transfer. Only `dependency_type = 'prerequisite'` should hard-lock a
        learner out of a concept.
        """
        clean = [c for c in dict.fromkeys(concepts) if c]
        if not clean:
            return {}
        prereqs: Dict[str, List[str]] = {c: [] for c in clean}
        try:
            rows = self.postgres_store.execute_read(
                """
                SELECT target_concept AS concept_id, source_concept AS prereq
                FROM concept_dependencies
                WHERE dependency_type = 'prerequisite'
                  AND target_concept = ANY(%s)
                ORDER BY target_concept, source_concept
                """,
                (clean,),
            )
            for row in rows or []:
                concept = str(row.get("concept_id") or "")
                prereq = str(row.get("prereq") or "")
                if concept and prereq:
                    prereqs.setdefault(concept, []).append(prereq)
        except Exception as exc:
            self.logger.warning(
                "concept_prereq_lookup_failed",
                concepts=clean,
                error=str(exc),
            )
        return prereqs

    @staticmethod
    def _mastery_from_state(state: Any) -> float:
        if isinstance(state, str):
            try:
                state = json.loads(state)
            except json.JSONDecodeError:
                state = {}
        if not isinstance(state, dict):
            return 0.0
        raw = (
            state.get("mastery")
            or state.get("lyapunov_mastery")
            or state.get("kalman_mastery")
            or state.get("bayesian_mastery")
        )
        try:
            return max(0.0, min(1.0, float(raw)))
        except (TypeError, ValueError):
            return 0.0

    def _mastery_map_for_user(self, user_id: str, concepts: List[str]) -> Dict[str, float]:
        clean = [c for c in dict.fromkeys(concepts) if c]
        if not clean:
            return {}
        try:
            rows = self.postgres_store.execute_read(
                """
                SELECT DISTINCT ON (concept) concept, state_data
                FROM learning_state
                WHERE user_id::text = %s AND concept = ANY(%s)
                ORDER BY concept, updated_at DESC NULLS LAST
                """,
                (str(user_id), clean),
            )
        except Exception as exc:
            self.logger.warning(
                "mastery_map_lookup_failed",
                user_id=user_id,
                concepts=clean,
                error=str(exc),
            )
            rows = []
        result: Dict[str, float] = {}
        for row in rows or []:
            concept = row.get("concept")
            if concept:
                result[str(concept)] = self._mastery_from_state(row.get("state_data"))
        return result

    def get_concept_lock_states(
        self,
        user_id: str,
        concepts: Optional[List[str]] = None,
        *,
        mastery_threshold: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """Return locked/unlocked state for each concept from the active DAG."""
        candidates = list(concepts) if concepts else self._task_catalog_concepts()
        prereq_map = self._concept_prereq_map(candidates)
        all_prereqs = sorted({p for vals in prereq_map.values() for p in vals})
        mastery = self._mastery_map_for_user(user_id, all_prereqs)
        states: List[Dict[str, Any]] = []
        for concept in candidates:
            prereqs = prereq_map.get(concept, [])
            missing = [p for p in prereqs if mastery.get(p, 0.0) < mastery_threshold]
            states.append(
                {
                    "id": concept,
                    "locked": bool(missing),
                    "prerequisites": prereqs,
                    "missing_prereqs": missing,
                    "mastery_threshold": mastery_threshold,
                }
            )
        return states

    def _unlocked_concepts_for_user(
        self,
        user_id: str,
        candidates: List[str],
        *,
        mastery_threshold: float = 0.6,
    ) -> List[str]:
        """Filter candidate concepts before the bandit sees them."""
        states = self.get_concept_lock_states(
            user_id,
            candidates,
            mastery_threshold=mastery_threshold,
        )
        unlocked = [s["id"] for s in states if not s.get("locked")]
        if len(unlocked) != len(candidates):
            self.logger.info(
                "hcie_prereq_concepts_filtered",
                user_id=user_id,
                before=len(candidates),
                after=len(unlocked),
                locked=[s for s in states if s.get("locked")],
            )
        return unlocked

    def _foundation_concepts(self, candidates: Optional[List[str]] = None) -> List[str]:
        """Concepts with no hard prerequisites, constrained to active tasks."""
        pool = list(candidates) if candidates else self._task_catalog_concepts()
        prereq_map = self._concept_prereq_map(pool)
        foundation = [c for c in pool if not prereq_map.get(c)]
        if foundation:
            return foundation
        fallback = self._resolve_fallback_concept(pool)
        return [fallback] if fallback else list(self.DEFAULT_CONCEPTS[:1])

    def _select_concept_with_bandit(
        self,
        user_id: str,
        available_concepts: List[str],
        policy: str
    ) -> str:
        """
        Select concept using bandit (single recommendation authority).

        For the ``random`` baseline policy we pick uniformly so the baseline
        genuinely scatters across concepts.  HCIE/ZPD policies use the
        Thompson-sampling bandit fed by _read_posterior — this avoids the
        earlier crash caused by passing interaction=None into the spine.
        """
        # Random baseline: uniform concept selection (no ZPD bias)
        if policy == "random":
            try:
                n = len(available_concepts)
                idx = int(self.rng.get_bandit_stream().randint(0, n))
                return available_concepts[idx % n]
            except Exception:
                import random as _stdlib_random
                return _stdlib_random.choice(available_concepts)

        try:
            # Read mastery/uncertainty from learning_state via _read_posterior
            # (safe: returns defaults 0.3/0.5 for cold-start users)
            mastery_params = {}
            difficulty_map = {}

            for concept in available_concepts:
                mastery, uncertainty = self._read_posterior(user_id, concept)
                # Convert mastery + uncertainty into Beta prior:
                # mean = mastery, pseudo-count = 1/uncertainty^2 (higher uncertainty → weaker prior)
                pseudo_n = max(2.0, min(20.0, 1.0 / (uncertainty ** 2 + 1e-6)))
                alpha = mastery * pseudo_n
                beta = (1.0 - mastery) * pseudo_n
                mastery_params[concept] = (max(0.5, alpha), max(0.5, beta))
                try:
                    difficulty_map[concept] = self._get_concept_difficulty(concept)
                except Exception:
                    difficulty_map[concept] = 0.5

            selected_concept, _, score = self.bandit.select_arm(
                user_id=user_id,
                available_nodes=available_concepts,
                mastery_params=mastery_params,
                representation_params={},
                difficulty_map=difficulty_map,
                context={"policy": policy},
            )

            self.logger.info(
                "hcie_concept_selected",
                user_id=user_id,
                selected_concept=selected_concept,
                policy=policy,
                score=score,
            )

            return selected_concept

        except Exception as exc:
            self.logger.error(
                "hcie_bandit_selection_failed",
                user_id=user_id,
                error=str(exc),
            )
            return available_concepts[0]

    def _emit_recommendation_event(
        self,
        user_id: str,
        concept_id: str,
        policy: str,
        deterministic_hash: Optional[str],
    ) -> None:
        """
        Emit RecommendationGenerated event for single authority trace.
        
        🔥 CRITICAL: This event establishes the recommendation decision as the single
        source of truth. ProjectionConsumer persists this to learner_projections,
        ensuring all downstream components observe the same decision.
        """
        if not self.outbox:
            self.logger.debug(
                "recommendation_event_skipped",
                user_id=user_id,
                reason="outbox_not_available"
            )
            return
        
        try:
            from datetime import datetime, timezone
            from messaging.schema.canonical_events import RecommendationGenerated

            # P2 fix: BaseCanonicalEvent requires event_timestamp + emitted_at
            # (both no-default). The previous construction omitted them, raising
            # a Pydantic ValidationError that was swallowed by the except below —
            # so RecommendationGenerated never reached the outbox and the
            # recommendation-authority chain (→ learner_projections) never fired.
            # Pass ISO strings (not datetime objects): the event payload is
            # later JSON-serialized for the outbox envelope, and datetime
            # objects are not JSON-serializable. Pydantic coerces ISO strings
            # into the model's datetime fields, and the serialized form stays
            # JSON-safe — matching the working CognitionUpdated emit path.
            _now_iso = datetime.now(timezone.utc).isoformat()
            event = RecommendationGenerated(
                event_type="RecommendationGenerated",
                user_id=user_id,
                recommendation_timestamp=_now_iso,
                event_timestamp=_now_iso,   # business time (required by BaseCanonicalEvent)
                emitted_at=_now_iso,         # system time (required by BaseCanonicalEvent)
                recommended_concept=concept_id,
                recommended_task_id=None,  # Task selection happens after concept
                recommended_difficulty=None,  # Will be determined by task selection
                policy=policy,
                confidence=0.7,  # Default confidence from bandit selection
                selection_metrics={
                    "policy": policy,
                    "authority": "unified_brain_bandit",
                    "deterministic": deterministic_hash is not None,
                },
                governance={},
                capability_manifest_fingerprint=None,
                deterministic_inputs_hash=deterministic_hash,
            )
            
            # Emit via outbox (correct pattern).
            # mode="json": the model's event_timestamp/emitted_at are typed
            # `datetime`; the outbox later runs json.dumps on the payload, which
            # cannot serialize datetime objects. mode="json" renders them as ISO
            # strings so the envelope serializes cleanly.
            outbox_event = self.outbox.create_event(
                event_id=f"recommend_{user_id}_{int(time.time())}",
                event_type="RecommendationGenerated",
                topic="learning_analytics",
                payload=event.model_dump(mode="json"),
            )
            self.outbox.save_event(outbox_event)
            
            self.logger.info(
                "recommendation_event_emitted",
                user_id=user_id,
                recommended_concept=concept_id,
                policy=policy,
            )
            
        except Exception as exc:
            self.logger.error(
                "recommendation_event_failed",
                user_id=user_id,
                error=str(exc),
            )
            # Don't fail the request if event emission fails

    def submit_attempt(
        self,
        user_id: str,
        *,
        task_id: str,
        concept_id: str,
        answer: Any,
        correct: Optional[bool] = None,
        response_time: float = 10.0,
        signal_detail: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None,
        deterministic: Optional[DeterministicModeConfig] = None,
    ) -> AttemptResult:
        det_hash = self._apply_deterministic_config(deterministic)
        event_id = event_id or str(uuid.uuid4())
        with self.tracer.start_span(
            "its.submit_attempt", user_id=user_id, event_id=event_id
        ):
            self.metrics.incr("hcie_its_submit_total", user_id=user_id)
            task = None
            try:
                task = self.postgres_store.get_task_by_id(task_id)
            except Exception as exc:
                self.logger.warning(
                    "task lookup failed",
                    task_id=task_id,
                    error=str(exc),
                )

            if correct is None and task is not None:
                user_answer = str(answer).strip().lower()
                correct_answer = str(task.get("correct_answer", "")).strip().lower()
                correct = user_answer == correct_answer or (
                    user_answer in correct_answer or correct_answer in user_answer
                )
            is_correct = bool(correct)

            interaction = {
                "correct": is_correct,
                "response_time": response_time,
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data_source": "its_runtime",
            }
            event_data = {"source": "its_runtime", "task_id": task_id}
            # Record the material modality so the representation bandit can learn
            # which representation works for this learner (interactions.representation).
            rep_label: Optional[str] = None
            if task is not None:
                try:
                    rep_label = self._row_representation(task)
                    interaction["representation"] = rep_label
                    event_data["representation"] = rep_label
                except Exception:
                    rep_label = None
            if signal_detail:
                interaction["signal_detail"] = signal_detail
                event_data["signal_detail"] = signal_detail
                # Tier 2.5c2: lift well-known V2 trigger fields from signal_detail
                # to the top of event_data so jt_v2_signals.compute_v2_signals()
                # picks them up via event_data.get("is_assessment") etc. The
                # producer (external KT runner / canonical-events emitter) places
                # these inside signal_detail; the V2 hot path reads them flat.
                for _v2_key in (
                    "is_assessment",
                    "assessment_flag",
                    "assessment",
                    "prereq_weights",
                    "adaptation_context",
                ):
                    if _v2_key in signal_detail and _v2_key not in event_data:
                        event_data[_v2_key] = signal_detail[_v2_key]
            if det_hash:
                interaction["deterministic_inputs_hash"] = det_hash
                event_data["deterministic_inputs_hash"] = det_hash
                event_data["deterministic"] = True
                event_data["deterministic_seed"] = deterministic.seed if deterministic else None

            result = self.spine.process_interaction(
                user_id=user_id,
                concept_id=concept_id,
                interaction=interaction,
                event_id=event_id,
                event_data=event_data,
                mode=RuntimeMode.CANONICAL_WRITE,
            )
            # Close the representation-bandit loop: persist the REAL (representation,
            # correct) outcome synchronously so the next recommend reads it via
            # _representation_outcomes. The async analytics_worker path hardcodes
            # representation='unknown'/correct=NULL, so it cannot feed the bandit.
            if (rep_label is not None
                    and not self._is_synthetic_user(user_id)
                    and hasattr(self.postgres_store, "save_interaction")):
                try:
                    self.postgres_store.save_interaction({
                        "user_id": user_id,
                        "concept_id": concept_id,
                        "representation": rep_label,
                        "correct": is_correct,
                        "reward": 1.0 if is_correct else 0.0,
                        "response_time": response_time,
                        "difficulty": float((task or {}).get("difficulty") or 0.5),
                        "task_id": task_id,
                        "policy_mode": "hcie",
                        "timestamp": datetime.utcnow(),
                    })
                except Exception:
                    pass
            payload = result.payload or {}
            if signal_detail:
                payload["signal_detail"] = signal_detail
            if det_hash:
                payload["deterministic_inputs_hash"] = det_hash
            mastery = payload.get("mastery")
            return AttemptResult(
                user_id=user_id,
                event_id=event_id,
                concept_id=concept_id,
                correct=is_correct,
                mastery=mastery,
                payload=payload,
            )

    def get_progress(self, user_id: str) -> ProgressView:
        if hasattr(self.projection, "progress_for_user"):
            return ProgressView(
                user_id=user_id,
                concepts=self.projection.progress_for_user(
                    user_id,
                    include_synthetic=self._is_synthetic_user(user_id),
                ),
            )
        return ProgressView(user_id=user_id, concepts={})

    def get_session(self, user_id: str) -> SessionView:
        try:
            rec = self.recommend(user_id)
            active = rec.concept_id or rec.recommended_concept
        except RuntimeDegraded:
            active = None
        return SessionView(user_id=user_id, active_concept=active)

    def _normalize_policy(self, user_id: str, policy: Optional[str]) -> Optional[str]:
        """Validate ``policy`` and enforce the synthetic-only constitutional guard.

        Real users must always run on the canonical recommendation path. Only
        synthetic learners are allowed to request alternate baseline selectors
        because baselines deliberately ignore the JT-governed brain — this is
        a research isolation contract, not a feature for real users.
        """
        if policy is None:
            return None
        normalized = str(policy).strip().lower()
        if not normalized:
            return None
        if normalized not in self.SUPPORTED_POLICIES:
            raise RuntimeDegraded(
                "policy_not_supported",
                details={"policy": policy, "supported": list(self.SUPPORTED_POLICIES)},
            )
        if not self._is_synthetic_user(user_id):
            raise RuntimeDegraded(
                "policy_forbidden_for_real_user",
                details={"policy": normalized, "user_id": user_id},
            )
        return normalized

    def _get_concept_difficulty(self, concept_id: str) -> float:
        """Get concept difficulty from database or return default.

        The canonical concept catalog table is ``k12_concepts`` whose primary
        key column is ``id`` (not ``concept_id``). The original implementation
        targeted a non-existent ``concepts`` table which produced a "relation
        does not exist" error on every recommend call and drowned the API
        logs in noise that masked real failures.
        """
        try:
            result = self.postgres_store.execute_read(
                """
                SELECT difficulty FROM k12_concepts
                WHERE id = %s
                LIMIT 1
                """,
                (concept_id,),
                fetch_one=True,
            )
            if result and result.get("difficulty") is not None:
                return float(result["difficulty"])
        except Exception as exc:
            self.logger.debug(
                "concept_difficulty_lookup_failed",
                concept_id=concept_id,
                error=str(exc),
            )
        return 0.5  # Default difficulty

    # ── Archetype × Task covariate (observational only) ──────────────────
    # These helpers populate ``selection_metrics.archetype_covariate`` for
    # the instructor dashboard. They never feed back into the MAB score —
    # the design decision (Slice 5b) is to validate HCIE/JT under
    # archetype-uniform conditions first, then study archetype × concept
    # outcomes as a separate observational analysis. Folding archetype into
    # the score would contaminate the validation: a JT improvement could no
    # longer be attributed cleanly to the model.

    # Three taxonomies, fixed-vocabulary. Tags outside these are ignored so
    # the dashboard groupings stay tidy even if instructors author novel
    # tags by hand.
    _ARCHETYPE_AXES: Dict[str, Tuple[str, ...]] = {
        "vark": ("vark_visual", "vark_auditory", "vark_reading", "vark_kinesthetic"),
        "behav": (
            "behav_participant", "behav_passenger", "behav_partner",
            "behav_pathfinder", "behav_pirate", "behav_prisoner",
        ),
        "motiv": ("motiv_social", "motiv_solitary", "motiv_logical", "motiv_explorer"),
    }

    def _read_archetype_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Return the user's self-reported archetype profile, or ``None`` if
        the user has not completed onboarding yet.
        """
        try:
            row = self.postgres_store.execute_read(
                """
                SELECT vark_scores, behav_scores, motiv_scores, source, confidence
                FROM user_archetype_profile
                WHERE user_id = %s
                """,
                (str(user_id),),
                fetch_one=True,
            )
        except Exception as exc:
            self.logger.debug(
                "archetype_profile_read_failed", user_id=user_id, error=str(exc)
            )
            return None
        if not row:
            return None

        def _as_dict(value: Any) -> Dict[str, float]:
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    return {}
            if not isinstance(value, dict):
                return {}
            out: Dict[str, float] = {}
            for k, v in value.items():
                try:
                    out[str(k)] = float(v)
                except (TypeError, ValueError):
                    continue
            return out

        return {
            "vark": _as_dict(row.get("vark_scores")),
            "behav": _as_dict(row.get("behav_scores")),
            "motiv": _as_dict(row.get("motiv_scores")),
            "source": row.get("source") or "self_report",
            "confidence": float(row.get("confidence") or 0.5),
        }

    def _archetype_covariate(
        self,
        user_id: str,
        task_tags: List[str],
    ) -> Optional[Dict[str, Any]]:
        """Compute the observational archetype-intersection covariate.

        Returns ``None`` when either side is empty so the dashboard query
        can ``WHERE archetype_covariate IS NOT NULL`` cleanly.
        """
        if not task_tags:
            return None
        profile = self._read_archetype_profile(user_id)
        if not profile:
            # The dashboard still wants to know which tags the task carried
            # even when the learner has no profile yet (so we can compare
            # later once they onboard). Emit a partial payload.
            return {
                "task_tags": list(task_tags),
                "user_profile_present": False,
                "intersection_score": None,
                "per_axis_intersection": None,
            }

        # Per-axis intersection: dot product between the user's score vector
        # on that axis and a one-hot vector for whichever tags the task
        # carries on that axis. Tags outside an axis don't contribute to
        # that axis's score, which is the property we want.
        per_axis: Dict[str, float] = {}
        for axis, vocab in self._ARCHETYPE_AXES.items():
            scores = profile.get(axis) or {}
            # Strip the axis prefix when looking up scores: stored as
            # ``{"visual":0.7,...}`` but tags are ``vark_visual``.
            prefix = f"{axis}_"
            axis_intersection = 0.0
            for tag in task_tags:
                if not tag.startswith(prefix):
                    continue
                short = tag[len(prefix):]
                axis_intersection += float(scores.get(short, 0.0))
            per_axis[axis] = round(axis_intersection, 4)

        # Overall intersection score is the unweighted mean of the three
        # axis scores — keeps the value bounded in [0, 1] regardless of
        # how many tags the task carries.
        overall = round(sum(per_axis.values()) / len(per_axis), 4)

        return {
            "task_tags": list(task_tags),
            "user_profile_present": True,
            "user_profile_source": profile.get("source"),
            "user_profile_confidence": profile.get("confidence"),
            "intersection_score": overall,
            "per_axis_intersection": per_axis,
        }

    @staticmethod
    def _row_representation(row: Dict[str, Any]) -> str:
        """Canonical representation (modality) label for a task row. Mirrors the
        ``kind`` derivation used when serving the task, so the value recorded on an
        attempt, the bandit arm, and what the learner sees all agree."""
        task_type = row.get("task_type", "text")
        media_type = row.get("media_type")
        if not media_type:
            _content = row.get("content")
            if isinstance(_content, dict):
                media_type = _content.get("media_type")
        if task_type == "video_mcq" or media_type == "video":
            return "video_question"
        if task_type == "audio_mcq" or media_type == "audio":
            return "audio_listen"
        if task_type in {"multiple_choice", "mpq"}:
            return "mcq"
        return task_type or "text"

    def _representation_outcomes(
        self, user_id: str, concept_id: str, reps: List[str]
    ) -> Dict[str, Tuple[float, float]]:
        """Per-representation Beta(alpha, beta) success priors for this learner,
        read from the ``interactions`` table (which records representation + correct
        on every attempt). Prefers per-(concept, representation) history; falls back
        to the learner's global per-representation history when the concept has none.
        Returns {} on any error or no history → the caller leaves modality unbiased."""
        if not reps:
            return {}
        try:
            rows = self.postgres_store.execute_read(
                """
                SELECT representation,
                       SUM(CASE WHEN correct THEN 1 ELSE 0 END)::int AS c,
                       COUNT(*)::int AS n
                FROM interactions
                WHERE user_id = %s AND concept_id = %s
                  AND representation = ANY(%s) AND correct IS NOT NULL
                GROUP BY representation
                """,
                (user_id, concept_id, list(reps)),
            ) or []
            if not rows:
                rows = self.postgres_store.execute_read(
                    """
                    SELECT representation,
                           SUM(CASE WHEN correct THEN 1 ELSE 0 END)::int AS c,
                           COUNT(*)::int AS n
                    FROM interactions
                    WHERE user_id = %s AND representation = ANY(%s) AND correct IS NOT NULL
                    GROUP BY representation
                    """,
                    (user_id, list(reps)),
                ) or []
            params: Dict[str, Tuple[float, float]] = {}
            for r in rows:
                rep = r.get("representation")
                if not rep:
                    continue
                c = int(r.get("c") or 0)
                n = int(r.get("n") or 0)
                params[str(rep)] = (1.0 + c, 1.0 + max(0, n - c))
            return params
        except Exception as exc:  # never break recommend on a stats read
            self.logger.debug("representation_outcomes_read_failed", user_id=user_id, error=str(exc))
            return {}

    def _pick_task(
        self,
        user_id: str,
        concept_id: str,
        deterministic: Optional[DeterministicModeConfig],
        *,
        policy: Optional[str] = None,
        language: Optional[List[str]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        # Normalize the language filter. Default ``['en']`` preserves the
        # pre-Slice-5b behaviour for callers that haven't started passing the
        # parameter yet. We also accept ``None`` / empty as "any language".
        lang_filter: Optional[List[str]] = None
        if language:
            lang_filter = [
                str(l).strip().lower() for l in language if str(l).strip()
            ] or None

        if lang_filter:
            query = """
                SELECT id, concept_id, difficulty, task_type, content, solution, hints, metadata,
                       media_url, media_type, transcript,
                       language, archetype_tags
                FROM tasks
                WHERE concept_id = %s AND concept_type = 'k12'
                  AND language = ANY(%s)
                ORDER BY id ASC
                LIMIT 10
            """
            rows = self.postgres_store.execute_read(query, (concept_id, lang_filter))
        else:
            query = """
                SELECT id, concept_id, difficulty, task_type, content, solution, hints, metadata,
                       media_url, media_type, transcript,
                       language, archetype_tags
                FROM tasks
                WHERE concept_id = %s AND concept_type = 'k12'
                ORDER BY id ASC
                LIMIT 10
            """
            rows = self.postgres_store.execute_read(query, (concept_id,))

        # If the language filter wiped the catalog for this concept (e.g.
        # learner requested 'id' but no Indonesian sibling exists yet), retry
        # in language-agnostic mode rather than 503-ing the learner.
        if not rows and lang_filter:
            self.logger.info(
                "task_language_fallback",
                user_id=user_id,
                concept_id=concept_id,
                requested_languages=lang_filter,
            )
            rows = self.postgres_store.execute_read(
                """
                SELECT id, concept_id, difficulty, task_type, content, solution, hints, metadata,
                       media_url, media_type, transcript,
                       language, archetype_tags
                FROM tasks
                WHERE concept_id = %s AND concept_type = 'k12'
                ORDER BY id ASC
                LIMIT 10
                """,
                (concept_id,),
            )

        if not rows:
            raise RuntimeDegraded(
                "k12_task_not_found",
                details={"concept_id": concept_id},
            )

        # ── Representation (modality) bandit ──────────────────────────────────
        # If this concept offers more than one modality (text / video / mcq / …),
        # Thompson-sample the one that has worked best for THIS learner (from the
        # per-(concept, representation) success recorded in `interactions`) and
        # restrict the candidate pool to it. The task selector below then picks the
        # specific task within the chosen modality. Fully guarded: any failure
        # leaves the full pool and the prior behaviour untouched.
        representation_meta: Dict[str, Any] = {}
        try:
            avail_reps = sorted({self._row_representation(r) for r in rows})
            # Representation bandit is a LIVE real-learner feature ONLY. It must never
            # fire for synthetic / replay / experimental users, so it cannot influence
            # the sealed cross-model evaluation (those cohorts are generated via
            # cohort_runner, NOT this path; baseline AUC filters by sealed run_id; and
            # the MAB writes only `interactions`, which no sealed-metric script reads).
            # This guard makes the isolation a contract, not an empty-history accident.
            if len(avail_reps) > 1 and not self._is_synthetic_user(user_id):
                rep_params = self._representation_outcomes(user_id, concept_id, avail_reps)
                if rep_params:
                    chosen_rep = self.bandit.select_representation(
                        user_id, concept_id, avail_reps, representation_params=rep_params,
                    )
                    matched = [r for r in rows if self._row_representation(r) == chosen_rep]
                    if matched and len(matched) < len(rows):
                        rows = matched
                    representation_meta = {
                        "representation_selected": chosen_rep,
                        "representation_candidates": avail_reps,
                        "representation_arms": {
                            k: {"alpha": round(v[0], 2), "beta": round(v[1], 2)} for k, v in rep_params.items()
                        },
                    }
        except Exception as exc:
            self.logger.debug("representation_bandit_skipped", user_id=user_id, error=str(exc))

        selector = (policy or "default").lower()
        det_active = bool(deterministic and deterministic.deterministic)
        candidates_count = len(rows)
        policy_score: Optional[float] = None
        # Top-K candidate scores (selector evidence). For scored selectors we
        # capture the deterministic ranking; for unscored selectors (static /
        # random) we still emit task_id ordering so replay diffs can audit
        # candidate stability.
        candidate_arm_scores: List[Dict[str, Any]] = []

        if selector == "static":
            row = rows[0]
        elif selector == "random":
            if candidates_count <= 1:
                row = rows[0]
            elif det_active:
                idx = int(self.rng.get_noise_stream().randint(0, candidates_count))
                row = rows[idx]
            else:
                import random as _random
                row = _random.choice(rows)
        elif selector in {
            "hcie",
            "bandit",
            "thompson",
            "ucb",
            "epsilon_greedy",
            "mastery_greedy",
            "zpd_aligned",
            "uncertainty_reduction",
        }:
            scored = self._score_policy_candidates(user_id, concept_id, rows, selector)
            row = scored[0][1]
            policy_score = float(scored[0][0])
            for rank, (score, candidate_row) in enumerate(scored[:5], start=1):
                candidate_arm_scores.append(
                    {
                        "rank": rank,
                        "task_id": candidate_row.get("id"),
                        "score": float(score),
                        "difficulty": (
                            float(candidate_row["difficulty"])
                            if candidate_row.get("difficulty") is not None
                            else None
                        ),
                    }
                )
        else:
            if det_active:
                if candidates_count <= 1:
                    row = rows[0]
                else:
                    idx = int(self.rng.get_bandit_stream().randint(0, candidates_count - 1))
                    row = rows[idx]
            else:
                import random as _random
                row = _random.choice(rows)

        # For non-scoring selectors, surface the candidate-id ordering so the
        # cohort writer / replay harness can still audit candidate stability.
        if not candidate_arm_scores:
            for rank, candidate_row in enumerate(rows[:5], start=1):
                candidate_arm_scores.append(
                    {
                        "rank": rank,
                        "task_id": candidate_row.get("id"),
                        "score": None,
                        "difficulty": (
                            float(candidate_row["difficulty"])
                            if candidate_row.get("difficulty") is not None
                            else None
                        ),
                    }
                )

        content = row.get("content") or {}
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                content = {"question": content}
        if not isinstance(content, dict):
            content = {}

        media_url = row.get("media_url") or content.get("media_url")
        media_type = row.get("media_type") or content.get("media_type")
        transcript = row.get("transcript") or content.get("transcript")
        task_type = row.get("task_type", "text")
        kind = self._row_representation(row)

        task_payload = {
            "task_id": row["id"],
            "id": row["id"],
            "concept_id": row["concept_id"],
            "difficulty": row.get("difficulty"),
            "task_type": task_type,
            "representation": kind,
            "kind": kind,
            "content": {
                **content,
                "id": row["id"],
                "conceptId": row["concept_id"],
                "kind": kind,
                "difficulty": row.get("difficulty"),
                "mediaUrl": media_url,
                "media_url": media_url,
                "mediaType": media_type,
                "media_type": media_type,
                "transcript": transcript,
            },
            "media_url": media_url,
            "media_type": media_type,
            "transcript": transcript,
            "question_text": content.get("question") or content.get("question_text", ""),
            "choices": content.get("choices", []),
            "correct_answer": self._extract_correct(row),
        }
        # Surface the chosen row's language + archetype_tags so the recommend
        # orchestrator can attach the observational covariate to
        # ``selection_metrics`` without doing a second DB hop.
        chosen_tags = row.get("archetype_tags") or []
        if isinstance(chosen_tags, str):
            try:
                chosen_tags = json.loads(chosen_tags)
            except json.JSONDecodeError:
                chosen_tags = []
        pick_meta = {
            "policy_selector": selector if selector in self.SUPPORTED_POLICIES else "default",
            "policy_score": policy_score,
            "candidates_count": candidates_count,
            "candidate_arm_scores": candidate_arm_scores,
            "selected_task_id": row.get("id"),
            "language": row.get("language") or "en",
            "archetype_tags": list(chosen_tags) if isinstance(chosen_tags, list) else [],
            **representation_meta,
        }
        return task_payload, pick_meta

    def _score_policy_candidates(
        self,
        user_id: str,
        concept_id: str,
        rows: List[Dict[str, Any]],
        selector: str,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """Score candidate tasks for synthetic research-policy ecology.

        These selectors are deliberately synthetic-only (enforced in
        ``_normalize_policy``). They give FINAL the same broad policy ecology
        used by the old V2 Contribution C harness while staying inside the
        shipped live stack: every score is computed from the task catalog,
        the learner's current posterior, and deterministic RNG streams.
        """
        mastery, uncertainty = self._read_posterior(user_id, concept_id)
        scored: List[Tuple[float, Dict[str, Any]]] = []
        alpha = 1.0 + mastery * max(0.1, 1.0 - uncertainty)
        beta_param = 1.0 + (1.0 - mastery) * max(0.1, 1.0 - uncertainty)
        bandit_rng = self.rng.get_bandit_stream() if self.rng is not None else None
        noise_rng = self.rng.get_noise_stream() if self.rng is not None else None
        hcie_target = min(0.95, mastery + 0.12 * uncertainty + 0.06)
        ucb_target = min(0.95, mastery + 0.22)
        eps_target = min(0.95, mastery + 0.05)
        for row in rows:
            difficulty = float(row.get("difficulty") or 0.5)
            task_id = str(row.get("id") or "")
            zpd_distance = abs(mastery - difficulty)
            zpd_bonus = math.exp(-(zpd_distance ** 2) / 0.1)
            tiebreak = self._policy_tiebreak(selector, task_id)

            if selector in {"hcie", "bandit"}:
                # Governance blend: stay in ZPD but lean slightly above mastery when uncertain.
                stretch = math.exp(-((difficulty - hcie_target) ** 2) / 0.07)
                score = (
                    0.55 * zpd_bonus
                    + 0.30 * stretch
                    + 0.10 * uncertainty
                    + 0.05 * max(0.0, 1.0 - mastery)
                )
            elif selector == "zpd_aligned":
                # Pure ZPD proximity — intentionally not identical to HCIE stretch target.
                score = -zpd_distance + tiebreak * 1e-6
            elif selector == "mastery_greedy":
                score = (1.0 - difficulty) + 0.20 * math.exp(
                    -((difficulty - max(0.08, mastery - 0.10)) ** 2) / 0.05
                )
            elif selector == "uncertainty_reduction":
                # Seek tasks that split mastery belief (away from posterior and from 0.5 anchor).
                info_gain = uncertainty * (abs(difficulty - mastery) + 0.35 * abs(difficulty - 0.5))
                score = info_gain + 0.15 * difficulty
            elif selector == "ucb":
                exploitation = math.exp(-((difficulty - ucb_target) ** 2) / 0.06)
                exploration_bonus = uncertainty * math.sqrt(2.0 + difficulty)
                score = exploitation + 0.55 * exploration_bonus
            elif selector == "epsilon_greedy":
                # Keep exploration off the uniform random manifold: explore only inside
                # a ZPD band around eps_target so ε-greedy does not collapse to random.
                epsilon = 0.18
                band = math.exp(-((difficulty - eps_target) ** 2) / 0.10)
                explore = bool(noise_rng is not None and noise_rng.rand() < epsilon)
                if explore and noise_rng is not None:
                    score = float(noise_rng.rand()) * band + 0.05 * band
                else:
                    score = math.exp(-((difficulty - eps_target) ** 2) / 0.05) + 0.08 * band
            elif selector == "thompson":
                # Exploitative Thompson: per-arm Beta with difficulty-shaped priors.
                arm_alpha = alpha + difficulty * 2.5
                arm_beta = beta_param + (1.0 - difficulty) * 2.5
                sample = (
                    float(bandit_rng.beta(arm_alpha, arm_beta))
                    if bandit_rng is not None
                    else mastery
                )
                exploit = math.exp(-((difficulty - mastery) ** 2) / 0.09)
                score = 0.82 * sample * exploit + 0.18 * exploit
            else:
                score = math.exp(-((difficulty - mastery) ** 2) / 0.08)
            scored.append((score, row))
        scored.sort(
            key=lambda pair: (
                -pair[0],
                self._policy_tiebreak(selector, str(pair[1].get("id") or "")),
            )
        )
        return scored

    @staticmethod
    def _policy_tiebreak(selector: str, task_id: str) -> float:
        """Deterministic tie-break so policies diverge even on near-tied scores."""
        import hashlib

        digest = hashlib.sha256(f"{selector}:{task_id}".encode("utf-8")).hexdigest()
        return int(digest[:8], 16) / float(0xFFFFFFFF)

    def _read_posterior(self, user_id: str, concept_id: str) -> Tuple[float, float]:
        """Return ``(mastery, uncertainty)`` from learning_state with safe defaults."""
        try:
            row = self.postgres_store.execute_read(
                """
                SELECT state_data
                FROM learning_state
                WHERE user_id::text = %s AND concept = %s
                ORDER BY updated_at DESC NULLS LAST
                LIMIT 1
                """,
                (str(user_id), concept_id),
                fetch_one=True,
            )
        except Exception:
            row = None
        if not row:
            return 0.3, 0.5
        state = row.get("state_data") or {}
        if isinstance(state, str):
            try:
                state = json.loads(state)
            except json.JSONDecodeError:
                state = {}
        if not isinstance(state, dict):
            state = {}
        mastery_raw = (
            state.get("mastery")
            or state.get("lyapunov_mastery")
            or state.get("kalman_mastery")
        )
        uncertainty_raw = state.get("uncertainty")
        try:
            mastery = float(mastery_raw) if mastery_raw is not None else 0.3
        except (TypeError, ValueError):
            mastery = 0.3
        try:
            uncertainty = float(uncertainty_raw) if uncertainty_raw is not None else 0.5
        except (TypeError, ValueError):
            uncertainty = 0.5
        return mastery, uncertainty

    def _cold_start_view(self, user_id: str, concept_id: str) -> Dict[str, Any]:
        """Return cold-start guidance when the user has no prior interactions on this concept.

        Uses ``ColdStartOptimizer`` for a personalized initial mastery estimate (avoids the
        constitutional synthetic-mastery ban — §7 — by labelling it as ``policy_type='cold_start_its'``
        and exposing the cohort + signal explicitly, not as posterior mastery).
        """
        try:
            # `cognition_updates` was a Phase-1 bootstrap table that no longer
            # exists.  The canonical interaction record is `experiment_trajectories`
            # (written by trajectory_recorder_consumer after every attempt).
            # Fallback: `learning_state` row existence means ≥1 interaction.
            row = self.postgres_store.execute_read(
                "SELECT COUNT(*) AS c FROM experiment_trajectories WHERE user_id = %s",
                (user_id,),
            )
            interactions = int(row[0]["c"]) if row else 0
            if interactions == 0:
                # Fast path: learning_state upserted on every write
                ls = self.postgres_store.execute_read(
                    "SELECT 1 FROM learning_state WHERE user_id = %s LIMIT 1",
                    (user_id,),
                )
                if ls:
                    interactions = 1
        except Exception:
            interactions = 0

        if interactions > 0:
            return {"active": False, "interactions_observed": interactions}

        try:
            from core.mastery.cold_start_optimizer import ColdStartOptimizer

            initial = ColdStartOptimizer.get_personalized_mastery(user_id, concept_id)
            cohort = ColdStartOptimizer.get_user_cohort(user_id)
        except Exception as exc:
            return {
                "active": True,
                "reason": "cold_start_optimizer_unavailable",
                "error": str(exc),
            }

        return {
            "active": True,
            "interactions_observed": 0,
            "initial_mastery_estimate": initial,
            "cohort": cohort,
            "source": "ColdStartOptimizer",
            "note": "non-authoritative pedagogical signal; canonical mastery only set after first attempt",
        }

    def _governance_view(self, user_id: str, concept_id: str) -> Dict[str, Any]:
        """Pull the 6D governance snapshot (``J_t``, components, w1..w6) for this user / concept.

        The values are read-only; this never mutates governance state.
        """
        brain = getattr(self.spine, "unified_brain", None)
        if brain is None:
            return {"available": False, "reason": "no_brain"}

        snapshot: Dict[str, Any] = {"schema_version": "6D.1.0"}

        weights_obj = getattr(brain, "constitutional_weights", None)
        if weights_obj is not None and getattr(weights_obj, "weights", None):
            try:
                snapshot["weights"] = dict(weights_obj.weights)
                snapshot["adaptation_count"] = getattr(weights_obj, "adaptation_count", 0)
            except Exception:
                pass

        jt = getattr(brain, "jt_governance", None) or getattr(brain, "constitutional_jt_governance", None)
        if jt is not None:
            for attr in ("get_state_snapshot", "snapshot", "get_state"):
                fn = getattr(jt, attr, None)
                if callable(fn):
                    try:
                        state = fn(user_id) if "user" in fn.__code__.co_varnames else fn()
                        if isinstance(state, dict):
                            snapshot["jt_state"] = state
                            break
                    except Exception:
                        continue

        history = getattr(brain, "jt_history", None)
        if isinstance(history, dict) and user_id in history:
            try:
                latest = history[user_id][-1] if history[user_id] else None
                if isinstance(latest, dict):
                    snapshot["latest_jt"] = latest
            except Exception:
                pass

        if "weights" not in snapshot and "latest_jt" not in snapshot and "jt_state" not in snapshot:
            return {"available": False, "reason": "no_governance_state_yet"}

        snapshot["available"] = True
        return snapshot

    @staticmethod
    def _extract_correct(task_row: Dict[str, Any]) -> str:
        content = task_row.get("content") or {}
        if isinstance(content, dict):
            return str(content.get("correct_answer", ""))
        solution = task_row.get("solution") or {}
        if isinstance(solution, dict):
            return str(solution.get("correct_answer", solution.get("explanation", "")))
        return ""
