"""
Unified Learning Brain - Single function that defines ALL learning logic

This replaces the scattered approach with ONE canonical function that:
- READ mode: inference only (for API calls)
- WRITE mode: full update (for consumer)
- SIMULATION mode: for experiments and validation

Everything calls THIS ONE function - no more scattered logic!

🔥 BRAIN GOVERNANCE:
- JT (Objective Function) is the TOP-LEVEL CONTROL SIGNAL
- All adaptive behavior ultimately serves to maximize JT
- CONTROL variables: η, exploration, policy, ensemble weights
- STATE variables: mastery, uncertainty, ZPD, transfer (inform CONTROL)
- OBSERVE variables: metrics, regret, traces (dashboard/research only)
- PHASE 5 JT-AWARE POLICY: Policy selection maximizes expected future ΔJT
  - Old: STATE → POLICY (heuristic selection)
  - New: expected future ΔJT → POLICY (constitutional optimization)
  - Policies become governance instruments, not teaching styles
  - This makes policy temporally self-consistent with bandit/ensemble/η
- PHASE 6 CONSTITUTIONAL PURIFICATION: Remove hidden motivational priors
  - Old: policy_multiplier = hardcoded priors (hcie=1.12, heuristic=1.05, static=1.0, random=0.97)
  - New: policy_multiplier = expected_JT (learned from governance history)
  - Removes embedded pedagogical ideology and makes policy purely JT-driven
  - All subsystems now serve JT, not independent objectives

See BRAIN_GOVERNANCE.md for the complete governance architecture
"""

import math
import os
import random
import time
import uuid
import json
import hashlib
import logging
import threading
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from dataclasses import dataclass, asdict
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Individualized cold-start prior (Yudelson, Koedinger & Gordon 2013).
#
# The PopulationPrior (per-concept Beta-Binomial base rate) lives in
# jt_v2_signals.py. It was previously audit-only on the V2 branch. We wire it
# onto the V1 hot path so cold-start (learner, concept) seeds the Bayesian
# learner's Beta prior from the concept's population posterior instead of a
# flat generic prior — the change validated in
# research_validation/reports/COLDSTART_BEAT_BKT_2026-06-05.md (config
# "HCIE BKT+prior-init" / "EB-Beta(prior)", prior strength=5).
#
# The module uses numbered directory prefixes that are illegal Python package
# names, so PopulationPriorState is loaded from its file path (same mechanism
# the V2 signals block at the bottom of this module already uses). The loaded
# class is cached at module scope so every brain instance shares one class
# object (state itself is per-brain-instance, see UnifiedLearningBrain).
COLDSTART_PRIOR_STRENGTH = 5.0  # Beta pseudo-count strength for the individualized prior
COLDSTART_MIN_POP_OBS = 8       # min per-concept observations before using the population prior
_GENERIC_PRIOR_ALPHA = 3.0      # legacy generic fallback (mean 0.30)
_GENERIC_PRIOR_BETA = 7.0
_COLDSTART_GENERIC_ALPHA = 1.5  # legacy cold-start canonical seed (mean 0.30)
_COLDSTART_GENERIC_BETA = 3.5

_POPULATION_PRIOR_CLASS = None  # cached PopulationPriorState class object


def _load_population_prior_class():
    """Load PopulationPriorState from jt_v2_signals.py (numbered-dir safe)."""
    global _POPULATION_PRIOR_CLASS
    if _POPULATION_PRIOR_CLASS is not None:
        return _POPULATION_PRIOR_CLASS
    try:
        import importlib.util as _il
        import sys as _sys
        from pathlib import Path as _Path

        _v2_mod = _sys.modules.get("jt_v2_signals")
        if _v2_mod is None:
            _v2_path = _Path(__file__).resolve().parent / "jt_v2_signals.py"
            if not _v2_path.is_file():
                return None
            _spec = _il.spec_from_file_location("jt_v2_signals", _v2_path)
            _v2_mod = _il.module_from_spec(_spec)
            # dataclass introspection needs the module registered before exec.
            _sys.modules["jt_v2_signals"] = _v2_mod
            _spec.loader.exec_module(_v2_mod)  # type: ignore[union-attr]
        _POPULATION_PRIOR_CLASS = getattr(_v2_mod, "PopulationPriorState", None)
    except Exception as _e:  # pragma: no cover - defensive
        logger.warning(f"⚠️ Could not load PopulationPriorState for cold-start prior: {_e}")
        _POPULATION_PRIOR_CLASS = None
    return _POPULATION_PRIOR_CLASS


@dataclass(frozen=True)
class CapabilityRecord:
    name: str
    dotted_path: str
    required: bool
    available: bool
    status: str
    error: Optional[str] = None


@dataclass(frozen=True)
class CapabilityManifest:
    """Boot-time cognitive engine topology.

    The fingerprint intentionally excludes `boot_time`: it identifies the
    loaded topology, not the timestamp of this process.
    """

    schema_version: str
    boot_time: str
    environment: str
    engines: Dict[str, Dict[str, Any]]
    fingerprint: str

    @classmethod
    def build(
        cls,
        *,
        environment: str,
        import_records: Dict[str, CapabilityRecord],
        runtime_records: Dict[str, CapabilityRecord],
    ) -> "CapabilityManifest":
        engines = {
            name: asdict(record)
            for name, record in sorted({**import_records, **runtime_records}.items())
        }
        fingerprint_payload = {
            "schema_version": "capability-manifest.v1",
            "environment": environment,
            "engines": engines,
        }
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return cls(
            schema_version="capability-manifest.v1",
            boot_time=datetime.utcnow().isoformat(),
            environment=environment,
            engines=engines,
            fingerprint=fingerprint,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


_LATEST_CAPABILITY_MANIFEST: Optional[CapabilityManifest] = None
_CAPABILITY_MISSING_COUNTER = None


def get_latest_capability_manifest() -> Optional[Dict[str, Any]]:
    return _LATEST_CAPABILITY_MANIFEST.to_dict() if _LATEST_CAPABILITY_MANIFEST else None


def _increment_capability_missing(name: str, required: bool) -> None:
    global _CAPABILITY_MISSING_COUNTER
    try:
        if _CAPABILITY_MISSING_COUNTER is None:
            from prometheus_client import Counter

            _CAPABILITY_MISSING_COUNTER = Counter(
                "hcie_capability_missing_total",
                "Missing optional/required cognitive capabilities at brain boot.",
                ["capability", "required"],
            )
        _CAPABILITY_MISSING_COUNTER.labels(
            capability=name,
            required=str(required).lower(),
        ).inc()
    except Exception:
        # Metrics must not become a second hidden boot dependency.
        return

# Phase 14e: split brain imports so a single missing module (e.g.
# `learning_loop_engine_v2`, quarantined in Phase 14c) does not cascade and
# leave the rest of the symbols undefined — that was the root cause of the
# `LearnerType` / `LearnerState` / `LearningMetricsAggregator` NameErrors
# that broke V3 auth and the user repository.

_REQUIRED_BRAIN_IMPORTS = {
    "LearnerFactory",
    "ContextualBandit",
    "TransferLearningEngine",
    "LearningMetricsAggregator",
    "interaction_is_correct",
    "normalize_interaction_for_brain",
}
_BRAIN_IMPORT_RECORDS: Dict[str, CapabilityRecord] = {}


def _safe_import(symbol_name: str, dotted: str, attr: str = None):
    """Import ``dotted.attr`` (or ``dotted``) and bind it as ``symbol_name`` in
    module globals; on failure, leave it undefined and log once.
    """
    dotted_path = f"{dotted}.{attr}" if attr else dotted
    required = symbol_name in _REQUIRED_BRAIN_IMPORTS
    try:
        from importlib import import_module

        mod = import_module(dotted)
        value = getattr(mod, attr) if attr else mod
        globals()[symbol_name] = value
        _BRAIN_IMPORT_RECORDS[symbol_name] = CapabilityRecord(
            name=symbol_name,
            dotted_path=dotted_path,
            required=required,
            available=True,
            status="loaded",
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.debug("brain import skipped: %s (%s.%s): %s", symbol_name, dotted, attr or "*", exc)
        _BRAIN_IMPORT_RECORDS[symbol_name] = CapabilityRecord(
            name=symbol_name,
            dotted_path=dotted_path,
            required=required,
            available=False,
            status="missing",
            error=str(exc),
        )
        return False


_brain_import_ok = True
for _symbol, _dotted, _attr in (
    ("LearnerFactory", "core.learning.learner_factory", "LearnerFactory"),
    ("ContextualBandit", "core.bandit.bandit", "ContextualBandit"),
    ("TransferLearningEngine", "core.learning.transfer_learning_engine", "TransferLearningEngine"),
    ("research_logger", "core.learning.research_logger", "research_logger"),
    ("MathematicalLogEntry", "core.learning.research_logger", "MathematicalLogEntry"),
    ("ResearchLogger", "core.learning.research_logger", "ResearchLogger"),
    ("AdaptiveTransferEngine", "core.learning.adaptive_transfer_engine", "AdaptiveTransferEngine"),
    ("RealDAGDependencies", "core.learning.real_dag_dependencies", "RealDAGDependencies"),
    ("ConfidenceWeightedLearner", "core.learning.confidence_weighted_learner", "ConfidenceWeightedLearner"),
    ("LearningMetricsAggregator", "core.learning.learning_metrics", "LearningMetricsAggregator"),
    ("LearnerState", "core.learning.learner_state_protocol", "LearnerState"),
    ("LearnerType", "core.learning.learner_state_protocol", "LearnerType"),
    ("LyapunovState", "core.learning.learner_state_protocol", "LyapunovState"),
    ("BayesianState", "core.learning.learner_state_protocol", "BayesianState"),
    ("KalmanState", "core.learning.learner_state_protocol", "KalmanState"),
    ("interaction_is_correct", "core.state.interaction_keys", "interaction_is_correct"),
    ("normalize_interaction_for_brain", "core.state.interaction_keys", "normalize_interaction_for_brain"),
):
    if not _safe_import(_symbol, _dotted, _attr):
        _brain_import_ok = False

_missing_required_imports = [
    record for record in _BRAIN_IMPORT_RECORDS.values()
    if record.required and not record.available
]
if _missing_required_imports:
    raise RuntimeError(
        "UnifiedLearningBrain required capability imports failed: "
        + ", ".join(f"{record.name} ({record.error})" for record in _missing_required_imports)
    )

# Phase 14e final safety net: if any brain symbol is still unbound after the
# per-import loop above (e.g. an entirely missing module on a dev box), give
# it a typed stub so class-body annotations don't raise NameError.
from enum import Enum as _FallbackEnum
from dataclasses import dataclass as _fallback_dataclass

if "LearnerType" not in globals():
    class LearnerType(_FallbackEnum):  # type: ignore[no-redef]
        LYAPUNOV = "lyapunov"
        BAYESIAN = "bayesian"
        KALMAN = "kalman"

if "LearnerState" not in globals():
    @_fallback_dataclass
    class LearnerState:  # type: ignore[no-redef]
        learner_type: str = "unknown"
        mastery: float = 0.0

for _stub in ("LyapunovState", "BayesianState", "KalmanState"):
    if _stub not in globals():
        @_fallback_dataclass
        class _StubState(LearnerState):  # type: ignore[no-redef]
            pass
        globals()[_stub] = _StubState

if "LearningMetricsAggregator" not in globals():
    class LearningMetricsAggregator:  # type: ignore[no-redef]
        def __init__(self, *_a, **_kw): pass
        def record(self, *_a, **_kw): pass
        def snapshot(self): return {}

if "ContextualBandit" not in globals():
    class ContextualBandit:  # type: ignore[no-redef]
        def __init__(self, *_a, **_kw): pass

if "LearnerFactory" not in globals():
    class LearnerFactory:  # type: ignore[no-redef]
        def __init__(self, *_a, **_kw): pass
        def create_learners(self, *_a, **_kw): return {}

if "LearningLoopEngineV2" not in globals():
    class LearningLoopEngineV2:  # type: ignore[no-redef]
        """No-op stand-in for the quarantined Phase 14c learning loop engine."""

        def __init__(self, *_a, **_kw): pass

        def step(self, *_a, **_kw):
            return {"status": "noop", "reason": "LearningLoopEngineV2 quarantined Phase 14c"}


# ============================================================================
# COMPOSED GOVERNANCE CLASSES (Internal decomposition for clarity)
# ============================================================================

# --- governance cluster extracted to governance_engine.py (Stage 1 split) ---
from .governance_engine import (
    ConstitutionalWeights,
    VolatilityMonitor,
    StabilityMonitor,
    AttributionEngine,
    ConstitutionalJTGovernance,
)
# --- ensemble fusion extracted to ensemble_fusion.py (Stage 2 split) ---
from .ensemble_fusion import JTAttributedEnsemble
# --- V2-causal inverse-variance fusion (HCIE_REDESIGN_V2_CAUSAL; off => V1/sealed untouched) ---
from .learner_fusion import LearnerFusion, beta_variance, v2_causal_fusion_enabled
_LEARNER_FUSION = LearnerFusion()  # stateless; safe module-level singleton
# --- state types extracted to brain_state.py (Stage 3 split) ---
from .brain_state import (
    LearningResult,
    REQUIRED_FIELDS,
    build_learning_result,
    InMemoryState,
    MultiConceptWorkingState,
    InMemoryLearningStateRepository,
)
class UnifiedLearningBrain:
    """
    Unified Learning Brain - Single source of truth for all learning operations
    
    This class combines multiple learning algorithms into a single, coherent
    learning system that maintains consistency across all components.
    """
    
    # SHARED CANONICAL STORE: Accessible by StateAdapter to eliminate cold starts
    _shared_canonical_store = None
    
    # 🔥 CRITICAL: Track canonical state misses (should always be 0)
    _canonical_state_misses = 0
    _canonical_state_reads = 0
    
    # 🔥 OBSERVABILITY: Prometheus middleware reference for metrics
    _prometheus_middleware = None
    
    @classmethod
    def set_prometheus_middleware(cls, middleware):
        """Set Prometheus middleware for metrics tracking"""
        cls._prometheus_middleware = middleware
    
    @classmethod
    def update_canonical_state_metrics(cls):
        """Update canonical state metrics in Prometheus"""
        if cls._prometheus_middleware:
            total_reads = cls._canonical_state_reads
            total_misses = cls._canonical_state_misses
            
            # Update counters
            cls._prometheus_middleware.increment_canonical_state_reads()
            cls._prometheus_middleware.increment_canonical_state_misses()
            
            # Calculate and update miss rate
            miss_rate = total_misses / total_reads if total_reads > 0 else 0.0
            cls._prometheus_middleware.update_canonical_state_miss_rate(miss_rate)
    
    ALLOWED_ENVIRONMENTS = ("production", "research")

    def __init__(self, event_bus=None, outbox=None, environment="production", policy_config=None, experiment_context=False, deterministic_config=None, trajectory_recorder=None, redis_store=None, postgres_store=None, learning_state_repo=None, trace_repo=None, personalizer=None):
        """
        Initialize the UnifiedLearningBrain with all advanced layers

        Args:
            event_bus: Event bus for publishing learning events (fallback)
            outbox: Outbox pattern for atomic event publishing (production)
            environment: "production" or "research" — see ``ALLOWED_ENVIRONMENTS``.
                Slice 0a removes "staging" as an allowed value (no fake-staging
                topology); the runtime fails fast if anything else is passed.
            policy_config: PolicyConfiguration object for experiment policy overrides (optional, non-breaking)
            experiment_context: Whether this is an experiment context (policy config only applied if True)
            deterministic_config: DeterministicModeConfig for replay-safe deterministic mode (optional, opt-in)
            trajectory_recorder: TrajectoryRecorder for automatic trajectory capture (optional, first-class infrastructure)
            redis_store: cache/state store injected by application DI
            postgres_store: SQL/interaction store injected by application DI
            learning_state_repo: canonical state repository injected by application DI
            trace_repo: optional trace repository injected by application DI
            personalizer: optional personalized cold-start provider injected by application DI

        Note (Slice 0a / Phase 14g): the legacy ``system_mode`` parameter
        ("reward" / "jt" / "hybrid") was removed. Only the constitutional JT
        objective is canonical in FINAL; the parameter was assigned but never
        read. Removing it eliminates a semantic-lie surface.
        """
        self.event_bus = event_bus  # 🔥 FALLBACK: Direct event bus (dev mode)
        self.outbox = outbox  # 🔥 PRODUCTION: Outbox pattern for atomic publishing
        self.environment = environment  # 🔥 BULLETPROOF: Environment mode
        self.policy_config = policy_config  # 🔥 POLICY: Configuration for policy overrides (optional)
        self.experiment_context = experiment_context  # 🔥 SAFETY: Policy config only applied in experiment context
        self.trajectory_recorder = trajectory_recorder  # 🔥 TRAJECTORY: Automatic trajectory capture
        self.redis_store = redis_store
        self.db_store = postgres_store
        self._learning_state_repo = learning_state_repo
        self._trace_repo = trace_repo
        self.personalizer = personalizer
        self.capability_manifest: Optional[CapabilityManifest] = None

        # 🔥 TOPOLOGY CONTRACT: Ensure bandit attribute always exists (even if None)
        # This prevents AttributeError when experiments check self.unified_brain.bandit
        self.bandit = None

        # 🔥 DETERMINISTIC MODE: Opt-in replay-safe deterministic runtime
        self.deterministic_config = deterministic_config
        self.deterministic = deterministic_config.deterministic if deterministic_config else False
        
        if self.deterministic:
            self._init_deterministic_mode(deterministic_config)
            logger.info(f"🔥 Deterministic mode enabled (seed={deterministic_config.seed})")
            
            # 🔥 DETERMINISTIC RUNTIME: Set global deterministic context for automatic event metadata propagation
            try:
                from core.determinism.deterministic_config import set_global_deterministic_config
                set_global_deterministic_config(deterministic_config)
                logger.info("🔥 Global deterministic context set for automatic event metadata propagation")
            except ImportError:
                logger.warning("⚠️ Failed to set global deterministic context - deterministic event metadata may not propagate automatically")
        else:
            self.uuid_gen = None
            self.time_provider = None
            self.rng_manager = None
        
        # 🔥 CRITICAL: Initialize production infrastructure (ALWAYS, not just deterministic mode)
        # This ensures UnifiedBrain always has _learning_state_repo for governance-state persistence
        self._init_production_infrastructure()
        self._emit_capability_manifest()

        # ── Individualized cold-start prior (Yudelson 2013) ──────────────
        # One PopulationPriorState per brain instance. The LIVE API runs a
        # single long-lived brain, so this accumulates per-concept base rates
        # GLOBALLY across every interaction and every traffic class (live::,
        # synthetic, dataset replay) — it is updated unconditionally in
        # process_event below, independent of the HCIE_REDESIGN_V2 flag.
        #
        # Replay determinism: replay/seal engines construct a FRESH brain per
        # run (replay_engine_service.py, routes/replay.py, experiment_runner_
        # service.py), so the instance-scoped prior starts empty per replay
        # run and accumulates deterministically in event order — no
        # cross-run leakage. The live process keeps one growing prior.
        self._population_prior = None
        self._coldstart_prior_enabled = (
            os.environ.get("HCIE_COLDSTART_PRIOR", "1").strip().lower()
            not in ("0", "false", "no")
        )
        if self._coldstart_prior_enabled:
            try:
                _pp_cls = _load_population_prior_class()
                if _pp_cls is not None:
                    self._population_prior = _pp_cls(prior_alpha=1.0, prior_beta=1.0)
                    self._warm_up_population_prior()
            except Exception as _e:  # pragma: no cover - defensive
                logger.warning(f"⚠️ Cold-start population prior init failed: {_e}")
                self._population_prior = None

    def _warm_up_population_prior(self) -> None:
        """Seed the population prior from the sealed cohort snapshot if present.

        Gives the live system an immediate grounded per-concept prior (matching
        the validated offline result) for the concepts seen in the sealed run.
        Concepts NOT in the snapshot (e.g. synthetic k12_* concepts) simply
        accumulate online from live interactions. Best-effort: a missing or
        unreadable snapshot leaves the prior empty (it still accumulates
        online). Warm-up does not affect replay determinism because replay
        engines reset the per-instance prior by constructing a fresh brain and
        the snapshot is a fixed, content-addressed artifact.
        """
        if self._population_prior is None:
            return
        try:
            from pathlib import Path as _Path

            # The snapshot is mounted read-only into the API/consumer images at
            # /app/research_validation/reports/grounding/. Resolve relative to a
            # couple of known roots so this works in-container and in tests.
            candidates = [
                _Path("/app/research_validation/reports/grounding/tier2_5_population_prior_snapshot.json"),
                _Path(__file__).resolve().parents[4]
                / "research_validation" / "reports" / "grounding"
                / "tier2_5_population_prior_snapshot.json",
            ]
            snap_path = next((p for p in candidates if p.is_file()), None)
            if snap_path is None:
                logger.info("🔥 COLD-START PRIOR: no cohort snapshot found; prior will accumulate online")
                return
            payload = json.loads(snap_path.read_text(encoding="utf-8"))
            snapshot = payload.get("snapshot", {})
            cohort_stats = {}
            for concept, st in snapshot.items():
                if concept == "__global__":
                    continue
                a = float(st.get("alpha", 1.0))
                b = float(st.get("beta", 1.0))
                n = int(st.get("n", 0))
                # warm_up expects (correct, attempts); recover from Beta counts
                # seeded with prior_alpha=prior_beta=1.0 (so correct = alpha-1).
                correct = max(0, int(round(a - 1.0)))
                attempts = max(correct, n if n > 0 else int(round(a + b - 2.0)))
                if attempts > 0:
                    cohort_stats[str(concept)] = (correct, attempts)
            if cohort_stats:
                self._population_prior.warm_up(cohort_stats)
                logger.info(
                    f"🔥 COLD-START PRIOR: warmed up {len(cohort_stats)} concepts "
                    f"from {snap_path.name} (global_hit_rate={payload.get('global_hit_rate')})"
                )
        except Exception as _e:  # pragma: no cover - defensive
            logger.warning(f"⚠️ COLD-START PRIOR warm-up failed (continuing online-only): {_e}")

    def _individualized_cold_start_prior(self, concept: str) -> Tuple[float, float, Optional[float], int]:
        """Return (alpha, beta, pop_mean, n_obs) for a cold-start Bayesian seed.

        Yudelson (2013) individualized prior: seed the per-concept Beta from the
        concept's population posterior mean when there is enough evidence
        (>= COLDSTART_MIN_POP_OBS observations); otherwise fall back to the
        legacy generic cold-start prior. pop_mean is the population prior value
        actually consulted (recorded for audit); it is None when the prior was
        unavailable.
        """
        pp = getattr(self, "_population_prior", None)
        # Single source of truth per mode: when HCIE_REDESIGN_V2 is on, the V2
        # block is the writer, so read the cold-start prior from its singleton.
        try:
            if os.environ.get("HCIE_REDESIGN_V2", "").strip().lower() in ("1", "true", "yes"):
                _pp_cls = _load_population_prior_class()  # ensures jt_v2_signals loaded
                import sys as _sys
                _v2_mod = _sys.modules.get("jt_v2_signals")
                if _v2_mod is not None and hasattr(_v2_mod, "get_population_prior"):
                    pp = _v2_mod.get_population_prior()
        except Exception:
            pass
        if pp is None:
            return (_COLDSTART_GENERIC_ALPHA, _COLDSTART_GENERIC_BETA, None, 0)
        try:
            n_obs = int(pp.n_observations(concept))
            pop_mean = float(pp.posterior_mean(concept))
        except Exception:
            return (_COLDSTART_GENERIC_ALPHA, _COLDSTART_GENERIC_BETA, None, 0)
        if n_obs >= COLDSTART_MIN_POP_OBS:
            pm = min(max(pop_mean, 1e-3), 1.0 - 1e-3)
            alpha = COLDSTART_PRIOR_STRENGTH * pm
            beta = COLDSTART_PRIOR_STRENGTH * (1.0 - pm)
            return (alpha, beta, pop_mean, n_obs)
        # too few observations: keep the generic seed but still report pop_mean
        return (_COLDSTART_GENERIC_ALPHA, _COLDSTART_GENERIC_BETA, pop_mean, n_obs)

    def reset_coldstart_prior(self) -> None:
        """Reset the population prior to its deterministic warm-started baseline.

        Called at the START of a fresh replay/experiment/external run so the
        run begins from the same fixed baseline (the sealed cohort snapshot)
        regardless of priors accumulated by earlier runs in the same long-lived
        process — making API-driven runs replay-deterministic, the same property
        the ReplayEngine gets for free by constructing a fresh brain. The live
        interactive traffic never calls this, so its global per-concept prior
        keeps growing as intended.
        """
        if not getattr(self, "_coldstart_prior_enabled", False):
            return
        try:
            _pp_cls = _load_population_prior_class()
            if _pp_cls is not None:
                self._population_prior = _pp_cls(prior_alpha=1.0, prior_beta=1.0)
                self._warm_up_population_prior()
                logger.info("🔥 COLD-START PRIOR: reset to warm-started baseline for new run")
        except Exception as _e:  # pragma: no cover - defensive
            logger.warning(f"⚠️ Cold-start prior reset failed: {_e}")

    def _record_runtime_capability(
        self,
        name: str,
        dotted_path: str,
        value: Any,
        *,
        required: bool = False,
        error: Optional[str] = None,
    ) -> CapabilityRecord:
        available = value is not None and error is None
        return CapabilityRecord(
            name=name,
            dotted_path=dotted_path,
            required=required,
            available=available,
            status="loaded" if available else "missing",
            error=error,
        )

    def _emit_capability_manifest(self) -> None:
        """Build and log the Slice 0b cognitive capability manifest."""
        global _LATEST_CAPABILITY_MANIFEST

        runtime_records = {
            "transfer_engine.runtime": self._record_runtime_capability(
                "transfer_engine.runtime",
                "UnifiedLearningBrain.transfer_engine",
                getattr(self, "transfer_engine", None),
            ),
            "metrics_aggregator.runtime": self._record_runtime_capability(
                "metrics_aggregator.runtime",
                "UnifiedLearningBrain.metrics_aggregator",
                getattr(self, "metrics_aggregator", None),
            ),
            "learner_factory.runtime": self._record_runtime_capability(
                "learner_factory.runtime",
                "UnifiedLearningBrain.learner_factory",
                getattr(self, "learner_factory", None),
            ),
            "learning_engine.runtime": self._record_runtime_capability(
                "learning_engine.runtime",
                "UnifiedLearningBrain.learning_engine",
                getattr(self, "learning_engine", None),
            ),
            "bandit.runtime": self._record_runtime_capability(
                "bandit.runtime",
                "UnifiedLearningBrain.bandit",
                getattr(self, "bandit", None),
            ),
            "transfer_aware_bandit.runtime": self._record_runtime_capability(
                "transfer_aware_bandit.runtime",
                "UnifiedLearningBrain.transfer_aware_bandit",
                getattr(self, "transfer_aware_bandit", None),
            ),
            "jt_ensemble.runtime": self._record_runtime_capability(
                "jt_ensemble.runtime",
                "UnifiedLearningBrain.jt_ensemble",
                getattr(self, "jt_ensemble", None),
                required=True,
            ),
            "jt_governance.runtime": self._record_runtime_capability(
                "jt_governance.runtime",
                "UnifiedLearningBrain.jt_governance",
                getattr(self, "jt_governance", None),
                required=True,
            ),
            "trajectory_recorder.runtime": self._record_runtime_capability(
                "trajectory_recorder.runtime",
                "UnifiedLearningBrain.trajectory_recorder",
                getattr(self, "trajectory_recorder", None),
            ),
            "learning_state_repo.runtime": self._record_runtime_capability(
                "learning_state_repo.runtime",
                "UnifiedLearningBrain._learning_state_repo",
                getattr(self, "_learning_state_repo", None),
            ),
            "trace_repo.runtime": self._record_runtime_capability(
                "trace_repo.runtime",
                "UnifiedLearningBrain._trace_repo",
                getattr(self, "_trace_repo", None),
            ),
            "personalizer.runtime": self._record_runtime_capability(
                "personalizer.runtime",
                "UnifiedLearningBrain.personalizer",
                getattr(self, "personalizer", None),
            ),
        }

        manifest = CapabilityManifest.build(
            environment=self.environment,
            import_records=_BRAIN_IMPORT_RECORDS,
            runtime_records=runtime_records,
        )
        self.capability_manifest = manifest
        _LATEST_CAPABILITY_MANIFEST = manifest

        for record in runtime_records.values():
            if not record.available:
                _increment_capability_missing(record.name, record.required)
                logger.warning(
                    "hcie_capability_missing",
                    extra={
                        "capability": record.name,
                        "required": record.required,
                        "environment": self.environment,
                        "manifest_fingerprint": manifest.fingerprint,
                    },
                )

        logger.info(
            "hcie_capability_manifest",
            extra={
                "event_type": "CapabilityManifestEmitted",
                "manifest_fingerprint": manifest.fingerprint,
                "environment": manifest.environment,
                "boot_time": manifest.boot_time,
                "engine_count": len(manifest.engines),
            },
        )
    
    def _init_production_infrastructure(self):
        """
        Initialize production infrastructure (always required, not just deterministic mode).
        
        🔥 CRITICAL: This must run for ALL initialization paths, not just deterministic mode.
        This ensures UnifiedBrain always has _learning_state_repo for governance-state persistence.
        """
        try:
            # Create transfer engine first (always available)
            self.transfer_engine = TransferLearningEngine()
            
            # Initialize research-grade measurement
            self.metrics_aggregator = LearningMetricsAggregator()
            
            # Initialize advanced components
            self._init_advanced_layers()
            
            # Try to create full stack, fall back to minimal
            try:
                # Redis/cache store is provided by application DI. Core owns
                # cognition logic only and must not import infrastructure.
                if self.redis_store is None:
                    raise RuntimeError("redis_store is required for UnifiedLearningBrain production infrastructure")
                
                # 🔥 BULLETPROOF: Environment-based repository selection
                
                if self.environment == "production":
                    # Production mode: Use Postgres repository
                    try:
                        if self.db_store is None:
                            raise RuntimeError("postgres_store is required in production mode")
                        if self._learning_state_repo is None:
                            raise RuntimeError("learning_state_repo is required in production mode")
                        
                        logger.info("🔥 Postgres learning state repository initialized (production mode)")
                        logger.info("🔬 Learning trace repository initialized")
                        
                        # 🔄 LEGACY: Keep Redis for backward compatibility but mark as cache
                        self._canonical_state_store = self.redis_store  # Cache only
                        logger.info(" Redis now used as cache only (Postgres is source of truth)")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to initialize Postgres repository: {e}")
                        raise RuntimeError(f"CRITICAL: Production mode requires Postgres repository: {e}")
                        
                elif self.environment == "research":
                    # Research mode: Use in-memory repository
                    self._learning_state_repo = InMemoryLearningStateRepository()
                    self._canonical_state_store = self.redis_store  # Still use Redis for cache
                    logger.info("🔥 In-memory learning state repository initialized (research mode)")
                    
                else:
                    raise ValueError(
                        f"Invalid environment: {self.environment!r}. "
                        f"Allowed environments: {UnifiedLearningBrain.ALLOWED_ENVIRONMENTS}. "
                        f"'staging' is intentionally not supported in FINAL — adding fake "
                        f"staging semantics would create a non-canonical topology. "
                        f"Use 'production' (real Postgres + outbox) or 'research' "
                        f"(in-memory repository)."
                    )
                
                # 🔥 CRITICAL: Initialize idempotency manager for distributed system safety
                from .idempotency_manager import IdempotencyManager
                self._idempotency_manager = IdempotencyManager(self.redis_store)
                logger.info(" Idempotency manager initialized for distributed system safety")
                
                # Create learner factory with transfer engine and learning state repository
                self.learner_factory = LearnerFactory(
                    redis_store=self.redis_store, 
                    transfer_engine=self.transfer_engine,
                    learning_state_repo=self._learning_state_repo
                )
                
                # 🔥 BULLETPROOF: Initialize learners dictionary for batch writing
                self.learners = {}
                for learner_type in ["lyapunov", "bayesian", "kalman"]:
                    self.learners[learner_type] = self.learner_factory.get(learner_type)
                
                # Create learning engine WITH learner factory
                self.learning_engine = LearningLoopEngineV2(learner_factory=self.learner_factory)
                
                # SQL store is injected above in production mode; research mode
                # may intentionally leave it unset.
                
                # 🔥 PRIORITY 2: Pass deterministic bandit RNG stream if deterministic mode enabled
                bandit_rng_stream = self.rng_manager.get_bandit_stream() if self.deterministic and self.rng_manager else None
                self.bandit = ContextualBandit(rng_stream=bandit_rng_stream)

                # 🔥 TRANSFER-AWARE BANDIT: Initialize transfer-aware bandit for inter-concept selection
                try:
                    from core.bandit.transfer_aware_bandit import TransferAwareBandit
                    self.transfer_aware_bandit = TransferAwareBandit(
                        bandit=self.bandit,
                        pg_store=self.db_store,
                        transfer_engine=self.adaptive_transfer_engine
                    )
                    logger.info("🔥 Transfer-aware bandit initialized for inter-concept selection")
                except Exception as e:
                    self.transfer_aware_bandit = None
                    logger.warning(f"⚠️ Transfer-aware bandit initialization failed: {e}")

                # 🔥 CONTROL: Initialize JT-attributed ensemble for adaptive weights
                self.jt_ensemble = JTAttributedEnsemble(window_size=100, ema_alpha=0.1)
                logger.info("🔥 JT-attributed ensemble initialized (adaptive ensemble weights)")

                # 🔥 CONSTITUTIONAL FOUNDATION: Initialize constitutional JT governance
                self.jt_governance = ConstitutionalJTGovernance(window_size=10)
                logger.info("🔥 Constitutional JT governance initialized (principled decomposition, not heuristic aggregation)")

                # 🔥 POLICY CONFIGURATION: Apply policy configuration as non-breaking overrides (only in experiment context)
                if self.experiment_context and self.policy_config:
                    self._apply_policy_config(self.policy_config)
                    logger.info(f"🔥 Policy configuration applied (experiment context): {self.policy_config.config.get('policy_name', 'unknown')}")
                elif self.policy_config and not self.experiment_context:
                    logger.warning("⚠️ Policy configuration provided but experiment_context=False, using default production behavior")

                
            except Exception as e:
                import traceback
                traceback.print_exc()
                
                # Minimal fallback
                self.learner_factory = None
                self.learning_engine = None
                self.db_store = None
                self.bandit = None
                self.jt_ensemble = JTAttributedEnsemble(window_size=100, ema_alpha=0.1)  # Still initialize for minimal mode
                self.jt_governance = ConstitutionalJTGovernance(window_size=10)  # Initialize constitutional governance
                self.redis_store = None  # ✅ FIXED: Set redis_store to None
                
                # 🔥 BULLETPROOF: Initialize minimal components for research mode
                try:
                    from .idempotency_manager import IdempotencyManager
                    # Create minimal idempotency manager for research mode
                    class MinimalIdempotencyManager:
                        def __init__(self):
                            self.processed_events = {}
                        
                        def acquire_lock(self, event_id, timeout_seconds=30):
                            return True
                        
                        def release_lock(self, event_id):
                            pass
                        
                        def is_processed(self, event_id):
                            return event_id in self.processed_events
                        
                        def mark_processed(self, event_id, result):
                            self.processed_events[event_id] = result
                        
                        def check_duplicate_by_content(self, event_data):
                            return None
                        
                        def mark_content_hash(self, event_data, event_id):
                            pass
                        
                        def get_cached_result(self, event_id):
                            return self.processed_events.get(event_id)
                    
                    self._idempotency_manager = MinimalIdempotencyManager()
                    logger.info(" Minimal idempotency manager initialized for research mode")
                except ImportError:
                    self._idempotency_manager = None
                    logger.warning(" No idempotency manager available")
            
            # ✅ FIXED: Fallback canonical state store for minimal stack
            if not hasattr(self, '_canonical_state_store'):
                self._canonical_state_store = None
                logger.warning("⚠️ Canonical state store not initialized")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize production infrastructure: {e}")
            raise
    
    def _init_deterministic_mode(self, config):
        """
        Initialize deterministic mode components.
        
        Architecture Principles:
        - Namespace-based UUIDs (uuid5) for replay stability
        - Isolated RNG streams (time, noise, bandit, exploration, uuid)
        - Simulated time provider with dedicated RNG stream
        - PYTHONHASHSEED set externally (not here)
        
        🔥 PRIORITY 2: Seed all RNGs (numpy, random) for trajectory determinism
        
        Args:
            config: DeterministicModeConfig
        """
        from core.determinism.deterministic_uuid import DeterministicUUIDGenerator
        from core.determinism.rng_stream_manager import RNGStreamManager
        from core.determinism.simulated_time import SimulatedTimeProvider

        # 🔥 FIX: Eliminate global numpy seeding - use per-instance RNG instead
        # Global np.random.seed() causes async divergence under concurrency
        # Use RNGStreamManager for isolated streams instead
        if config.trajectory_determinism:
            import numpy as np
            import random as py_random
            # 🔥 FIX: Use per-instance RNG instead of global mutation
            self.global_rng = np.random.default_rng(config.seed)
            py_random.seed(config.seed)  # Still seed Python random for legacy compatibility
            logger.info(f"🔥 PRIORITY 2: Initialized per-instance RNG with seed={config.seed} (no global mutation)")

        # Initialize RNG stream manager (isolated streams)
        self.rng_manager = RNGStreamManager(seed=config.seed)
        
        # Initialize deterministic UUID generator (namespace-based)
        if config.deterministic_uuids:
            self.uuid_gen = DeterministicUUIDGenerator(seed=config.seed)
        else:
            self.uuid_gen = None
        
        # Initialize simulated time provider (with dedicated RNG stream)
        if config.deterministic_time:
            self.time_provider = SimulatedTimeProvider(
                seed=config.seed,
                rng_stream=self.rng_manager.get_time_stream()
            )
        else:
            self.time_provider = None
        
        # CRITICAL: Do NOT set PYTHONHASHSEED here
        # Set externally in: Docker compose, CI pipeline, experiment launcher, replay scripts
        # Python hash seed is process-start scoped, changing during runtime is unreliable
        
        # 🔥 NOTE: Production infrastructure (including _learning_state_repo) is now initialized
        # in _init_production_infrastructure() which is called from __init__ for ALL paths
        # This ensures governance-state persistence is always available
    
    def _apply_policy_config(self, policy_config):
        """
        Apply policy configuration as non-breaking overrides to existing components
        
        This method applies policy configuration as parameter overrides, NOT logic replacement.
        It preserves existing cognition semantics and only influences behavior through parameters.
        
        Args:
            policy_config: PolicyConfiguration object with policy parameters
        
        Risk Mitigation:
        - Non-breaking: Only applies if components exist
        - Parameter-only: Overrides parameters, not logic
        - Backward compatible: If policy_config is None, uses default behavior
        - Observable: Policy configuration logged and recorded in metrics
        """
        try:
            # Apply governance weights to JT governance
            if hasattr(self, 'jt_governance') and self.jt_governance:
                governance_weights = policy_config.get_governance_weights()
                if governance_weights:
                    # Override governance weights (non-breaking parameter change)
                    if hasattr(self.jt_governance, 'governance_weights'):
                        self.jt_governance.governance_weights.update(governance_weights)
                        logger.info(f"🔥 Policy config: Governance weights overridden: {governance_weights}")
            
            # Apply bandit configuration to contextual bandit
            if hasattr(self, 'bandit') and self.bandit:
                bandit_config = policy_config.get_bandit_config()
                if bandit_config:
                    # Override bandit parameters (non-breaking parameter change)
                    if 'uncertainty_weight' in bandit_config:
                        self.bandit.uncertainty_weight = bandit_config['uncertainty_weight']
                    if 'exploration_rate' in bandit_config:
                        self.bandit.exploration_rate = bandit_config['exploration_rate']
                    if 'jt_aware_exploration' in bandit_config:
                        self.bandit.jt_aware_exploration = bandit_config['jt_aware_exploration']
                    logger.info(f"🔥 Policy config: Bandit config overridden: {bandit_config}")
            
            # Apply transfer configuration to transfer engine
            if hasattr(self, 'transfer_engine') and self.transfer_engine:
                transfer_config = policy_config.get_transfer_config()
                if transfer_config:
                    # Override transfer parameters (non-breaking parameter change)
                    if 'transfer_enabled' in transfer_config:
                        self.transfer_engine.enabled = transfer_config['transfer_enabled']
                    if 'transfer_multiplier' in transfer_config:
                        self.transfer_engine.transfer_multiplier = transfer_config['transfer_multiplier']
                    logger.info(f"🔥 Policy config: Transfer config overridden: {transfer_config}")
            
            # Apply ensemble weights to JT ensemble
            if hasattr(self, 'jt_ensemble') and self.jt_ensemble:
                ensemble_weights = policy_config.get_ensemble_weights()
                if ensemble_weights:
                    # Override ensemble weights (non-breaking parameter change)
                    if hasattr(self.jt_ensemble, 'ensemble_weights'):
                        self.jt_ensemble.ensemble_weights.update(ensemble_weights)
                        logger.info(f"🔥 Policy config: Ensemble weights overridden: {ensemble_weights}")
            
            # Record policy configuration in metrics for observability
            if hasattr(self, 'metrics_aggregator') and self.metrics_aggregator:
                self.metrics_aggregator.record_metric(
                    "policy_config_applied",
                    1.0,
                    tags={"policy_name": policy_config.config.get("policy_name", "unknown")}
                )
            
            logger.info("✅ Policy configuration applied successfully (non-breaking parameter overrides)")
            
        except Exception as e:
            logger.error(f"❌ Failed to apply policy configuration: {e}")
            # Non-breaking: Continue with default behavior if policy config fails
            logger.warning("Continuing with default behavior (policy config application failed)")
    
    def _init_advanced_layers(self):
        """Initialize advanced layers for 25+ layer system"""
        
        # Layer 13: Signal Processing Weights
        try:
            from core.signal.signal_extractor import SignalExtractor
            self.signal_extractor = SignalExtractor()
        except ImportError:
            self.signal_extractor = None
        
        # Layer 14: Policy Engine Weights
        try:
            from core.policy.policy import PolicyEngine
            self.policy_engine = PolicyEngine()
        except ImportError:
            self.policy_engine = None
        
        # Layer 15: Reward Calculation Weights
        try:
            from core.reward.reward import RewardCalculator
            self.reward_calculator = RewardCalculator()
        except ImportError:
            self.reward_calculator = None
        
        # Layer 16: Confidence-Weighted Learning
        try:
            from core.learning.confidence_weighted_learner import ConfidenceWeightedLearner
            self.confidence_learner = ConfidenceWeightedLearner(base_learning_rate=0.08)
        except ImportError:
            self.confidence_learner = None
        
        # Layer 17: Research Logger
        try:
            from core.learning.research_logger import ResearchLogger
            self.research_logger = ResearchLogger()
        except ImportError:
            self.research_logger = None
        
        #  REMOVED: Transfer-Aware Learning initialization
        # TransferAwareLearner is now a pure function provider only
        # No initialization needed since it won't write state
        
        # Layer 19: Adaptive Transfer Engine (Additional)
        try:
            from core.learning.adaptive_transfer_engine import AdaptiveTransferEngine
            self.adaptive_transfer_engine = AdaptiveTransferEngine()
        except ImportError:
            self.adaptive_transfer_engine = None
        
        # Layer 20: Real DAG Dependencies (Additional)
        try:
            from core.learning.real_dag_dependencies import RealDAGDependencies
            self.real_dag_dependencies = RealDAGDependencies()
        except ImportError:
            self.real_dag_dependencies = None
        
        # Layer 19-22: Configuration & Performance Tracking
        self.cumulative_regret = 0.0
        self.learning_regret = 0.0
        self.decision_regret = 0.0
        self.total_interactions = 0
        
    
    def get_recommendation(self, user_id: str, mastery_data: Optional[Dict[str, Any]] = None, transfer_aware: bool = False) -> Dict[str, Any]:
        """
        Get recommendation for next learning concept using two-level decision hierarchy
        
        Level 1: Transfer-aware bandit selects concept (inter-concept with transfer)
        Level 2: Normal bandit selects task within concept (intra-concept)
        
        Args:
            user_id: User identifier
            mastery_data: Current mastery data for all concepts
            transfer_aware: Whether to use transfer-aware concept selection (default: False)
        
        This is the SINGLE source of truth for ALL recommendation logic
        """
        try:
            # ✅ EFFICIENT: Use provided mastery_data or compute once
            if mastery_data is None:
                key_concepts = ["k2_algorithms", "k5_algorithms", "k8_algorithms", 
                              "k2_computing_systems_devices", "k2_networks_communication"]
                
                mastery_data = {}
                for concept in key_concepts:
                    result = self.process_event(user_id=user_id, concept=concept, mode="read", write_enabled=True)
                    # ✅ STORE FULL LEARNING RESULT (including real Bayesian parameters)
                    mastery_data[concept] = {
                        "mastery": result.mastery,
                        "bayesian_alpha": getattr(result, 'bayesian_alpha', None),
                        "bayesian_beta": getattr(result, 'bayesian_beta', None)
                    }
            
            # 🔥 TRANSFER-AWARE MODE: Use TransferAwareBandit for concept selection
            if transfer_aware and self.transfer_aware_bandit:
                try:
                    recommendation = self.transfer_aware_bandit.get_transfer_aware_recommendation(
                        user_id=user_id,
                        mastery_data={k: (v["mastery"] if isinstance(v, dict) else v) for k, v in mastery_data.items()},
                        context={"mode": "transfer_aware"}
                    )
                    
                    logger.info(f"🔥 TRANSFER-AWARE RECOMMENDATION: {recommendation}")
                    
                    return {
                        "recommended_concept": recommendation.get("recommended_concept"),
                        "mastery": recommendation.get("mastery"),
                        "mastery_gap": recommendation.get("mastery_gap"),
                        "transfer_bonus": recommendation.get("transfer_bonus"),
                        "exploration_cost": recommendation.get("exploration_cost"),
                        "score": recommendation.get("score"),
                        "transfer_relationships": recommendation.get("transfer_relationships", []),
                        "recommendation_reason": "transfer_aware",
                        "selection_engine": "transfer_aware_bandit",
                        "mastery_data": {k: (v["mastery"] if isinstance(v, dict) else v) for k, v in mastery_data.items()}
                    }
                except Exception as e:
                    logger.warning(f"Transfer-aware recommendation failed, falling back to normal bandit: {e}")
                    # Fall through to normal bandit
            
            # ✅ NORMAL BANDIT MODE: Use normal bandit for concept selection
            if self.bandit:
                # Build candidates for bandit (same as task generation)
                candidates = [{"concept_id": concept} for concept in mastery_data.keys()]
                
                # Build mastery context for bandit (same as task generation)
                mastery_context = {}
                for concept_id, data in mastery_data.items():
                    if isinstance(data, dict):
                        mastery_context[concept_id] = data["mastery"]
                    else:
                        mastery_context[concept_id] = data  # data is already a float
                
                try:
                    # ✅ BANDIT DECISION: Use bandit to select best concept (READ MODE)
                    # ✅ FIXED: Use REAL Bayesian posterior parameters (not synthetic reconstruction)
                    mastery_params = {}
                    for concept, data in mastery_data.items():
                        if isinstance(data, dict):
                            mastery = data["mastery"]
                            bayesian_alpha = data["bayesian_alpha"]
                            bayesian_beta = data["bayesian_beta"]
                        else:
                            mastery = data  # data is already a float
                            bayesian_alpha = None
                            bayesian_beta = None
                        
                        # ✅ REAL: Use actual Bayesian posterior parameters
                        if bayesian_alpha is not None and bayesian_beta is not None:
                            alpha = bayesian_alpha
                            beta = bayesian_beta
                            logger.debug(f"✅ REAL Bayesian params for {concept}: α={alpha:.2f}, β={beta:.2f} (from posterior)")
                        else:
                            # 🔥 FIX F-027: Use cold-start prior only when truly missing (not as default)
                            alpha, beta = 3.0, 7.0
                            logger.warning(
                                f"⚠️ Missing Bayesian posterior for {concept}; using cold-start prior α=3, β=7"
                            )
                        
                        mastery_params[concept] = (alpha, beta)
                    
                    bandit_result = self.bandit.select_arm(
                        user_id=user_id,
                        available_nodes=[c["concept_id"] for c in candidates],
                        mastery_params=mastery_params,
                        representation_params={},  # Not needed for concept selection
                        difficulty_map={},  # Not needed for concept selection
                        context={"mode": "recommendation"}  # Read mode context
                    )
                    
                    # Handle different return formats
                    if isinstance(bandit_result, tuple) and len(bandit_result) >= 3:
                        selected_concept, representation, score = bandit_result[:3]
                    elif isinstance(bandit_result, tuple) and len(bandit_result) >= 2:
                        selected_concept, score = bandit_result[:2]
                        representation = "concept"
                    elif isinstance(bandit_result, (list, tuple)):
                        selected_concept = bandit_result[0]
                        score = float(bandit_result[1]) if len(bandit_result) > 1 else 0.5
                        representation = "concept"
                    else:
                        # Single value returned
                        selected_concept = bandit_result
                        score = 0.5
                        representation = "concept"
                    
                    return {
                        "recommended_concept": selected_concept,
                        "recommendation_score": round(score, 3),
                        "mastery_data": {k: (v["mastery"] if isinstance(v, dict) else v) for k, v in mastery_data.items()},  # Extract mastery for compatibility
                        "recommendation_reason": "bandit_selected",
                        "bandit_context": mastery_context,
                        "selection_engine": "contextual_bandit"
                    }
                except Exception as e:
                    logger.warning(f"Bandit recommendation failed, using mastery fallback: {e}")
                    # Fallback to mastery-based (but still inside brain)
                    mastery_dict = {k: (v["mastery"] if isinstance(v, dict) else v) for k, v in mastery_data.items()}
                    best_concept = max(mastery_dict.items(), key=lambda x: x[1] if x[1] < 0.8 else 0)[0]
                    best_mastery = mastery_dict[best_concept]
                    
                    return {
                        "recommended_concept": best_concept,
                        "recommendation_score": round(best_mastery, 2),
                        "mastery_data": mastery_dict,
                        "recommendation_reason": "bandit_fallback",
                        "selection_engine": "mastery_fallback"
                    }
            else:
                # No bandit available, use simple mastery-based fallback
                mastery_dict = {k: (v["mastery"] if isinstance(v, dict) else v) for k, v in mastery_data.items()}
                best_concept = max(mastery_dict.items(), key=lambda x: x[1] if x[1] < 0.8 else 0)[0]
                best_mastery = mastery_dict[best_concept]
                
                return {
                    "recommended_concept": best_concept,
                    "recommendation_score": round(best_mastery, 2),
                    "mastery_data": mastery_dict,
                    "recommendation_reason": "no_bandit_mastery_based",
                    "selection_engine": "mastery_fallback"
                }
        
        except Exception as e:
            logger.error(f"❌ Error getting recommendation for {user_id}: {e}")
            # Safe fallback (K-12 framework)
            return {
                "recommended_concept": "k2_computing_systems_devices",
                "recommendation_score": 0.5,
                "recommendation_reason": "fallback_error",
                "selection_engine": "emergency_fallback"
            }
    
    def process_kafka_event(self, event_data: Dict[str, Any], write_enabled: bool = True) -> LearningResult:
        """
        🚀 EVENT-DRIVEN ENTRYPOINT: Process learning event from Kafka
        This is the ONLY method called by the learning consumer
        
        Args:
            event_data: Dictionary containing:
                - event_id: Required unique identifier
                - user_id: Required user identifier  
                - concept: Required learning concept
                - interaction: Required interaction data
                - timestamp: Optional event timestamp
                - source: Optional source identifier
                
        Returns:
            LearningResult: Complete canonical state with all components
            
        Raises:
            ValueError: If required fields are missing
            RuntimeError: If event processing fails
        """
        # 🔥 CRITICAL: Validate required fields
        required_fields = ["event_id", "user_id", "concept", "interaction"]
        for field in required_fields:
            if field not in event_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Extract event data
        event_id = event_data["event_id"]
        user_id = event_data["user_id"]
        concept = event_data["concept"]
        interaction = event_data["interaction"]
        interaction_id = event_data.get("task_id", f"kafka_{event_id}")
        
        # Log event processing
        source = event_data.get("source", "kafka")
        logger.info(f"🚀 Processing Kafka event {event_id} from {source}: user={user_id}, concept={concept}")
        
        # Delegate to main process_event method
        return self.process_event(
            user_id=user_id,
            concept=concept,
            interaction=interaction,
            mode="write",  # Always write mode for state changes
            event_id=event_id,
            interaction_id=interaction_id,
            write_enabled=True,  # Default to enabled for normal operation
            event_data=event_data  # 🔥 CRITICAL: Pass original event data for confidence workaround
        )
    
    def _get_canonical_state_from_postgres(self, user_id: str, concept: str) -> Optional[Dict[str, Any]]:
        """
        🔥 PHASE 4: Get canonical state from Postgres (source of truth)
        Falls back to Redis cache if Postgres fails
        """
        if self._learning_state_repo:
            try:
                state_data = self._learning_state_repo.get_state(user_id, concept)

                if state_data:
                    logger.debug(f"📖 Retrieved canonical state from Postgres: {user_id}/{concept}")
                    return state_data
                else:
                    logger.debug(f"📖 No canonical state found in Postgres: {user_id}/{concept}")
                    # 🔥 OBSERVABILITY: Track canonical state misses
                    UnifiedLearningBrain._canonical_state_misses += 1
            except Exception as e:
                logger.warning(f"⚠️ Failed to get canonical state from Postgres: {e}")
                return None

        return None
    
    def process_event(self, user_id: str, concept: str, interaction: Optional[Dict[str, Any]] = None, mode: str = "write", event_id: Optional[str] = None, interaction_id: Optional[str] = None, write_enabled: bool = True, event_data: Optional[Dict[str, Any]] = None) -> LearningResult:
        """
        ONE canonical function that handles all learning operations with distributed system safety
        
        Args:
            user_id: User identifier
            concept: Learning concept
            interaction: User interaction data (correctness, response_time, etc.)
            mode: "read" (inference), "write" (update), "simulation" (experiment)
            event_id: Unique identifier for deduplication
            interaction_id: Unique identifier for interaction tracking
            write_enabled: Whether to write state changes (False for shadow mode)
            
        Returns:
            LearningResult: Complete canonical state with all components
        """
        timestamp = datetime.now()
        
        # 🔥 CRITICAL: Generate event_id if not provided for distributed safety
        if not event_id:
            import uuid
            event_id = str(uuid.uuid4())
        if not interaction_id:
            interaction_id = f"auto_{event_id}"

        if interaction:
            interaction = normalize_interaction_for_brain(interaction)
        
        # 🔬 CAPTURE TRUE STATE_BEFORE (critical for research validity)
        # Must happen BEFORE any state updates to ensure accurate delta measurement
        state_before = self._get_canonical_state_from_postgres(user_id, concept) if self._learning_state_repo else {}
        # 🔥 CRITICAL FIX: Handle None state_before
        if state_before is None:
            state_before = {}
        
        # Define state_key for error handling
        state_key = f"{user_id}_{concept}"
        
        # 🔥 CRITICAL: Check idempotency before processing
        if mode == "write" and self._idempotency_manager is not None:
            # 🔒 CRITICAL: Acquire distributed lock BEFORE any checks
            if not self._idempotency_manager.acquire_lock(event_id, timeout_seconds=30):
                # Lock failed - wait and retry
                import time
                time.sleep(0.1)
                
                # Check if processed while waiting
                if self._idempotency_manager.is_processed(event_id):
                    cached_result = self._idempotency_manager.get_cached_result(event_id)
                    if cached_result:
                        return build_learning_result(cached_result)
                
                logger.error(f"❌ Failed to acquire lock for event {event_id}")
                raise RuntimeError(f"Could not acquire lock for event {event_id}")
            
            try:
                # Create event data for deduplication check (exclude timestamp for determinism)
                event_data = {
                    "user_id": user_id,
                    "concept": concept,
                    "interaction": interaction,
                    "mode": mode
                }
                
                # Check if already processed
                # 🔥 CRITICAL: Skip idempotency check in experiment context to allow state persistence
                # Deterministic UUIDs cause events to be marked as "already processed" across runs
                if not self.experiment_context and self._idempotency_manager.is_processed(event_id):
                    cached_result = self._idempotency_manager.get_cached_result(event_id)
                    if cached_result:
                        return build_learning_result(cached_result)
                    else:
                        logger.error(f"❌ Event {event_id} marked processed but no cached result")
                        raise RuntimeError(f"Inconsistent state for event {event_id}")
                
                # Check for duplicate by content
                duplicate_event_id = self._idempotency_manager.check_duplicate_by_content(event_data)
                if duplicate_event_id:
                    duplicate_result = self._idempotency_manager.get_cached_result(duplicate_event_id)
                    if duplicate_result:
                        # Mark current event as processed to prevent future duplicates
                        self._idempotency_manager.mark_processed(event_id, duplicate_result)
                        
                        # 🔥 CRITICAL: Save final state to database even for duplicates
                        # This ensures mastery_delta is persisted for API consistency
                        final_state = {
                            "mastery": duplicate_result.get("mastery", 0.3),
                            "uncertainty": duplicate_result.get("uncertainty", 0.2),
                            "confidence": duplicate_result.get("confidence", 0.8),
                            "lyapunov_mastery": duplicate_result.get("lyapunov_mastery", 0.3),
                            "bayesian_alpha": duplicate_result.get("bayesian_alpha", 3.0),
                            "bayesian_beta": duplicate_result.get("bayesian_beta", 7.0),
                            "kalman_mastery": duplicate_result.get("kalman_mastery", 0.3),
                            "kalman_covariance": duplicate_result.get("kalman_covariance", 0.1),
                            # 🔥 CONTROL: JT-attributed ensemble weights (adaptive, not static)
                            "ensemble_weights": self.jt_ensemble.get_weights(),
                            "ensemble_variance": duplicate_result.get("ensemble_variance", 0.02),
                            "policy": duplicate_result.get("policy", "default"),
                            "policy_multiplier": duplicate_result.get("policy_multiplier", 1.0),
                            "transfer_amounts": duplicate_result.get("transfer_amounts", {}),
                            "transfer_efficiency": duplicate_result.get("transfer_efficiency", 0.0),
                            "zpd_target": duplicate_result.get("zpd_target", 0.3),
                            "zpd_alignment_error": duplicate_result.get("zpd_alignment_error", 0.0),
                            "zpd_score": duplicate_result.get("zpd_score", 0.8),
                            "zpd_delta_signal": duplicate_result.get("zpd_delta_signal", 0.0),
                            "timestamp": duplicate_result.get("timestamp", datetime.now().isoformat()),
                            "processing_mode": duplicate_result.get("processing_mode", "read"),
                            "processing_time": duplicate_result.get("processing_time", 0.0),
                            "J_value": duplicate_result.get("J_value", None),
                            # 🔥 CRITICAL: Include mastery_delta for API delta calculation
                            "mastery_delta": duplicate_result.get("mastery_delta", 0.0),
                            "event_id": duplicate_result.get("event_id", event_id),
                            "interaction_id": duplicate_result.get("interaction_id", None),
                            "adaptive_rate": duplicate_result.get("adaptive_rate", 0.02)
                        }
                        # 🔥 SINGLE WRITER: Repository handles all writes atomically
                        # No direct PostgreSQL writes - ensures consistency
                        logger.info(f"✅ Duplicate event state ready for repository write: {user_id}/{concept}")
                        
                        return build_learning_result(duplicate_result)
                    else:
                        logger.error(f"❌ Duplicate event {duplicate_event_id} has no cached result")
                        raise RuntimeError(f"Inconsistent duplicate handling for {event_id}")
            
            except Exception as e:
                # Always release lock on error
                if self._idempotency_manager is not None:
                    self._idempotency_manager.release_lock(event_id)
                raise
        
        if mode == "read":
            return self._read_mode(user_id, concept, interaction, timestamp, event_id, interaction_id)
        elif mode == "write":
            try:
                
                # 🔥 CRITICAL FIX: Ensure canonical state exists BEFORE any learner/bandit operations
                existing_state = self._get_canonical_state_from_postgres(user_id, concept)
                
                if existing_state is None:
                    logger.info(f"🔥 COLD START INIT: {user_id}/{concept}")
                    
                    # Create initial canonical state for cold start
                    import time
                    initial_state = {
                        "mastery": 0.3,
                        "uncertainty": 0.2,
                        "zpd_score": 0.8,
                        "lyapunov_mastery": 0.3,
                        "bayesian_alpha": 1.5,
                        "bayesian_beta": 3.5,
                        "kalman_mastery": 0.3,
                        "kalman_covariance": 0.1,
                        "timestamp": time.time()
                    }
                    
                    if write_enabled:
                        # 🔥 SINGLE WRITER: Repository handles all writes atomically
                        # No direct PostgreSQL writes - ensures consistency
                        logger.info(f"✅ Cold start state ready for repository write: {user_id}/{concept}")
                
                try:
                    result = self._write_mode(user_id, concept, interaction, timestamp, event_id, interaction_id, write_enabled, state_before, event_data)
                except Exception as e:
                    logger.error(f"❌ Failed to process event: {e}")
                    raise
                
                # 🔥 CRITICAL: Mark as processed and cache result for idempotency
                result_dict = {
                    "mastery": result.mastery,
                    "uncertainty": result.uncertainty,
                    "confidence": result.confidence,
                    "lyapunov_mastery": result.lyapunov_mastery,
                    "bayesian_alpha": result.bayesian_alpha,
                    "bayesian_beta": result.bayesian_beta,
                    "kalman_mastery": result.kalman_mastery,
                    "kalman_covariance": result.kalman_covariance,
                    "ensemble_weights": result.ensemble_weights,
                    "ensemble_variance": result.ensemble_variance,
                    "policy": result.policy,
                    "policy_multiplier": result.policy_multiplier,
                    "transfer_amounts": result.transfer_amounts,
                    "transfer_efficiency": result.transfer_efficiency,
                    "zpd_target": result.zpd_target,
                    "zpd_alignment_error": result.zpd_alignment_error,
                    "zpd_score": result.zpd_score,
                    "zpd_delta_signal": result.zpd_delta_signal,
                    "processing_time": result.processing_time,
                    "timestamp": result.timestamp,
                    "processing_mode": result.processing_mode,
                    "J_value": result.J_value,
                    # 🔥 CRITICAL: Include debugging and analytics fields
                    "confidence_adjusted_mastery": result.confidence_adjusted_mastery,
                    "effective_learning_rate": result.effective_learning_rate,
                    "mastery_delta": result.mastery_delta,
                    "transfer_amount": result.transfer_amount,
                    "event_id": result.event_id,
                    "interaction_id": result.interaction_id,
                    # 🔥 CRITICAL: Include adaptive_rate for research validation
                    "adaptive_rate": getattr(result, 'adaptive_rate', 0.02),
                    # F-024: correctness for trajectory / worker path
                    "correct": getattr(result, 'correct', None),
                    "correctness": getattr(result, 'correctness', None),
                    # F-031: governance metrics for trajectory / worker path
                    "jt_volatility": getattr(result, 'jt_volatility', None),
                    "exploration_pressure": getattr(result, 'exploration_pressure', None),
                    "stability_index": getattr(result, 'stability_index', None),
                    # 🔥 PHASE A / Tier-2 audit: surface 6D decomposition + attribution +
                    # weight snapshot on the API payload so the cohort writer can
                    # persist them as explicit columns (no JSON archaeology).
                    "jt_delta_m_contribution": getattr(result, 'jt_delta_m_contribution', None),
                    "jt_transfer_contribution": getattr(result, 'jt_transfer_contribution', None),
                    "jt_transfer_prospective_contribution": getattr(
                        result, 'jt_transfer_prospective_contribution', None
                    ),
                    "jt_challenge_contribution": getattr(result, 'jt_challenge_contribution', None),
                    "jt_uncertainty_contribution": getattr(result, 'jt_uncertainty_contribution', None),
                    "jt_zpd_contribution": getattr(result, 'jt_zpd_contribution', None),
                    "jt_unclamped": getattr(result, 'jt_unclamped', None),
                    "jt_clamped": getattr(result, 'jt_clamped', None),
                    "jt_attribution": getattr(result, 'jt_attribution', None),
                    "weights_snapshot": getattr(result, 'weights_snapshot', None),
                    # Tier 2.5 V2 dims (None unless HCIE_REDESIGN_V2=1)
                    "jt_baseline_difficulty_contribution": getattr(result, 'jt_baseline_difficulty_contribution', None),
                    "jt_challenge_event_contribution": getattr(result, 'jt_challenge_event_contribution', None),
                    "jt_population_prior_contribution": getattr(result, 'jt_population_prior_contribution', None),
                    "jt_t_realized_v2_contribution": getattr(result, 'jt_t_realized_v2_contribution', None),
                    "jt_v2_active": getattr(result, 'jt_v2_active', None),
                    "jt_v2_state_snapshot": getattr(result, 'jt_v2_state_snapshot', None),
                    "jt_v2_challenge_event_fired": getattr(result, 'jt_v2_challenge_event_fired', None),
                    "jt_v2_challenge_event_reason": getattr(result, 'jt_v2_challenge_event_reason', None),
                }
                if self._idempotency_manager is not None:
                    self._idempotency_manager.mark_processed(event_id, result_dict)
                
                # 🔥 CRITICAL: Mark content hash for deduplication
                if self._idempotency_manager is not None:
                    self._idempotency_manager.mark_content_hash(event_data, event_id)
                
                # 🔥 CRITICAL: Save final result to database for persistence
                # Convert result to dict for DB storage (always needed for trace capture)
                final_state = {
                    "mastery": result.mastery,
                    "uncertainty": result.uncertainty,
                    "confidence": result.confidence,
                    "lyapunov_mastery": result.lyapunov_mastery,
                    "bayesian_alpha": result.bayesian_alpha,
                    "bayesian_beta": result.bayesian_beta,
                    "kalman_mastery": result.kalman_mastery,
                    "kalman_covariance": result.kalman_covariance,
                    "ensemble_weights": result.ensemble_weights,
                    "ensemble_variance": result.ensemble_variance,
                    "policy": result.policy,
                    "policy_multiplier": result.policy_multiplier,
                    "transfer_amounts": result.transfer_amounts,
                    "transfer_efficiency": result.transfer_efficiency,
                    "zpd_target": result.zpd_target,
                    "zpd_alignment_error": result.zpd_alignment_error,
                    "zpd_score": result.zpd_score,
                    "zpd_delta_signal": result.zpd_delta_signal,
                    "timestamp": result.timestamp,
                    "processing_mode": result.processing_mode,
                    "processing_time": result.processing_time,
                    "J_value": result.J_value,
                    # 🔥 CRITICAL: Include mastery_delta for API delta calculation
                    "mastery_delta": getattr(result, 'mastery_delta', 0.0),
                    "event_id": result.event_id,
                    "interaction_id": result.interaction_id,
                    "adaptive_rate": getattr(result, 'adaptive_rate', 0.02)
                }
                
                # 🔥 FIX F-027/F-028: Removed duplicate save_state that overwrites batch write
                # The batch write in _write_mode already persists the correct state with updated learner parameters
                # This duplicate write was overwriting with stale values from final_state
                
                # 🔥 TRAJECTORY (#59/#60): inline recording DISABLED.
                # This inline writer produced a SPARSE row (run_id=f"run_{event_id}",
                # hash interaction_number, no JT/ensemble columns because only a
                # thin governance_signals dict is passed here). For every write
                # interaction the runtime ALSO emits a CognitionUpdated outbox
                # event carrying the full Phase-14 payload, which the
                # trajectory_recorder_consumer persists with all JT/ensemble
                # columns populated. DB audit confirmed 23842/23842 inline rows
                # had a `_cognition` twin on the wire (zero legacy-only orphans),
                # so this inline path is fully redundant and only created the
                # duplicate sparse rows behind #60. The enriched Kafka-sourced
                # row is now the single trajectory authority for live/human
                # traffic; research traffic continues to use the dedicated
                # direct-SQL writer in experiments/cohorts.py (_record_trajectory).
                if False and self.trajectory_recorder:
                    try:
                        # Capture state_after for trajectory
                        state_after = self._get_canonical_state_from_postgres(user_id, concept) if self._learning_state_repo else final_state

                        self.trajectory_recorder.record_trajectory(
                            experiment_run_id=f"run_{event_id}",
                            user_id=user_id,
                            concept=concept,
                            interaction_id=interaction_id,
                            event_id=event_id,
                            state_before=state_before,
                            state_after=state_after,
                            governance_signals={
                                "J_value": result.J_value,
                                "policy": result.policy,
                                "policy_multiplier": result.policy_multiplier,
                                "adaptive_rate": getattr(result, 'adaptive_rate', 0.02),
                                "capability_manifest_fingerprint": (
                                    self.capability_manifest.fingerprint
                                    if self.capability_manifest
                                    else None
                                ),
                            },
                            interaction_data=interaction,
                        )
                        logger.debug(f"🔥 Trajectory recorded for {user_id}/{concept}")
                    except Exception as e:
                        logger.error(f"⚠️ Failed to record trajectory: {e}")
                    
                # 🔬 CAPTURE TRACE: Save algorithm trace for research API
                if hasattr(self, '_trace_repo') and self._trace_repo:
                    # Use pre-captured state_before (captured at method start)
                    # This ensures accurate delta measurement without race conditions
                    trace_data = {
                        "schema_version": "v1.0",
                        "observability": {
                            "cold_start": existing_state is None,
                            "state_source": "canonical"  # cold_start is a condition, not a source
                        },
                        "event": {
                            "event_id": event_id,
                            "user_id": user_id,
                            "concept": concept,
                            "timestamp": timestamp.isoformat()
                        },
                        "input": interaction,
                        "state_before": {
                            "mastery": state_before.get("mastery", 0.0),
                            "confidence": state_before.get("confidence", 0.0),
                            "uncertainty": state_before.get("uncertainty", 0.0)
                        },
                        "state_after": {
                            "mastery": final_state.get("mastery", 0.0),
                            "confidence": final_state.get("confidence", 0.0),
                            "uncertainty": final_state.get("uncertainty", 0.0)
                        },
                        "learners": {
                            "lyapunov": {
                                "mastery": final_state.get("lyapunov_mastery", 0.0)
                            },
                            "bayesian": {
                                "alpha": final_state.get("bayesian_alpha", 0.0),
                                "beta": final_state.get("bayesian_beta", 0.0)
                            },
                            "kalman": {
                                "mastery": final_state.get("kalman_mastery", 0.0),
                                "covariance": final_state.get("kalman_covariance", 0.0)
                            }
                        },
                        "ensemble": {
                            "weights": {"lyapunov": 0.33, "bayesian": 0.33, "kalman": 0.34},
                            "variance": 0.02
                        },
                        "learning": {
                            "mastery_after": result.mastery,
                            "mastery_delta": result.mastery_delta,
                            "effective_learning_rate": getattr(result, 'effective_learning_rate', 0.0),
                            "confidence_adjusted_mastery": getattr(result, 'confidence_adjusted_mastery', 0.0)
                        },
                        "transfer": {
                            "transfer_amounts": final_state.get("transfer_amounts", {}),
                            "total_transfer": final_state.get("total_transfer", 0.0),
                            "efficiency": final_state.get("transfer_efficiency", 0.0)
                        },
                        "zpd": {
                            "target": final_state.get("zpd_target", 0.0),
                            "score": final_state.get("zpd_score", 0.0),
                            "alignment_error": final_state.get("zpd_alignment_error", 0.0),
                            "delta_signal": final_state.get("zpd_delta_signal", 0.0)
                        },
                        "objective": {
                            "J_t": getattr(result, 'J_value', 0.0)
                        },
                        "decision": {
                            "selected_action": concept,
                            "available_actions": getattr(self, '_last_bandit_decision', {}).get("available_actions", [concept]),
                            "bandit_result": getattr(self, '_last_bandit_decision', {}).get("bandit_result", None),
                            "mastery_params": getattr(self, '_last_bandit_decision', {}).get("mastery_params", {}),
                            "context": getattr(self, '_last_bandit_decision', {}).get("context", {}),
                            "policy": final_state.get("policy", "adaptive")
                        },
                        "bandit": {
                            "policy": final_state.get("policy", "adaptive"),
                            "reward": final_state.get("bandit_reward", 0.0),
                            "exploration": final_state.get("bandit_exploration", False)
                        },
                        "processing": {
                            "mode": "write",
                            "time": final_state.get("processing_time", 0.0)
                        }
                    }
                    
                    self._trace_repo.save_trace(event_id, user_id, concept, trace_data, experiment_id="production")
                
                return result
            
            finally:
                # 🔒 CRITICAL: Always release lock
                if self._idempotency_manager is not None:
                    self._idempotency_manager.release_lock(event_id)
        else:
            raise RuntimeError(
                f"process_event(mode={mode!r}) is not a canonical mode in FINAL runtime. "
                f"Only mode='read' and mode='write' are implemented (Phase 14g Slice 0a). "
                f"Previously, mode='simulation' fell through to a non-authoritative read-style "
                f"path with synthetic learner insights — that was a fake-live placeholder per "
                f"the Semantic Honesty Law and has been removed. For shadow comparison or "
                f"experiment isolation, use ReplayEngine via /v3/experiments/.../replay "
                f"(see Slice 4c) with explicit deterministic_config and the canonical 'read' "
                f"or 'write' modes."
            )
        
        # 🔥 PURE CANONICAL: No learner insights - use only database state
        # This ensures deterministic, reproducible read operations
        
        # 🔥 CANONICAL STATE: Return ONLY the stored state (no recomputation!)
        state_key = f"{user_id}_{concept}"
        
        # ✅ FIXED: Check if canonical state exists in Postgres repository
        try:
            # 🔥 CRITICAL: Track canonical state reads
            UnifiedLearningBrain._canonical_state_reads += 1
            
            # 🔥 PHASE 4: Read canonical state from Postgres (source of truth)
            state_before = self._get_canonical_state_from_postgres(user_id, concept)

            if state_before is None:
                # Cold start: no previous state exists
                state_before = self._get_default_canonical_state()
                logger.info(f"🆕 Cold start for {user_id}/{concept}")
            else:
                logger.debug(f"📖 Retrieved existing canonical state for {user_id}/{concept}")
            state_source = "canonical" if state_before else "default_fallback"
            
            # 🔥 OBSERVABILITY: Update Prometheus metrics
            UnifiedLearningBrain.update_canonical_state_metrics()
            
            # Track state source for research validity
            if UnifiedLearningBrain._prometheus_middleware:
                UnifiedLearningBrain._prometheus_middleware.increment_learning_state_source(state_source)
        except Exception as e:
            logger.error(f"🔥 Canonical state read failed: {e}")
            raise RuntimeError(f"Canonical state missing for {state_key} - read-only invariant violated")
        
        canonical_state = state_before

        # 🔥 PURE CANONICAL: Use ONLY Postgres state - no learner objects
        # This ensures deterministic, reproducible read operations
        state_key = f"{user_id}_{concept}"
        
        # Extract values directly from canonical state
        lyapunov_mastery = canonical_state.get("lyapunov_mastery", 0.3)
        bayesian_alpha = canonical_state.get("bayesian_alpha", 3.0)
        bayesian_beta = canonical_state.get("bayesian_beta", 7.0)
        bayesian_mastery = bayesian_alpha / (bayesian_alpha + bayesian_beta) if (bayesian_alpha + bayesian_beta) > 0 else 0.3
        kalman_mastery = canonical_state.get("kalman_mastery", 0.3)
        
        # 🔥 FIXED: Use adaptive JT ensemble weights instead of hardcoded equal weights
        if hasattr(self, 'jt_ensemble') and self.jt_ensemble:
            ensemble_weights = self.jt_ensemble.get_weights()
            ensemble_mastery = (
                ensemble_weights.get("lyapunov", 0.33) * lyapunov_mastery +
                ensemble_weights.get("bayesian", 0.33) * bayesian_mastery +
                ensemble_weights.get("kalman", 0.34) * kalman_mastery
            )
        else:
            # Fallback to equal weights if jt_ensemble not available
            ensemble_mastery = (
                lyapunov_mastery + 
                bayesian_mastery +
                kalman_mastery
            ) / 3
        

        # F-017: read persisted uncertainty or derive from estimator disagreement
        _read_uncertainty = canonical_state.get("uncertainty")
        _read_ensemble_variance = canonical_state.get("ensemble_variance")
        if _read_uncertainty is None or _read_ensemble_variance is None:
            _vals = [lyapunov_mastery, bayesian_mastery, kalman_mastery]
            _mean = sum(_vals) / len(_vals)
            _read_ensemble_variance = sum((x - _mean) ** 2 for x in _vals) / len(_vals)
            _read_uncertainty = _read_ensemble_variance
        _read_confidence = canonical_state.get(
            "confidence", max(0.0, 1.0 - min(float(_read_uncertainty), 1.0))
        )
        
        return build_learning_result({
            # Core learning state
            "mastery": ensemble_mastery,
            "uncertainty": float(_read_uncertainty),
            "confidence": float(_read_confidence),
            
            # 🔥 PURE CANONICAL STATE: Use ONLY Postgres - no Redis/learner mixing
            # Ensures deterministic, reproducible read operations
            "lyapunov_mastery": canonical_state.get("lyapunov_mastery", 0.3),
            "bayesian_alpha": canonical_state.get("bayesian_alpha", 3.0),
            "bayesian_beta": canonical_state.get("bayesian_beta", 7.0),
            "kalman_mastery": canonical_state.get("kalman_mastery", 0.3),
            "kalman_covariance": canonical_state.get("kalman_covariance", 0.1),

            # 🔥 CONTROL: JT-attributed ensemble weights (adaptive, not static)
            "ensemble_weights": self.jt_ensemble.get_weights(),
            "ensemble_variance": float(_read_ensemble_variance),

            # Policy information
            "policy": "adaptive_learning",
            "policy_multiplier": 1.0,
            
            # Transfer information
            "transfer_amounts": {},
            "transfer_efficiency": 0.0,
            
            # ZPD alignment
            "zpd_target": ensemble_mastery + 0.1,
            "zpd_alignment_error": 0.1,
            "zpd_score": 0.8,
            
            # Metadata
            "timestamp": timestamp,
            "processing_mode": "read",
            # 🔥 CRITICAL: Load mastery_delta from DB for API consistency
            "mastery_delta": canonical_state.get("mastery_delta", 0.0),
            "zpd_delta_signal": canonical_state.get("zpd_delta_signal", 0.0),
            "processing_time": canonical_state.get("processing_time", 0.0),
            
            # 🔥 OBSERVABILITY: Track data source for research validity
            "state_source": state_source
        })
    
    def _read_mode(self, user_id: str, concept: str, interaction: Dict[str, Any], timestamp: datetime, event_id: str, interaction_id: str, write_enabled: bool = True) -> LearningResult:
        """READ mode: Get current state without updates"""
        
        # Define state_key for error handling
        state_key = f"{user_id}_{concept}"
        
        # 🔥 PURE CANONICAL: No Redis/learner access in read mode
        # This ensures complete determinism and reproducibility
        
        # 🔥 CRITICAL: Use repository pattern ONLY (no Redis fallbacks)
        # This method should be called with actual user_id and concept parameters
        # NOT with a parsed state_key
        try:
            # 🔥 NEW: Use repository pattern with lazy hydration ONLY
            if hasattr(self, '_learning_state_repo') and self._learning_state_repo:
                # NOTE: This method is called from _read_mode with user_id and concept
                # We should use those parameters directly, not parse from state_key
                # But for now, extract from method context or use a different approach
                # TODO: Pass user_id and concept as parameters to this method
                
                # For now, use the existing _get_canonical_state_from_postgres method
                # which handles the repository correctly
                canonical_state = self._get_canonical_state_from_postgres(user_id, concept)
                
                if canonical_state:
                    mastery = canonical_state.get("mastery", 0.3)
                    state_source = "canonical"
                else:
                    # No state found - this is expected for new users
                    mastery = 0.3
                    state_source = "default_fallback"
            else:
                # Fallback to default if repository not available
                mastery = 0.3
                state_source = "default_fallback"
                
        except Exception as e:
            mastery = 0.3
            state_source = "error_fallback"
        
        # 🔥 CRITICAL: Build and return LearningResult from canonical state
        canonical_state = canonical_state or {}
        
        return build_learning_result({
            "mastery": canonical_state.get("mastery", mastery),
            "uncertainty": canonical_state.get("uncertainty", 0.2),
            "confidence": canonical_state.get("confidence", 0.8),

            "lyapunov_mastery": canonical_state.get("lyapunov_mastery", mastery),
            "bayesian_alpha": canonical_state.get("bayesian_alpha", 3.0),
            "bayesian_beta": canonical_state.get("bayesian_beta", 7.0),
            "kalman_mastery": canonical_state.get("kalman_mastery", mastery),
            "kalman_covariance": canonical_state.get("kalman_covariance", 0.1),

            # 🔥 CONTROL: JT-attributed ensemble weights (adaptive, not static)
            "ensemble_weights": self.jt_ensemble.get_weights(),
            "ensemble_variance": 0.02,

            "policy": "read",
            "policy_multiplier": 1.0,

            "transfer_amounts": canonical_state.get("transfer_amounts", {}),
            "transfer_efficiency": canonical_state.get("transfer_efficiency", 0.0),

            "zpd_target": canonical_state.get("zpd_target", mastery),
            "zpd_alignment_error": canonical_state.get("zpd_alignment_error", 0.0),
            "zpd_score": canonical_state.get("zpd_score", 0.8),
            "zpd_delta_signal": canonical_state.get("zpd_delta_signal", 0.0),

            "timestamp": timestamp.isoformat(),
            "processing_mode": "read",
            "processing_time": 0.0,

            # 🔥 CRITICAL: Include mastery_delta from stored state
            "mastery_delta": canonical_state.get("mastery_delta", 0.0),
            
            # 🔥 OBSERVABILITY: Track data source for research validity
            "state_source": state_source
        })
    
    def _write_mode(self, user_id: str, concept: str, interaction: Dict[str, Any], timestamp: datetime, event_id: str, interaction_id: str, write_enabled: bool = True, state_before: Optional[Dict[str, Any]] = None, event_data: Optional[Dict[str, Any]] = None) -> LearningResult:
        mode = self._resolve_experiment_mode(user_id, event_data)
        
        """WRITE mode: Full update (for consumer) with distributed system safety"""
        
        
        # 🔬 USE PASSED state_before (critical for research validity)
        # This ensures accurate delta measurement without race conditions
        if state_before is None:
            state_before = self._get_canonical_state_from_postgres(user_id, concept) if self._learning_state_repo else {}
        
        # 🔥 BULLETPROOF: Initialize mastery_context to prevent UnboundLocalError
        mastery_context = {}
        
        # 🔥 CRITICAL: Event identity already provided by process_event
        
        # 🔥 CRITICAL: Initialize ALL variables at method start to prevent scope issues
        # These are used throughout the method and must be available in all code paths
        true_mastery_before = 0.3
        raw_lyapunov = 0.3
        raw_bayesian = 0.3
        raw_kalman = 0.3
        # 🔥 FIX F-027: Read alpha/beta from state_before (canonical state) instead of hardcoding 3.0, 7.0
        # This allows cumulative Bayesian updates instead of resetting to prior each time
        alpha = state_before.get("bayesian_alpha", 3.0)
        beta = state_before.get("bayesian_beta", 7.0)
        bayesian_mastery = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.3
        kalman_mastery = 0.3
        confidence_adjusted_mastery = 0.3
        
        # 🔥 CRITICAL: Calculate η(t) at TOP to make it CAUSAL
        # Use current state to estimate energy for adaptive calculation
        current_mastery = true_mastery_before
        
        # Get behavioral signals
        try:
            response_time = interaction.get('response_time', 10.0) if interaction else 10.0
            is_correct = interaction.get('correct', False) if interaction else False
        except AttributeError as e:
            logger.error(f"❌ interaction.get() failed: {e}, interaction type: {type(interaction)}")
            response_time = 10.0
            is_correct = False
        
        # Initialize eta with default value - will be updated with computed adaptive value later
        eta = 0.11  # Default fallback
        computed_eta = None
        # 🔥 CAUSAL MEASUREMENT VARIABLES - Initialize before any try blocks
        true_transfer_contribution = 0.0
        direct_learning_gain = 0.0
        enhanced_learning_gain = 0.0
        baseline_mastery_after = true_mastery_before
        total_gain = 0.0
        actual_transfer_amount = 0.0
        transfer_efficiency = 0.0
        learning_velocity = 0.0
        transfer_bonus = 0.0
        J_regret = None
        transfer_amounts = {}
        actual_mastery_after = 0.3
        unified_mastery_change = 0.0
        policy_multiplier = 1.0
        cost = 0.0
        actual_reward = 0.0
        optimal_reward = 1.0
        meaningful_pseudo_regret = 0.0
        
        # DEFENSIVE: Ensure interaction has required fields
        if interaction is None:
            logger.error(f"❌ CRITICAL: interaction is None for event {event_id}")
            interaction = {"correct": True, "response_time": 10.0}  # Fallback
        elif isinstance(interaction, dict):
            interaction = dict(interaction)  # Don't mutate original
            interaction.setdefault("user_id", user_id)
            interaction.setdefault("concept", concept)
        
        learning_transfer_bonus = 0.0
        
        # 🔥 BULLETPROOF: Initialize in-memory state for atomic writes (DB READ = SEED ONLY!)
        # Load previous state as seed for incremental learning
        previous_state = self._learning_state_repo.get_state(user_id, concept) if self._learning_state_repo else None
        
        if previous_state:
            canonical_data = previous_state
        else:
            # 🔥 INDIVIDUALIZED COLD-START PRIOR (Yudelson, Koedinger & Gordon 2013):
            # seed the Bayesian learner's Beta from this concept's population
            # posterior instead of a flat generic prior. The Bayesian learner
            # reads bayesian_alpha/bayesian_beta straight out of this dict
            # (bayesian_learner.py:27), so seeding here individualizes the very
            # first prediction. Falls back to the legacy generic seed (mean 0.30)
            # when the concept has too few population observations. Kalman/Lyapunov
            # and the top-level mastery are seeded to the same population mean so
            # the whole cold-start ensemble read-out is grounded and internally
            # consistent. Validated in COLDSTART_BEAT_BKT_2026-06-05.md.
            cs_alpha, cs_beta, cs_pop_mean, cs_n_obs = self._individualized_cold_start_prior(concept)
            cs_mastery = cs_alpha / (cs_alpha + cs_beta) if (cs_alpha + cs_beta) > 0 else 0.3
            canonical_data = {
                "mastery": cs_mastery,
                "uncertainty": 0.2,
                "lyapunov_mastery": cs_mastery,
                "bayesian_alpha": cs_alpha,
                "bayesian_beta": cs_beta,
                "kalman_mastery": cs_mastery,
                "kalman_covariance": 0.1,  # Cold start prior for Kalman
                "timestamp": time.time()
            }
        
        # Create multi-concept working state (in-memory only)
        working_state = MultiConceptWorkingState(concept, canonical_data)
        
        # 🔥 ENHANCED: Use advanced layers for 25+ layer system
        
        # Layer 13: Signal Processing Weights
        signals = {}
        if self.signal_extractor:
            signals = self.signal_extractor.extract_learning_signal(interaction)
            if signals is None:
                signals = {}
            else:
                pass
        
        # Layer 16: Confidence-Weighted Learning
        # 🔥 RELEASE HANDBRAKE: Use adaptive confidence-weighted learning
        if self.confidence_learner:
            signal_mapping = {
                'confidence': interaction.get('confidence', 0.8),
                'data_source': interaction.get('data_source', 'direct'),
            }
            confidence_result = self.confidence_learner.update_mastery_with_confidence(
                current_mastery=true_mastery_before,
                is_correct=interaction.get('correct', False),
                response_time=interaction.get('response_time', 10.0),
                signal_mapping=signal_mapping,
                adaptive_eta=eta,
            )
            if confidence_result is None:
                logger.error(f"❌ confidence_result is None for event {event_id}")
                confidence_result = {}
            mastery_change = confidence_result.get('mastery_change', 0.05 if interaction.get('correct', False) else -0.02)
            confidence_adjusted_mastery = mastery_change
            effective_rate = eta  # 🔥 USE OUR CAUSAL η(t), NOT confidence result!
        else:
            # Fallback to hardcoded behavior only if confidence learner unavailable
            mastery_change = 0.05 if interaction.get('correct', False) else -0.02
            confidence_adjusted_mastery = mastery_change
            effective_rate = 0.08
            
            # This section moved to the adaptive learning rate implementation above
        
        # Layer 14.5: Bandit Selection Weights
        bandit_score = None  # Will be set by bandit calculation
        if self.bandit:
            try:
                # Get current ensemble mastery from actual working state
                current_mastery = working_state.get(concept, "mastery", 0.3)
                
                # 🔥 PRODUCTION: Build candidates list for bandit with related concepts
                candidates = [{"concept_id": concept}]  # Start with current concept
                
                # Add related concepts from K-12 dependencies for multi-armed bandit
                if self.transfer_engine:
                    try:
                        deps = self.transfer_engine.get_dependencies(concept)
                        # 🔥 PHASE 3 FIX: Increase from deps[:3] to deps[:10] to reduce candidate bottleneck
                        # Top-3 truncation was too aggressive for sparse K-12 DAG branching
                        for i, dep in enumerate(deps[:10]):  # Limit to top 10 related concepts
                            candidates.append({"concept_id": dep.target_concept})
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                else:
                    pass
                
                # 🔥 BULLETPROOF: Working state already handles all concepts - no need for separate canonical state creation

                # 🔥 PRODUCTION: Build mastery_context from REAL learner states
                mastery_context = {}
                if self.learner_factory:
                    try:
                        # Get real mastery from Lyapunov learner for all relevant concepts
                        lyapunov_learner = self.learner_factory.get("lyapunov")
                        
                        # Build mastery context for all concepts in candidates
                        for candidate in candidates:
                            concept_id = candidate.get("concept_id", concept)
                            

                            # 🔥 BULLETPROOF: Use multi-concept working state for bandit context (no DB reads!)
                            try:
                                # Get mastery from appropriate concept's working state
                                concept_mastery = working_state.get(concept_id, "mastery", 0.3)
                                mastery_context[concept_id] = concept_mastery

                            except Exception as e:
                                logger.error(f"❌ Failed to get mastery for {concept_id}: {e}")
                                # Last resort fallback
                                concept_mastery = 0.3
                                mastery_context[concept_id] = concept_mastery
                        
                        # Validate current concept mastery
                        current_mastery = mastery_context.get(concept, None)
                        if current_mastery is None:
                            raise RuntimeError(f"Canonical state invariant violated: Missing mastery for {concept}")
                        
                    except Exception as e:
                        logger.error(f"❌ CRITICAL: Failed to build mastery context: {e}")
                        raise RuntimeError(f"Canonical state invariant violated: Cannot build mastery context - {e}")
            except Exception as e:
                logger.warning(f" Failed to build mastery context: {e}")
                raise RuntimeError(f"Canonical state invariant violated: Cannot build mastery context - {e}")

        # 🔥 FIXED: Canonical state already ensured above

        # FIXED: Use correct bandit method signature with REAL mastery context
        if self.bandit:
            pass

        try:
            # 🔥 FIX F-027: Build mastery_params from actual learner state, not reconstructed from mastery
            mastery_params = {}
            for concept_id, mastery in mastery_context.items():
                # Get actual Bayesian alpha/beta from working state for ALL concepts
                concept_working_state = working_state.get_concept(concept_id)
                alpha = concept_working_state.get("bayesian_alpha", 3.0)
                beta = concept_working_state.get("bayesian_beta", 7.0)
                mastery_params[concept_id] = (alpha, beta)
            
            # 🔥 BULLETPROOF: Ensure no None values in bandit parameters
            for concept_id in mastery_params:
                alpha, beta = mastery_params[concept_id]
                mastery_params[concept_id] = (alpha if alpha is not None else 3.0, beta if beta is not None else 7.0)

            # Build representation_params (default)
            representation_params = {concept_id: (1.0, 1.0) for concept_id in mastery_context.keys()}

            # Build difficulty_map (default)
            difficulty_map = {concept_id: 0.5 for concept_id in mastery_context.keys()}

            # 🔥 CRITICAL: Add deterministic bandit seeding for replay correctness
            context = {
                'correct': interaction.get('correct', True),
                'response_time': interaction.get('response_time', 10.0),
                'event_id': event_id,  # Seed bandit with event_id for determinism
                'interaction_id': interaction_id
            }

            
            # 🔥 DETERMINISTIC: Seed bandit with event_id for reproducibility
            if hasattr(self.bandit, 'set_seed'):
                # Create deterministic seed from event_id
                seed = hash(event_id) % (2**31)  # Convert to 31-bit integer
                self.bandit.set_seed(seed)
                logger.info(f"🔥 Seeded bandit with event_id {event_id} -> seed {seed}")
            
            bandit_result = self.bandit.select_arm(
                user_id=user_id,
                available_nodes=list(mastery_context.keys()),
                mastery_params=mastery_params,
                representation_params=representation_params,
                difficulty_map=difficulty_map,
                context=context
            )

            # 🔥 CAPTURE BANDIT DECISION CONTEXT for research API
            # Store full decision context for debugging and analysis
            self._last_bandit_decision = {
                "selected_action": concept,
                "available_actions": list(mastery_context.keys()),
                "bandit_result": bandit_result,
                "mastery_params": mastery_params,
                "context": context,
                "timestamp": timestamp.isoformat()
            }

            # 🔥 CRITICAL: Bandit output validation to prevent catastrophic value contamination
            if isinstance(bandit_result, tuple) and len(bandit_result) >= 3:
                bandit_score = bandit_result[2]  # Third element is the score
                # Numerical safety check - NEVER allow invalid values to propagate
                if bandit_score is None or not np.isfinite(bandit_score):
                    bandit_score = 0.5
            else:
                bandit_score = 0.5


        except Exception as e:
            import traceback
            traceback.print_exc()
        
        # Layer 14: Policy Engine Weights
        # 🔥 PHASE 5: JT-aware policy selection (constitutional optimization)
        # 🔥 PHASE 6: Constitutional purification - remove hardcoded motivational priors
        policy_multiplier = 1.0  # 🔥 PHASE 6: Neutral prior (no inherent advantage)
        selected_policy = "hcie"  # Default
        if self.policy_engine:
            # 🔥 JT-AWARE POLICY SELECTION: Select policy based on expected future ΔJT
            available_policies = ["hcie", "heuristic", "static", "random"]  # Available policies
            selected_policy, expected_jt_score = self.policy_engine.select_policy_jt_aware(
                available_policies=available_policies,
                user_id=user_id,
                available_concepts=list(mastery_context.keys()),
                mastery_params=mastery_params,
                difficulty_map=difficulty_map,
                context=context
            )
            # 🔥 PHASE 6 CONSTITUTIONAL PURIFICATION: Use expected JT as multiplier
            # Old: policy_multiplier = hardcoded priors (hcie=1.12, heuristic=1.05, static=1.0, random=0.97)
            # New: policy_multiplier = expected_JT (learned from governance history)
            # This removes embedded pedagogical ideology and makes policy purely JT-driven
            if expected_jt_score != 0.0:
                # Normalize expected JT to multiplier range [0.8, 1.2] for stability
                # This is a bounded transformation, not a hardcoded prior
                # The range is small to prevent extreme swings during warm-up
                jt_multiplier = 1.0 + np.tanh(expected_jt_score * 10) * 0.2
                policy_multiplier = jt_multiplier
            else:
                # Insufficient history: use neutral prior
                policy_multiplier = 1.0

        # This will be handled after true_mastery_before is defined below

        # ✅ UNIFIED Jₜ OBJECTIVE: Replace heuristics with principled objective
        # Step 1: Compute all Jₜ terms explicitly - NORMALIZED
        delta_m = np.tanh(confidence_adjusted_mastery * policy_multiplier * bandit_score * 10)  # Normalized to [-1,1]
        
        # Step 2: Get transfer (computed later, but we'll include in Jₜ)
        # Note: learning_transfer_bonus will be calculated below
        
        # Step 3: Compute cost term (response time penalty) - NORMALIZED
        response_time = interaction.get('response_time', 10.0)
        expected_time = 10.0  # Expected response time for this difficulty
        cost = min(1.0, response_time / expected_time)  # Normalized to [0,1]
        
        # Step 4: Compute uncertainty penalty (from actual ensemble variance)
        # Get real uncertainty from current learner states
        
        # 🔥 BULLETPROOF: Calculate uncertainty from working state (no DB reads!)
        try:
            if not working_state:
                raise RuntimeError(f"Missing working state for uncertainty: {user_id}/{concept}")
            
            # Extract mastery values from main working state (no learner reads!)
            main_state = working_state.get_main_state()
            lyapunov_mastery = main_state.get("lyapunov_mastery", 0.3)
            
            # Get Bayesian alpha/beta from main working state
            bayesian_alpha = main_state.get("bayesian_alpha", 3.0)
            bayesian_beta = main_state.get("bayesian_beta", 7.0)
            bayesian_mastery = bayesian_alpha / (bayesian_alpha + bayesian_beta) if (bayesian_alpha + bayesian_beta) > 0 else 0.3
            
            # Get Kalman mastery from main working state
            kalman_mastery = main_state.get("kalman_mastery", 0.3)
            
            # Calculate ensemble variance (learner disagreement)
            # This is the uncertainty measure used in JT governance
            ensemble_values = [lyapunov_mastery, bayesian_mastery, kalman_mastery]
            ensemble_mean = sum(ensemble_values) / len(ensemble_values)
            ensemble_variance = sum((x - ensemble_mean) ** 2 for x in ensemble_values) / len(ensemble_values)

            # F-033: when ensemble collapses (F-016 deferred), use Beta posterior variance for JT U-channel
            from core.mastery.mastery_model import MasteryModel
            if ensemble_variance < 1e-8:
                _bayes_var = MasteryModel.variance(bayesian_alpha, bayesian_beta)
                uncertainty = max(ensemble_variance, _bayes_var)
                ensemble_variance = uncertainty
            else:
                uncertainty = ensemble_variance

            # F-017: persist uncertainty on working state for batch write / trajectory
            _main_for_u = working_state.get_main_state()
            _main_for_u.set("uncertainty", uncertainty)
            _main_for_u.set("ensemble_variance", ensemble_variance)
            _main_for_u.set("confidence", max(0.0, 1.0 - min(float(uncertainty), 1.0)))
            
        except Exception as e:
            logger.error(f"🔥 UNCERTAINTY CALCULATION FAILED: {e}")
            raise RuntimeError(f"Working state required for uncertainty calculation: {e}")
        
        # Step 5: Calculate ZPD as DELTA error signal (not state variable)
        # 🔥 CRITICAL FIX: Convert from state reward to delta signal
        concept_difficulty = self._lookup_concept_difficulty(concept)
        current_mastery = true_mastery_before  # Use current mastery for delta calculation
        
        # 🔥 CONTROL: JT-driven adaptive η(t)
        # η is computed to maximize expected JT on next interaction
        # Uses STATE variables (uncertainty, ZPD, mastery) to inform control decision
        if mode == "adaptive":
            # F-017: use ensemble-derived uncertainty (computed above), not hardcoded 0.2
            zpd_score = 1.0 - abs(concept_difficulty - current_mastery)  # STATE: ZPD alignment
            zpd_score = max(0.1, min(1.0, zpd_score))

            # CONTROL: Simple, brain-driven adaptive formula
            # These STATE variables inform the CONTROL decision for η
            confidence = 1.0 - uncertainty  # STATE: confidence
            stability = 1.0 / (1.0 + ensemble_variance)  # STATE: stability

            base_eta = 0.1
            computed_eta = base_eta * confidence * zpd_score * stability

            # Mastery-level adjustment (STATE-informed CONTROL)
            if current_mastery < 0.3:
                computed_eta *= 1.3  # Boost for struggling learners
            elif current_mastery > 0.7:
                computed_eta *= 0.7  # Reduce for advanced learners

            # Ensure η is within reasonable bounds
            computed_eta = max(0.01, min(0.30, computed_eta))


            # 🔥 GOVERNANCE: Validate CONTROL variables are JT-driven
            try:
                from core.learning.governance_validator import assert_no_parallel_objectives
                from core.learning.metrics_governance import record_governance_validation
                control_context = {
                    "eta": computed_eta,
                    "mode": mode,
                    "confidence": confidence,
                    "zpd_score": zpd_score,
                    "mastery": current_mastery
                }
                assert_no_parallel_objectives(control_context)
                record_governance_validation("control_validation", True)
            except ImportError:
                pass
            except AssertionError as e:
                from core.learning.metrics_governance import record_governance_validation, record_governance_violation
                record_governance_validation("control_validation", False)
                record_governance_violation("control_validation")
        else:
            # For non-adaptive modes, use fixed learning rate config
            try:
                from core.learning.learning_rate_config import get_fixed_learning_rate
                computed_eta = get_fixed_learning_rate(mode)
            except ImportError:
                # Fallback to hardcoded values
                if mode == "fixed_low":
                    computed_eta = 0.05
                elif mode == "fixed_mid":
                    computed_eta = 0.11
                elif mode == "fixed_high":
                    computed_eta = 0.20
                else:
                    computed_eta = 0.11
        
        # 🔥 Assign computed_eta to eta for use in the rest of the function
        eta = computed_eta
        
        # ZPD error signal: negative distance from optimal (delta, not state)
        # STATE: ZPD delta signal (used in JT calculation)
        zpd_error_signal = -abs(concept_difficulty - current_mastery)

        # Optional: Scale to match magnitude of other delta terms
        zpd_scaled = zpd_error_signal * 0.1  # Scale to similar range as ΔM and T


        # Step 6: We'll build Jₜ after transfer is calculated (below)
        # 🔥 JT is the TOP-LEVEL OBJECTIVE - all control decisions serve JT optimization

        # FIXED: Calculate transfers with enhanced mastery change - NORMALIZED
        transfers = {}
        deps = self.transfer_engine.get_dependencies(concept)

        # Adaptive γ(t) - closed-form ratio control
        alpha_target = 0.75  # Target direct learning ratio
        gamma_0 = 0.3  # Base transfer scaling
        
        for dep in deps:
            transfer_amount = self.transfer_engine.calculate_transfer_amount(
                source_concept=concept,
                target_concept=dep.target_concept,
                mastery_change=delta_m,
                confidence=signals.get('engagement_signal', 0.8),
                learning_gain=delta_m
            )
            
            # Store transfer amount
            transfers[dep.target_concept] = transfer_amount
            
            if transfer_amount >= self.transfer_engine.min_transfer_threshold:
                transfers[dep.target_concept] = transfer_amount
        
        learning_transfer_bonus = sum(transfers.values()) if transfers else 0.0
        
        # 🔥 FIX F-026: Removed misleading UNIFIED Jₜ weight optimization
        # The weights computed here were NOT actually used for J_t computation.
        # J_t is computed via constitutional JT governance (line 3224) which uses
        # its own internal weights and normalization. This section was causing
        # confusion and the 9-10% manual computation mismatch reported in F-026.
        # 
        # For F-026 fix: We now use placeholder weights for logging purposes only,
        # but the actual J_t computation happens in the constitutional JT section.
        w1, w2, w3, w4, w5, w6 = 0.17, 0.17, 0.17, 0.17, 0.17, 0.15  # 6D balanced placeholder weights

        # 🔥 CONSTITUTIONAL JT (Jₜ): Principled decomposition, not heuristic aggregation
        # See JT_GOVERNANCE_CONSTITUTION.md for constitutional semantics
        #
        # CONSTITUTIONAL FORMULA:
        # JT = σ(w₁·N(ΔM) + w₂·N(T) + w₃·N(C) + w₄·N(U) + w₅·N(Z))
        #
        # WHERE:
        # N(·) is component normalization to [0, 1] for scale consistency
        # σ is sigmoid normalization for bounded governance
        # w₁, w₂, w₃, w₄, w₅ are adaptive weights summing to unity
        #
        # CONSTITUTIONAL PRINCIPLES:
        # 1. Multi-Objective Governance: Synthesizes five learning objectives
        # 2. Scale Consistency: All components normalized to [0, 1]
        # 3. Interpretability: Each component has clear semantic interpretation
        # 4. Temporal Stability: JT exhibits bounded temporal variation
        # 5. Adaptivity: Weights adapt to context with constitutional bounds
        #
        # MATHEMATICAL GROUNDING:
        # ΔM (Mastery Gain): Bayesian knowledge tracing (Corbett & Anderson, 1995)
        # T (Transfer Score): Analogical transfer theory (Singley & Anderson, 1989)
        # C (Challenge Score): Zone of proximal development (Vygotsky, 1978)
        # U (Uncertainty Score): Information theory (Shannon, 1948)
        # Z (ZPD Score): Zone of proximal development (Vygotsky, 1978)
        #
        # CONTROL: All adaptive behavior serves to maximize JT
        # This is the single scalar that all control decisions optimize

        governance_volatility = 0.0
        governance_exploration_pressure = 0.5
        governance_stability_index = 1.0

        # 🔥 Use constitutional JT governance if available
        if hasattr(self, 'jt_governance') and self.jt_governance is not None:
            # Extract adaptation context from event_data if provided
            adaptation_context = None
            if event_data and isinstance(event_data, dict):
                adaptation_context = event_data.get("adaptation_context")

            # PROSPECTIVE held at 0.0 in the recorded JT (5-D core path). The C2 structural-utility
            # activation was attempted then REVERTED: a leak-free bake-off (C1-C5, 3 real Junyi DAGs,
            # permuted-DAG null) + a direct redundancy test showed the only formula that "activates"
            # (C2 = fringe x depth) is REDUNDANT with concept difficulty (signal -89% when difficulty is
            # controlled; corr(depth,difficulty)=+0.26) -- i.e. it re-measures what ZPD/Challenge already
            # carry, and it misfires negative on single-parent (chain) curricula. See VALIDATION_LEDGER
            # C-PROSP-FORMULA / C-PROSP-WIRE + PROSPECTIVE_TRANSFER_DESIGN.md. The prospective estimator
            # remains available OFF this core path for candidate ranking / pre-selection
            # (estimate_prospective_transfer, called in governance_score_candidate); the 6-D scaffolding
            # (DB column, projection consumers, frontend, dormant w3 weight) is retained as a passive
            # field for future work. Same conclusion as the headline ADC finding: the topology effect is
            # real but small and mostly proximity, not separable from a difficulty / general-mastery confound.
            # Constitutional JT computation with principled decomposition (recorded path = 5-D)
            J_t, contributions = self.jt_governance.compute_jt(
                delta_m=delta_m,
                transfer_realized=learning_transfer_bonus,
                transfer_prospective=0.0,  # 5-D recorded path (C2 redundant w/ difficulty; estimator used off-path for ranking)
                challenge=cost,
                uncertainty=uncertainty,
                zpd=zpd_scaled,
                context=adaptation_context
            )

            # Compute governance metrics
            volatility = self.jt_governance.compute_volatility()
            exploration_pressure = self.jt_governance.compute_exploration_pressure()
            stability_index = self.jt_governance.compute_stability_index()
            attribution = self.jt_governance.compute_attribution(J_t, contributions)
            governance_volatility = volatility
            governance_exploration_pressure = exploration_pressure
            governance_stability_index = stability_index

            # Log governance metrics for observability

            # Enforce constitutional bounds
            self.jt_governance.enforce_constitutional_bounds()

            # Adapt weights based on context (every 10 interactions)
            if len(self.jt_governance.jt_history) % 10 == 0 and len(self.jt_governance.jt_history) > 0:
                context = {
                    "transfer_utilization": 0.5 if learning_transfer_bonus > 0 else 0.2,
                    "challenge_mismatch_rate": 0.5 if cost > 0.5 else 0.3,
                    "exploration_need": exploration_pressure,
                    "zpd_alignment_rate": 0.5 if abs(zpd_scaled) < 0.1 else 0.3
                }
                self.jt_governance.adapt_weights(stability_index, context)

        else:
            # Fallback: Legacy JT computation (heuristic aggregation, 6D)
            J_t = (
                w1 * delta_m +                  # ΔM: Direct learning gain (delta) [-1, 1]
                w2 * learning_transfer_bonus -  # T_realized: Transfer gain (delta) [0, 1]
                w3 * cost +                     # T_prospective: Dormant placeholder (0 during fallback)
                w4 * uncertainty +              # C: Challenge/Uncertainty (combined in legacy)
                w5 * zpd_scaled +               # U: Uncertainty penalty (delta) [0, 0.1]
                w6 * 0.0                        # Z: ZPD alignment (placeholder)
            )
            contributions = None
            attribution = None
        
        # 🔥 CRITICAL: J_t safety clamp - prevent infinite/NaN propagation
        if not np.isfinite(J_t):
            J_t = 0.0

        # 🔥 GOVERNANCE: Validate JT centrality (governance validation)
        try:
            from core.learning.governance_validator import assert_jt_central
            from core.learning.metrics_governance import record_governance_validation
            assert_jt_central({"J_value": J_t})
            record_governance_validation("jt_centrality", True)
        except ImportError:
            pass
        except AssertionError as e:
            from core.learning.metrics_governance import record_governance_validation, record_governance_violation
            record_governance_validation("jt_centrality", False)
            record_governance_violation("jt_centrality")

        # 🔥 CONSTITUTIONAL GOVERNANCE: Log governance metrics for trajectory recording
        if hasattr(self, 'jt_governance') and self.jt_governance is not None:
            try:
                governance_metrics = self.jt_governance.get_governance_metrics()

                # Log to research_logger for trajectory recording
                if research_logger:
                    research_logger.log(
                        entry_type="governance_metrics",
                        data={
                            "user_id": user_id,
                            "concept": concept,
                            "interaction_number": len(self.jt_governance.jt_history),
                            "jt_value": J_t,
                            "weights": governance_metrics.get("weights", {}),
                            "volatility": governance_metrics.get("volatility", 0.0),
                            "exploration_pressure": governance_metrics.get("exploration_pressure", 0.0),
                            "stability_index": governance_metrics.get("stability_index", 0.0),
                            "jt_history_length": governance_metrics.get("jt_history_length", 0),
                            "attribution": attribution if attribution else None,
                            "components": contributions if contributions else None
                        }
                    )
            except Exception as e:
                logger.warning(f"⚠️ Failed to log governance metrics: {e}")

        # 🔥 PHASE 5: Record policy JT outcome (for JT-aware policy selection)
        if self.policy_engine:
            try:
                self.policy_engine.record_policy_jt(selected_policy, J_t)
            except Exception as e:
                pass

        # 🔥 CONTROL: Record learner contributions to JT (JT-attributed ensemble)
        try:
            # Get learner masteries from working state
            main_state = working_state.get_main_state()
            lyapunov_mastery = main_state.get("lyapunov_mastery", 0.3)
            bayesian_alpha = main_state.get("bayesian_alpha", 3.0)
            bayesian_beta = main_state.get("bayesian_beta", 7.0)
            bayesian_mastery = bayesian_alpha / (bayesian_alpha + bayesian_beta) if (bayesian_alpha + bayesian_beta) > 0 else 0.3
            kalman_mastery = main_state.get("kalman_mastery", 0.3)

            # Record each learner's contribution to JT
            self.jt_ensemble.record_learner_contribution("lyapunov", J_t, lyapunov_mastery)
            self.jt_ensemble.record_learner_contribution("bayesian", J_t, bayesian_mastery)
            self.jt_ensemble.record_learner_contribution("kalman", J_t, kalman_mastery)

            # 🔥 CONTROL: Update ensemble weights periodically (temporal separation)
            # Update every 10 interactions to respect slow update frequency
            total_contributions = sum(len(contribs) for contribs in self.jt_ensemble.jt_contributions.values())
            if total_contributions > 0 and total_contributions % 10 == 0:
                new_weights = self.jt_ensemble.update_weights()
        except Exception as e:
            logger.warning(f"⚠️ JT-attributed ensemble update failed: {e}")

        # 🔥 CONTROL: Update bandit with JT (JT-native reinforcement)
        # This makes exploration governance-native - bandit learns from actual JT
        try:
            if self.bandit is None:
                pass
            elif not hasattr(self.bandit, 'update_with_objective'):
                pass
            else:
                bandit_arm = f"{user_id}:{concept}"
                # Use variables that are guaranteed to be defined at this point
                # Some variables (confidence, zpd_score) may not be defined in all code paths
                bandit_context = {
                    "mastery": current_mastery if 'current_mastery' in locals() else true_mastery_before,
                    "uncertainty": uncertainty if 'uncertainty' in locals() else 0.2,
                    "confidence": confidence if 'confidence' in locals() else 0.8,
                    "zpd_score": zpd_score if 'zpd_score' in locals() else 1.0,
                    "J_t": J_t
                }
                self.bandit.update_with_objective(user_id, concept, J_t, bandit_context)
        except Exception as e:
            logger.warning(f"⚠️ Bandit JT update failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 8: Apply adaptive learning rate and update
        # 🔥 CRITICAL: Use TRUE ADAPTIVE η(t) calculated at method start
        # DO NOT recalculate eta here - use our causal η(t) from confidence-based calculation
        # adaptive_rate and effective_learning_rate are already set to our η(t) above
        
        # Calculate current energy for constraint enforcement (using J_t as proxy)
        current_energy = abs(J_t) + abs(learning_transfer_bonus)
        
        # 🔥 PRESERVE TRUE ADAPTIVE η(t) - DO NOT OVERRIDE!
        # eta, adaptive_rate, effective_learning_rate already set from confidence-based calculation
        
        unified_mastery_change = eta * J_t
        
        # Apply adaptive γ(t) - closed-form ratio control (after eta is defined)
        current_alpha = abs(unified_mastery_change) / (abs(unified_mastery_change) + abs(learning_transfer_bonus) + 1e-6)
        gamma = gamma_0 * (alpha_target / (current_alpha + 1e-6))
        gamma = max(0.1, min(0.5, gamma))  # Stability clamp
        
        # Apply adaptive scaling to transfer
        learning_transfer_bonus *= gamma
        
        
        # 🔥 HARD CONSTRAINT ENFORCEMENT - Project back into constraint manifold
        # Recalculate energy after adaptive controls
        E_t = abs(unified_mastery_change) + abs(learning_transfer_bonus)
        
        # Enforce minimum energy constraint
        if E_t < 0.01:
            scale_factor = 0.01 / E_t
            unified_mastery_change *= scale_factor
            learning_transfer_bonus *= scale_factor
            # Record constraint violation
            try:
                from core.learning.metrics import record_energy_violation
                record_energy_violation("energy_minimum")
            except ImportError:
                pass
        
        # Enforce maximum energy constraint
        elif E_t > 0.05:
            scale_factor = 0.05 / E_t
            unified_mastery_change *= scale_factor
            learning_transfer_bonus *= scale_factor
            # Record constraint violation
            try:
                from core.learning.metrics import record_energy_violation
                record_energy_violation("energy_maximum")
            except ImportError:
                pass
        
        # Recalculate alpha after energy scaling
        alpha_final = abs(unified_mastery_change) / (abs(unified_mastery_change) + abs(learning_transfer_bonus) + 1e-6)
        
        # Enforce alpha constraint (direct learning dominance)
        if alpha_final > 0.85:
            # Too much direct learning - increase transfer
            transfer_scale = alpha_final / 0.75
            learning_transfer_bonus *= transfer_scale
            # Record constraint violation
            try:
                from core.learning.metrics import record_energy_violation
                record_energy_violation("alpha_excessive")
            except ImportError:
                pass
        elif alpha_final < 0.70:
            # Too much transfer - decrease transfer
            transfer_scale = alpha_final / 0.75
            learning_transfer_bonus *= transfer_scale
            # Record constraint violation
            try:
                from core.learning.metrics import record_energy_violation
                record_energy_violation("alpha_insufficient")
            except ImportError:
                pass
        
        # Final energy check and adjustment if needed
        E_final = abs(unified_mastery_change) + abs(learning_transfer_bonus)
        alpha_final = abs(unified_mastery_change) / (abs(unified_mastery_change) + abs(learning_transfer_bonus) + 1e-6)
        
        
        # 🔥 CRITICAL: Mastery update guard - prevent numerical contamination
        if not np.isfinite(unified_mastery_change):
            unified_mastery_change = 0.0
        
        # For compatibility with existing code, set enhanced_mastery_change to unified value
        enhanced_mastery_change = unified_mastery_change
        
        # Layer 19-22: Performance Tracking
        self.total_interactions += 1
        if interaction.get('correct', False):
            self.learning_regret += (1.0 - (0.3 + enhanced_mastery_change))
        else:
            self.decision_regret += 0.3
        self.cumulative_regret = self.learning_regret + self.decision_regret
        
        
        # 🔥 SHADOW CAUSAL MODE - Execute BEFORE recursive update
        causal_valid = False
        
        try:
            # 🔥 CRITICAL FIX: True signal separation
            # Direct learning gain (learners only, no policy/bandit/transfer)
            direct_learning_gain = enhanced_mastery_change / (policy_multiplier if 'policy_multiplier' in locals() else 1.0)
            
            # Enhanced learning gain (includes policy + bandit effects)
            enhanced_learning_gain = enhanced_mastery_change
            
            # 🔥 CORRECTED: TRUE baseline mastery (direct learning only)
            baseline_mastery_after = true_mastery_before + direct_learning_gain
            
            # Get actual final state (includes ALL effects)
            # actual_mastery_after is already computed above
            
            # 🔥 CRITICAL FIX: Correct transfer attribution by direction
            # Total gain from before to after
            total_gain = actual_mastery_after - true_mastery_before
            
            # Get actual transfer amount from transfer engine
            actual_transfer_amount = sum(transfer_amounts.values()) if transfer_amounts else 0.0
            
            # 🔥 TRANSFER EFFICIENCY: Transfer contribution as proportion of total gain
            if abs(total_gain) > 1e-6:
                transfer_efficiency = actual_transfer_amount / abs(total_gain)
            else:
                transfer_efficiency = 0.0
            
            # 🔥 TRANSFER CONTRIBUTION: Actual transfer effect (not just potential)
            true_transfer_contribution = actual_transfer_amount
            
            # Step 1: Learning velocity (mastery change per interaction)
            if enhanced_mastery_change > 0:
                learning_velocity = enhanced_mastery_change
            else:
                learning_velocity = 0.0
            
            # Step 2: Transfer efficiency (transfer as multiplier of learning)
            # Transfer should amplify learning, not dominate it
            if direct_learning_gain > 0.001:
                transfer_multiplier = 1.0 + (true_transfer_contribution / direct_learning_gain)
                transfer_bonus = min(0.5, (transfer_multiplier - 1.0) * 0.5)  # Cap at 50% bonus
            else:
                transfer_bonus = 0.0
            
            J_regret = None  # Will be computed separately for evaluation
            
            # 🔥 METRICS LAYER: Variables are now properly defined
            
            causal_valid = True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Continue execution - DON'T fail the system
        
        # Store causal validity for API response
        self._last_causal_valid = causal_valid


        # ✅ UNIFIED Jₜ: Use recursive state update (no baseline reset)
        # Get previous mastery from canonical state or use baseline
        state_key = f"{user_id}_{concept}"
        previous_mastery = 0.3  # Default baseline
        
        try:
            if hasattr(self._canonical_state_store, 'get_value'):
                # Redis case
                previous_data = self._canonical_state_store.get_value(state_key)
                if previous_data:
                    previous_state = json.loads(previous_data)
                    previous_mastery = previous_state.get("mastery", 0.3)
            elif isinstance(self._canonical_state_store, dict):
                # Local dictionary case
                previous_state = self._canonical_state_store.get(state_key, {"mastery": 0.3})
                previous_mastery = previous_state.get("mastery", 0.3)
        except Exception as e:
            previous_mastery = 0.3
        
        # Apply unified Jₜ update recursively with numerical safety
        mastery_update = previous_mastery + enhanced_mastery_change
        # 🔥 CRITICAL: Final safety check before mastery update
        if not np.isfinite(mastery_update):
            actual_mastery_after = previous_mastery
        else:
            actual_mastery_after = min(1.0, max(0.0, mastery_update))
        
        # 🔥 DEFERRED: Create LearningResult after canonical-derived values are computed
        
        # 🔥 FIXED: Use the real transfers dict, not overwrite it
        transfer_amounts = transfers.copy()  # Use the actual target concepts!
        
        if learning_transfer_bonus > 0:
            transfer_amounts["total_transfer"] = learning_transfer_bonus
            
        
        # 🔥 FIXED: Update mastery tracking for transfer efficiency calculation
        key = f"{user_id}_{concept}"
        if not hasattr(self, '_last_mastery'):
            self._last_mastery = {}
        if not hasattr(self, '_last_mastery_change'):
            self._last_mastery_change = {}
        
        # Store the actual mastery after transfer
        self._last_mastery[key] = actual_mastery_after
        
        # Store the actual mastery change from enhanced learning
        if enhanced_mastery_change > 0.001:
            self._last_mastery_change[key] = enhanced_mastery_change
        else:
            # Use enhanced mastery change as fallback
            self._last_mastery_change[key] = enhanced_mastery_change if 'enhanced_mastery_change' in locals() else 0.0
        
        # 🔥 BULLETPROOF: Add null safety helper
        def safe_float(x, default=0.0):
            return float(x) if x is not None else default
        
        # 🔥 PREPARE DEFAULT STATE (define before metrics layer)
        # This ensures updated_state is always available
        # Compute uncertainty as ensemble variance (per formal specification)
        # U = variance([lyapunov_mastery, bayesian_mastery, kalman_mastery])
        computed_ensemble_variance = ensemble_variance if 'ensemble_variance' in locals() else 0.02
        computed_uncertainty = computed_ensemble_variance  # Uncertainty = ensemble variance

        # 🔥 FIX: Calculate ensemble mastery BEFORE build_learning_result to avoid circular dependency
        # Get individual learner masteries from canonical state
        raw_lyapunov = 0.3
        raw_bayesian = 0.3
        raw_kalman = 0.3
        alpha = 3.0
        beta = 7.0
        
        if canonical_data:
            raw_lyapunov = canonical_data.get("lyapunov_mastery", 0.3)
            alpha = canonical_data.get("bayesian_alpha", 3.0)
            beta = canonical_data.get("bayesian_beta", 7.0)
            raw_bayesian = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.3
            raw_kalman = canonical_data.get("kalman_mastery", 0.3)
        
        # Calculate ensemble mastery using adaptive weights
        if hasattr(self, 'jt_ensemble') and self.jt_ensemble:
            ensemble_weights = self.jt_ensemble.get_weights()
            ensemble_mastery = (
                ensemble_weights.get("lyapunov", 0.33) * raw_lyapunov +
                ensemble_weights.get("bayesian", 0.33) * raw_bayesian +
                ensemble_weights.get("kalman", 0.34) * raw_kalman
            )
        else:
            # Fallback to equal weights
            ensemble_mastery = (raw_lyapunov + raw_bayesian + raw_kalman) / 3.0
            ensemble_weights = {"lyapunov": 0.33, "bayesian": 0.33, "kalman": 0.34}

        # NOTE: V2-causal fusion is applied ONCE at the governing post-update site (search
        # "V2-causal: canonical mastery"); this pre-update synthesis is overwritten there.
        # Use ensemble mastery instead of recursive update
        actual_canonical_mastery = ensemble_mastery

        updated_state = build_learning_result({
            "mastery": actual_canonical_mastery,  # 🔥 Use ensemble mastery
            "uncertainty": computed_uncertainty,  # Ensemble variance from all three learners
            "confidence": 0.8,
            "lyapunov_mastery": raw_lyapunov,
            "processing_time": 0.015,
            "bayesian_alpha": alpha,
            "bayesian_beta": beta,
            "kalman_mastery": raw_kalman,
            "kalman_covariance": 0.1,
            # 🔥 CONTROL: JT-attributed ensemble weights (adaptive, not static)
            "ensemble_weights": ensemble_weights,
            "ensemble_variance": computed_ensemble_variance,  # Learner disagreement (separate from uncertainty)
            "policy": "text",  # Default policy
            "policy_multiplier": 1.0,
            "zpd_target": concept_difficulty,
            "zpd_alignment_error": abs(concept_difficulty - current_mastery),
            "zpd_score": max(0.0, 1.0 - abs(concept_difficulty - current_mastery)),  # State score for diagnostics
            "zpd_delta_signal": zpd_scaled,  # Delta signal for optimization
            "transfer_amounts": {},
            "transfer_efficiency": 0.0,
            "timestamp": timestamp.isoformat(),
            "processing_mode": "write",
            "J_value": None
        })
        
        # 🔥 METRICS LAYER: Record with TRUE CAUSAL MEASUREMENT
        try:
            # 🔥 FIX: Use repository for metrics (not Redis)
            canonical_data = self._learning_state_repo.get_state(user_id, concept)
            if not canonical_data:
                # For new users, use baseline values but still update mastery
                logger.debug(f"New user detected: {user_id}/{concept}, using baseline metrics")
                # Set baseline values for new users
                true_mastery_before = 0.3  # Cold start baseline
                raw_lyapunov = 0.3
                raw_bayesian = 0.3  # Default alpha=3, beta=7 -> 3/(3+7) = 0.3
                raw_kalman = 0.3
                # Don't return early - continue to mastery update!
            
            if canonical_data and self.learner_factory:
                # Extract mastery values from canonical state (existing users)
                try:
                    lyapunov_mastery = self.learner_factory.get("lyapunov").get_state_from_canonical(canonical_data)
                    
                    # Get Bayesian alpha/beta from canonical state
                    bayesian_alpha_beta = self.learner_factory.get("bayesian").get_state_from_canonical(canonical_data)
                    if isinstance(bayesian_alpha_beta, tuple) and len(bayesian_alpha_beta) == 2:
                        alpha, beta = bayesian_alpha_beta
                        bayesian_mastery = alpha / (alpha + beta)
                    else:
                        bayesian_mastery = 0.3  # Default
                        
                    kalman_mastery = self.learner_factory.get("kalman").get_state_from_canonical(canonical_data)[0]
                except Exception as e:
                    # 🔥 FIX F-027/F-002: Handle None canonical_data for cold start
                    if canonical_data:
                        lyapunov_mastery = canonical_data.get("lyapunov_mastery", 0.3)
                        bayesian_mastery_raw = canonical_data.get("bayesian_alpha", 3.0) / (canonical_data.get("bayesian_alpha", 3.0) + canonical_data.get("bayesian_beta", 7.0)) if (canonical_data.get("bayesian_alpha", 3.0) + canonical_data.get("bayesian_beta", 7.0)) > 0 else 0.3
                        kalman_mastery = canonical_data.get("kalman_mastery", 0.3)
                        alpha = canonical_data.get("bayesian_alpha", 3.0)
                        beta = canonical_data.get("bayesian_beta", 7.0)
                    else:
                        # Cold start fallback
                        lyapunov_mastery = 0.3
                        bayesian_mastery = 0.3
                        kalman_mastery = 0.3
                        alpha, beta = 3.0, 7.0
            else:
                # 🔥 FIX F-027 + individualized cold-start prior (Yudelson 2013):
                # for new users, seed the diagnostics α/β from the concept's
                # population posterior (consistent with the load-bearing
                # canonical_data cold-start seed above), falling back to the
                # generic prior when the concept has too few observations.
                _d_alpha, _d_beta, _d_pm, _d_n = self._individualized_cold_start_prior(concept)
                # diagnostics path historically used the generic (3.0,7.0)
                # strength; preserve that strength when falling back, else use
                # the population-individualized (alpha,beta).
                if _d_n >= COLDSTART_MIN_POP_OBS:
                    alpha, beta = _d_alpha, _d_beta
                else:
                    alpha, beta = _GENERIC_PRIOR_ALPHA, _GENERIC_PRIOR_BETA
                _d_mean = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.3
                lyapunov_mastery = _d_mean
                bayesian_mastery = _d_mean
                kalman_mastery = _d_mean

            # 🔥 FIXED: Use mastery values from individual learners (no canonical reads!)
            raw_lyapunov = lyapunov_mastery
            raw_bayesian = bayesian_mastery
            raw_kalman = kalman_mastery
            
            # 🔥 FIXED: Ensure bayesian_alpha_beta is always defined
            if 'bayesian_alpha_beta' not in locals():
                bayesian_alpha_beta = (alpha, beta) if 'alpha' in locals() and 'beta' in locals() else (3.0, 7.0)
            
            # 🔥 FIX F-032: Calculate TRUE baseline mastery using adaptive JT ensemble weights (not equal weights)
            if hasattr(self, 'jt_ensemble') and self.jt_ensemble:
                ensemble_weights = self.jt_ensemble.get_weights()
                true_mastery_before = (
                    ensemble_weights.get("lyapunov", 0.33) * raw_lyapunov +
                    ensemble_weights.get("bayesian", 0.33) * raw_bayesian +
                    ensemble_weights.get("kalman", 0.34) * raw_kalman
                )
            else:
                # Fallback to equal weights if jt_ensemble not available
                true_mastery_before = (raw_lyapunov + raw_bayesian + raw_kalman) / 3.0
            
            # ADAPTIVE LEARNING RATE: Barzilai-Borwein method for convergence
            # Mathematical guarantee: Superlinear convergence for smooth functions
            user_concept_key = f"{user_id}_{concept}"
            
            if not hasattr(self, '_adaptive_state'):
                self._adaptive_state = {}
            
            # 🔥 FIX: Initialize state variable to prevent scope issues
            state = None
            
            if user_concept_key not in self._adaptive_state:
                # 🔥 IMPROVED COLD START: Stable initialization for both research and production
                self._adaptive_state[user_concept_key] = {
                    'previous_mastery': true_mastery_before,
                    'previous_gradient': 0.0,
                    'iteration': 0,
                    'last_adaptive_rate': 0.08 * 0.25  # Start with baseline for stability
                }
                adaptive_rate = 0.08 * 0.25  # Start at baseline (0.02) for smooth transition
            else:
                state = self._adaptive_state[user_concept_key]
                # FIX: Use actual learning signal from unified Jₜ calculation
                # unified_mastery_change is the η·Jₜ we computed above
                raw_learning_signal = unified_mastery_change  # Use the actual Jₜ result!
                current_gradient = raw_learning_signal
                
                if state and state.get('iteration', 0) > 0:
                    # 🔥 IMPROVED: Barzilai-Borwein with stability constraints
                    s_k = current_gradient - state['previous_gradient']  # Difference in gradients
                    y_k = true_mastery_before - state['previous_mastery']  # Difference in mastery
                    
                    # Safety checks for numerical stability
                    s_k_norm = max(abs(s_k), 1e-8)
                    y_k_norm = max(abs(y_k), 1e-8)
                    
                    # Improved Barzilai-Borwein step with sign preservation
                    if s_k * y_k > 0:  # Same direction - positive step
                        bb_step = min(abs(s_k * y_k) / (y_k_norm * y_k_norm), 0.1)  # Cap at 0.1
                    else:  # Opposite direction - conservative step
                        bb_step = min(abs(s_k * y_k) / (y_k_norm * y_k_norm), 0.05)  # More conservative
                    
                    # 🔥 ENHANCED BOUNDS: Production-safe adaptive rates
                    base_lr = 0.08
                    min_rate = base_lr * 0.01  # 0.0008 (very conservative)
                    max_rate = base_lr * 0.5   # 0.04 (moderate, not aggressive)
                    
                    # Smooth adaptation with momentum
                    previous_rate = state.get('last_adaptive_rate', base_lr * 0.25)
                    adaptive_rate = 0.7 * bb_step + 0.3 * previous_rate  # Momentum smoothing
                    
                    # Final bounds with safety
                    adaptive_rate = max(min_rate, min(max_rate, adaptive_rate))
                    adaptive_rate = max(0.001, abs(adaptive_rate))  # Ensure positive (absolute value!)
                    
                    # Store for momentum
                    state['last_adaptive_rate'] = adaptive_rate
                else:
                    # 🔥 CONSERVATIVE FIRST ITERATION: Stable start
                    adaptive_rate = 0.08 * 0.25  # 0.02 (same as baseline for stability)
                    if state:
                        state['last_adaptive_rate'] = adaptive_rate
                
                # Update adaptive state (only if state exists)
                if state:
                    state['previous_mastery'] = true_mastery_before
                    state['previous_gradient'] = current_gradient
                    state['iteration'] = state.get('iteration', 0) + 1
            
            # 🔥 REMOVED: confidence_weighted_rate creates competing control signal
            # Use our causal η(t) instead of confidence-weighted calculation
            
            iteration = state.get('iteration', 0) if state else 0
            
            # 🔥 FIX F-007: Compute ensemble mastery as weighted average of individual learners
            # This ensures ensemble actually combines learner strengths instead of being worse than all
            if hasattr(self, 'jt_ensemble') and self.jt_ensemble:
                ensemble_weights = self.jt_ensemble.get_weights()
                # Compute Bayesian mastery from alpha/beta
                bayesian_mastery = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.3
                # Weighted ensemble
                ensemble_mastery = (
                    ensemble_weights.get("lyapunov", 0.33) * raw_lyapunov +
                    ensemble_weights.get("bayesian", 0.33) * bayesian_mastery +
                    ensemble_weights.get("kalman", 0.34) * raw_kalman
                )
                # Use ensemble mastery instead of recursive update
                updated_state.mastery = ensemble_mastery
                updated_state.ensemble_weights = ensemble_weights
            else:
                # Fallback to equal weights if jt_ensemble not available
                bayesian_mastery = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.3
                ensemble_mastery = (raw_lyapunov + bayesian_mastery + raw_kalman) / 3.0
                updated_state.mastery = ensemble_mastery
                updated_state.ensemble_weights = {"lyapunov": 0.33, "bayesian": 0.33, "kalman": 0.34}

            updated_state.lyapunov_mastery = raw_lyapunov
            updated_state.bayesian_alpha = alpha if isinstance(bayesian_alpha_beta, tuple) and len(bayesian_alpha_beta) == 2 else 3.0
            updated_state.bayesian_beta = beta if isinstance(bayesian_alpha_beta, tuple) and len(bayesian_alpha_beta) == 2 else 7.0
            updated_state.kalman_mastery = raw_kalman
            # 🔥 EXPOSE ADAPTIVE RATE for research validation - USE OUR ADAPTIVE η(t)!
            updated_state.adaptive_rate = safe_float(eta)  # Use adaptive η(t), not confidence_weighted_rate
            updated_state.confidence_adjusted_mastery = safe_float(confidence_adjusted_mastery)
            updated_state.effective_learning_rate = safe_float(eta)  # Use adaptive η(t)
            updated_state.mastery_delta = safe_float(enhanced_mastery_change)
            updated_state.transfer_amount = safe_float(learning_transfer_bonus)
            # 🔥 CALCULATED ZPD FIELDS: Both state score and delta signal
            # F-006 FIX: zpd_target = mastery + 2*uncertainty (spec-compliant formula)
            _zpd_uncertainty = uncertainty if 'uncertainty' in locals() else (ensemble_variance if 'ensemble_variance' in locals() else 0.02)
            zpd_target_computed = min(1.0, actual_mastery_after + 2.0 * _zpd_uncertainty)
            zpd_alignment = 1.0 - abs(actual_mastery_after - zpd_target_computed)
            updated_state.zpd_score = max(0.0, min(1.0, zpd_alignment))  # State score for diagnostics
            updated_state.zpd_target = zpd_target_computed
            updated_state.zpd_alignment_error = abs(zpd_target_computed - actual_mastery_after)
            updated_state.zpd_delta_signal = zpd_scaled  # Delta signal used in optimization
            updated_state.transfer_amounts = transfer_amounts
            updated_state.transfer_efficiency = 0.0  # Will be calculated later
            updated_state.J_value = safe_float(J_t)
            
        except Exception as e:
            # 🔥 FIX F-027: Read alpha/beta from canonical state instead of hardcoding
            true_mastery_before = canonical_data.get("mastery", 0.3)
            raw_lyapunov = canonical_data.get("lyapunov_mastery", 0.3)
            alpha = canonical_data.get("bayesian_alpha", 3.0)
            beta = canonical_data.get("bayesian_beta", 7.0)
            raw_bayesian = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.3
            raw_kalman = canonical_data.get("kalman_mastery", 0.3)
            bayesian_mastery = raw_bayesian
            kalman_mastery = raw_kalman
            confidence_adjusted_mastery = 0.3
            
            # 🔥 FIX F-007: Compute ensemble mastery in exception path too
            if hasattr(self, 'jt_ensemble') and self.jt_ensemble:
                ensemble_weights = self.jt_ensemble.get_weights()
                ensemble_mastery = (
                    ensemble_weights.get("lyapunov", 0.33) * raw_lyapunov +
                    ensemble_weights.get("bayesian", 0.33) * bayesian_mastery +
                    ensemble_weights.get("kalman", 0.34) * raw_kalman
                )
                updated_state.mastery = ensemble_mastery
                updated_state.ensemble_weights = ensemble_weights
            else:
                ensemble_mastery = (raw_lyapunov + bayesian_mastery + raw_kalman) / 3.0
                updated_state.mastery = ensemble_mastery
                updated_state.ensemble_weights = {"lyapunov": 0.33, "bayesian": 0.33, "kalman": 0.34}
            
            # 🔥 VARIABLES: All properly initialized at method start
            
            # 🔥 SHADOW CAUSAL MODE - Track without breaking system
            causal_valid = False
            
            try:
                # 🔥 CRITICAL FIX: True signal separation
                # Direct learning gain (learners only, no policy/bandit/transfer)
                # enhanced_mastery_change already includes policy/bandit, so we need the raw learner change
                direct_learning_gain = enhanced_mastery_change / (policy_multiplier if 'policy_multiplier' in locals() else 1.0)
                
                # Enhanced learning gain (includes policy + bandit effects)
                enhanced_learning_gain = enhanced_mastery_change
                
                # 🔥 CORRECTED: TRUE baseline mastery (direct learning only)
                baseline_mastery_after = true_mastery_before + direct_learning_gain
                
                # Get actual final state (includes ALL effects)
                # actual_mastery_after is already computed above
                
                # 🔥 CRITICAL FIX: Correct transfer attribution by direction
                # Total gain from before to after
                total_gain = actual_mastery_after - true_mastery_before
                
                # Get actual transfer amount from transfer engine
                actual_transfer_amount = sum(transfer_amounts.values()) if transfer_amounts else 0.0
                
                # 🔥 TRANSFER EFFICIENCY: Transfer contribution as proportion of total gain
                if abs(total_gain) > 1e-6:
                    transfer_efficiency = actual_transfer_amount / abs(total_gain)
                else:
                    transfer_efficiency = 0.0
                
                # 🔥 TRANSFER CONTRIBUTION: Actual transfer effect (not just potential)
                true_transfer_contribution = actual_transfer_amount
                
                # Step 1: Learning velocity (mastery change per interaction)
                if enhanced_mastery_change > 0:
                    learning_velocity = enhanced_mastery_change
                else:
                    learning_velocity = 0.0
                
                # Step 2: Transfer efficiency (transfer as multiplier of learning)
                # Transfer should amplify learning, not dominate it
                if direct_learning_gain > 0.001:
                    transfer_multiplier = 1.0 + (true_transfer_contribution / direct_learning_gain)
                    transfer_bonus = min(0.5, (transfer_multiplier - 1.0) * 0.5)  # Cap at 50% bonus
                else:
                    transfer_bonus = 0.0
                
                J_regret = None  # Will be computed separately for evaluation
                
                # 🔥 METRICS LAYER: Variables are now properly defined
                
                causal_valid = True
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                # Continue execution - DON'T fail the system
            
            # Store causal validity for API response
            self._last_causal_valid = causal_valid
            
            # 🔥 PHASE 2 CORRECTED: Compute per-interaction J_t
            # Get contextual bandit scores for this context
            context_scores = []
            if hasattr(self.bandit, '_get_context_scores'):
                context_scores = self.bandit._get_context_scores(user_id, concept)
            optimal_reward = max(context_scores) if context_scores else 1.0
            actual_reward = reward if 'reward' in locals() else 0.0
            meaningful_pseudo_regret = optimal_reward - actual_reward
            
            # 🔥 CRITICAL FIX: Proper cost normalization (same scale as learning)
            response_time = interaction.get('response_time', 10.0)
            # Cost should be on same scale as learning gains (0.01-0.1)
            # Normalize: 10 seconds = 0.05 cost penalty
            cost = (response_time / 10.0) * 0.05  # Linear scaling to learning gain scale
            
            # 🔥 CRITICAL FIX: Update learner states with new mastery
        # 🔥 BULLETPROOF: Initialize state deltas for atomic batch writing
        state_deltas = []
        
        if self.learner_factory:
            try:
                # 🔥 BULLETPROOF: Collect state deltas for atomic batch writing
                
                for learner_name in ["lyapunov", "bayesian", "kalman"]:
                    learner = self.learner_factory.get(learner_name)
                    
                    # Create interaction data for learner update
                    # 🔥 HARD TYPE ENFORCEMENT: Ensure transfer_bonus is always scalar
                    transfer_bonus = 0.0
                    if isinstance(true_transfer_contribution, dict):
                        transfer_bonus = sum(true_transfer_contribution.values())
                    elif isinstance(true_transfer_contribution, (int, float)):
                        transfer_bonus = float(true_transfer_contribution)
                    
                    learner_interaction = {
                        'user_id': user_id,
                        'concept_id': concept,
                        'correct': interaction_is_correct(interaction, False),
                        'response_time': interaction.get('response_time', 10.0),
                        'mastery_before': true_mastery_before,
                        'mastery_after': actual_mastery_after,
                        'transfer_bonus': transfer_bonus
                    }
                    
                    # 🔥 PURE FUNCTION: Get state delta from learner (no immediate write)
                    # Pass canonical state for write mode (no external reads)
                    canonical_for_learner = working_state.get_main_state().to_dict()
                    if learner_name == "bayesian":
                        logger.info(f"🔥 PASSING TO BAYESIAN LEARNER: α={canonical_for_learner.get('bayesian_alpha', 3.0):.4f}, β={canonical_for_learner.get('bayesian_beta', 7.0):.4f} (sum={canonical_for_learner.get('bayesian_alpha', 3.0) + canonical_for_learner.get('bayesian_beta', 7.0):.4f})")
                    learner_result = learner.update(user_id, concept, learner_interaction, canonical_for_learner)
                    
                    # Collect state delta for batch writing
                    if learner_result and "state_delta" in learner_result:
                        state_deltas.append(learner_result["state_delta"])
                        
                        # 🔥 BULLETPROOF: Update main working state with learner results
                        main_state = working_state.get_main_state()
                        if learner_name == "lyapunov":
                            main_state.set("lyapunov_mastery", learner_result.get("mastery_after", 0.3))
                        elif learner_name == "bayesian":
                            main_state.set("bayesian_alpha", learner_result.get("alpha", 3.0))
                            main_state.set("bayesian_beta", learner_result.get("beta", 7.0))
                            main_state.set("bayesian_gamma", learner_result.get("gamma", 0.5))  # Add this line
                        elif learner_name == "kalman":
                            main_state.set("kalman_mastery", learner_result.get("mastery_after", 0.3))
                            main_state.set("kalman_covariance", learner_result.get("covariance", 0.1))
                            main_state.set("kalman_process_noise", learner_result.get("process_noise", 0.01))  # Add this line
                            main_state.set("kalman_measurement_noise", learner_result.get("measurement_noise", 0.01))  # Add this line
                    
            except Exception as e:
                logger.error(f"⚠️ Failed to update learners: {e}")

            # F-027/F-028: LearningResult must reflect post-update learner state
            _post_main = working_state.get_main_state()
            updated_state.bayesian_alpha = float(_post_main.get("bayesian_alpha", 3.0))
            updated_state.bayesian_beta = float(_post_main.get("bayesian_beta", 7.0))
            updated_state.lyapunov_mastery = float(_post_main.get("lyapunov_mastery", updated_state.lyapunov_mastery))
            updated_state.kalman_mastery = float(_post_main.get("kalman_mastery", updated_state.kalman_mastery))
            # 🔥 FIX F-028: Preserve Kalman covariance from working state (not hardcoded 0.1)
            # 🔥 F-002 fix: Handle None canonical_data for cold start
            kalman_cov_default = canonical_data.get("kalman_covariance", 0.1) if canonical_data else 0.1
            updated_state.kalman_covariance = float(_post_main.get("kalman_covariance", kalman_cov_default))
        
        # 🔥 BULLETPROOF: Create canonical state from multi-concept working state
        state_key = f"{user_id}_{concept}"
        canonical_state = working_state.get_main_state().to_dict()  # Start with main working state
        # 🔥 FIX F-016/F-017/F-027/F-028: Remove hardcoded values, preserve learner-computed state
        # Only override mastery with ensemble result; let other fields flow from working_state
        # 🔥 FIX F-027/F-028: Explicitly preserve learner-specific parameters in canonical state
        main_state = working_state.get_main_state()
        _persisted_uncertainty = main_state.get(
            "uncertainty",
            ensemble_variance if "ensemble_variance" in locals() else 0.02,
        )
        _persisted_ensemble_variance = main_state.get(
            "ensemble_variance",
            ensemble_variance if "ensemble_variance" in locals() else 0.02,
        )
        canonical_state.update({
            "mastery": updated_state.mastery,  # Override with ensemble result (FIX: was actual_mastery_after)
            "bayesian_alpha": main_state.get("bayesian_alpha", 3.0),  # Preserve Bayesian alpha
            "bayesian_beta": main_state.get("bayesian_beta", 7.0),  # Preserve Bayesian beta
            "kalman_mastery": main_state.get("kalman_mastery", 0.3),  # Preserve Kalman mastery
            "lyapunov_mastery": main_state.get("lyapunov_mastery", 0.3),  # Preserve Lyapunov mastery
            "kalman_covariance": main_state.get("kalman_covariance", 0.1),  # Preserve Kalman covariance
            "uncertainty": _persisted_uncertainty,
            "ensemble_variance": _persisted_ensemble_variance,
            "confidence": main_state.get(
                "confidence",
                max(0.0, 1.0 - min(float(_persisted_uncertainty), 1.0)),
            ),
            "timestamp": timestamp.isoformat(),
            "transfer_amounts": transfer_amounts,
            "transfer_efficiency": getattr(updated_state, 'transfer_efficiency', 0.0),
            "processing_mode": "write",
            "J_value": getattr(updated_state, 'J_value', 0.0),  # Persist JT governance value
            # 🔥 F-002 fix: Add Tier1 canonical fields for schema validation
            "zpd_score": getattr(updated_state, 'zpd_score', 0.8),
            "zpd_target": getattr(updated_state, 'zpd_target', actual_mastery_after),
            "zpd_alignment_error": getattr(updated_state, 'zpd_alignment_error', 0.0),
            "zpd_delta_signal": getattr(updated_state, 'zpd_delta_signal', 0.0),
            "ensemble_weights": getattr(updated_state, 'ensemble_weights', {"lyapunov": 0.33, "bayesian": 0.33, "kalman": 0.34}),
            "policy": getattr(updated_state, 'policy', "default"),
            "policy_multiplier": getattr(updated_state, 'policy_multiplier', 1.0),
            "mastery_delta": getattr(updated_state, 'mastery_delta', 0.0),
            "adaptive_rate": getattr(updated_state, 'adaptive_rate', 0.02)
        })
        
        self._persist_combined_state(user_id, concept, canonical_state, working_state, updated_state, _persisted_uncertainty, _persisted_ensemble_variance, write_enabled)
        
        # 🔥 BULLETPROOF: Transfer propagation using working_state only (no external reads!)
        if transfer_amounts:
            for target_concept, transfer_amount in transfer_amounts.items():
                if target_concept != concept:  # Don't apply self-transfer
                    # Get target concept's working state (creates default if needed)
                    target_working_state = working_state.get_concept(target_concept)
                    current_mastery = target_working_state.get("mastery", 0.3)
                    
                    # Apply transfer to working state
                    new_mastery = max(0.05, min(0.95, current_mastery + transfer_amount))
                    target_working_state.set("mastery", new_mastery)
                    target_working_state.set("last_transfer", transfer_amount)
                    target_working_state.set("transfer_timestamp", timestamp.isoformat())
                    
        
        # Calculate transfer efficiency
        if enhanced_mastery_change > 0.001:
            transfer_efficiency = learning_transfer_bonus / enhanced_mastery_change
        else:
            transfer_efficiency = 0.0
        
        # 🔥 BASELINE vs ENHANCED INTERACTION RECORDING
        try:
            
            # Record BASELINE interaction (pre-enhancement)
            self.metrics_aggregator.record_interaction(
                user_id=user_id + "_baseline",
                concept=concept,
                mastery_before=true_mastery_before,
                mastery_after=baseline_mastery_after,
                transfer_amount=0.0,
                transfer_contribution=0.0,
                selected_action=concept,
                bandit_reward=actual_reward,
                policy_multiplier=1.0,  # No policy effects in baseline
                response_time=interaction.get('response_time', 0.0),
                difficulty=interaction.get('difficulty', 0.5),
                lyapunov_mastery=raw_lyapunov,
                bayesian_mastery=raw_bayesian,
                kalman_mastery=raw_kalman,
                ensemble_variance=0.02,
                J_value=0.0  # Baseline has no J_t (no transfer/regret/cost optimization)
            )
            
            # Record ACTUAL interaction (with enhancement and transfer)
            self.metrics_aggregator.record_interaction(
                user_id=user_id + "_enhanced",
                concept=concept,
                mastery_before=true_mastery_before,
                mastery_after=actual_mastery_after,
                transfer_amount=sum(transfer_amounts.values()) if transfer_amounts else 0.0,
                transfer_contribution=true_transfer_contribution,  # 🔥 FIXED: Use computed value, not 0.0
                selected_action=concept,
                bandit_reward=actual_reward,
                policy_multiplier=policy_multiplier if 'policy_multiplier' in locals() else 1.0,
                response_time=interaction.get('response_time', 0.0),
                difficulty=interaction.get('difficulty', 0.5),
                lyapunov_mastery=raw_lyapunov,
                bayesian_mastery=raw_bayesian,
                kalman_mastery=raw_kalman,
                ensemble_variance=ensemble_variance if 'ensemble_variance' in locals() else 0.02,
                J_value=J_t  # 🔥 PHASE 2: Store per-interaction objective function
            )
            
        except Exception as e:
            pass
        
        # Update the result with new transfer info
        updated_state.transfer_amounts = transfer_amounts
        updated_state.transfer_efficiency = safe_float(transfer_efficiency)
        
        # 🔥 BULLETPROOF: Ensure no None values in final result
        updated_state.event_id = event_id
        updated_state.interaction_id = interaction_id
        updated_state.processing_time = safe_float(processing_time) if 'processing_time' in locals() else 0.015
        updated_state.confidence_adjusted_mastery = safe_float(confidence_adjusted_mastery)
        updated_state.effective_learning_rate = safe_float(eta)  # 🔥 USE OUR ADAPTIVE η(t)!
        updated_state.mastery_delta = safe_float(enhanced_mastery_change)
        updated_state.transfer_amount = safe_float(learning_transfer_bonus)
        updated_state.adaptive_rate = safe_float(eta)  # 🔥 USE OUR ADAPTIVE η(t)!
        
        # 🔥 CRITICAL FIX: Ensure J_value is properly assigned
        updated_state.J_value = safe_float(J_t)

        # F-024: expose interaction outcome on LearningResult for Kafka / trajectory consumers
        _is_correct = interaction.get("correct", interaction.get("correctness"))
        if _is_correct is not None:
            updated_state.correct = bool(_is_correct)
            updated_state.correctness = bool(_is_correct)

        # ── Individualized cold-start prior: record + online update (V1 path) ──
        # Population prior is GLOBAL per concept and accumulates across ALL
        # traffic classes from this single point. Predict-then-update ordering:
        # we record the posterior mean as consulted BEFORE this interaction
        # (the value a cold-start would seed from right now), then fold this
        # interaction in so it informs the NEXT cold-start — leak-free, exactly
        # as in probe_coldstart_powered.py. Deterministic (O(1), no RNG); on a
        # fresh replay brain it accumulates in event order. Recorded on the V1
        # path in jt_population_prior_contribution so every decision is
        # auditable even with HCIE_REDESIGN_V2 off.
        try:
            _pp = getattr(self, "_population_prior", None)
            # When HCIE_REDESIGN_V2 is on, the V2 block below owns the prior
            # read+update+recording (via its own singleton) — skip here to keep
            # exactly one writer per mode and avoid double-counting. V2 is OFF in
            # the live runtime, so this V1 block is the canonical updater there.
            _v2_on = os.environ.get("HCIE_REDESIGN_V2", "").strip().lower() in ("1", "true", "yes")
            if _pp is not None and _is_correct is not None and not _v2_on:
                _pp_mean_consulted = float(_pp.posterior_mean(concept))
                updated_state.jt_population_prior_contribution = _pp_mean_consulted
                _pp.update(concept, bool(_is_correct))
        except Exception as _e:  # pragma: no cover - defensive, never block write
            logger.warning(f"⚠️ Population-prior update failed (non-blocking): {_e}")

        # F-031: expose JT governance metrics on LearningResult
        updated_state.jt_volatility = safe_float(governance_volatility)
        updated_state.exploration_pressure = safe_float(governance_exploration_pressure)
        updated_state.stability_index = safe_float(governance_stability_index)

        # Ensemble-semantics evidence (migration 019). Persist the
        # m_ensemble synthesis, per-learner contributions, Bayesian
        # posterior reconstruction, Kalman R, and the weight-derivation
        # method as explicit fields. Kept SEMANTICALLY DISTINCT from the
        # JT 6D attribution block below (those describe governance
        # component shares of |J_t|; these describe per-learner shares of
        # m_ensemble). Mixing the two would poison the math audit.
        #
        # TEMPORAL SNAPSHOT POLICY (Step 2 of Phase A reconciliation):
        # All values in this block are read from `updated_state.*` at the
        # capture point, which is AFTER the F-027/F-028 fix has copied
        # per-learner post-update state from `_post_main`. We deliberately
        # do NOT read raw_lyapunov/alpha/beta/raw_kalman/bayesian_mastery
        # from locals(), because those are the pre-update snapshots
        # populated at line ~4444 and would cross the learner-update step
        # before reaching this point. Reading from updated_state.* ensures
        # the persisted row is internally consistent:
        #
        #   ensemble_mastery_estimate = Σ w_i × m_i_post   (synthesis identity)
        #   bayesian_mastery_after    = α_post / (α_post + β_post)  (posterior identity)
        #   canonical_mastery_after   = ensemble_mastery_estimate    (single-layer identity)
        #
        # The runtime-persisted `updated_state.mastery` (which becomes the
        # `mastery_after` DB column) is intentionally NOT recomputed here
        # so the Tier-1 certified bundle is preserved bit-for-bit.
        try:
            _ens_w = locals().get('ensemble_weights') or {}
            # 🔥 2-LEARNER FUSION (ENSEMBLE_ABLATION_2026-06-05.md): enforce the
            # canonical Kalman+Bayesian fusion at the synthesis chokepoint too,
            # so the PERSISTED ensemble_mastery_estimate / canonical_mastery_after
            # and the ensemble_weight_* columns reflect Lyapunov=0 regardless of
            # how ensemble_weights was sourced (get_weights, policy-config
            # override, or a hardcoded fallback). lyapunov_mastery_after is still
            # written. Reversible via HCIE_FUSION_CUT_LYAPUNOV=0.
            if (
                _ens_w
                and os.environ.get("HCIE_FUSION_CUT_LYAPUNOV", "1").strip().lower()
                not in ("0", "false", "no")
            ):
                _kb = float(safe_float(_ens_w.get('kalman')) or 0.0) + float(
                    safe_float(_ens_w.get('bayesian')) or 0.0
                )
                if _kb > 1e-12:
                    _ens_w = {
                        "lyapunov": 0.0,
                        "bayesian": (float(safe_float(_ens_w.get('bayesian')) or 0.0)) / _kb,
                        "kalman": (float(safe_float(_ens_w.get('kalman')) or 0.0)) / _kb,
                    }
                else:
                    _ens_w = {"lyapunov": 0.0, "bayesian": 0.5, "kalman": 0.5}
            _jt_abs = abs(safe_float(J_t) or 0.0)

            # Read post-update per-learner state from updated_state. This
            # is what gets persisted to bayesian_alpha_after/
            # lyapunov_mastery_after/kalman_mastery_after, so any
            # ensemble-layer value we compute from them is per-row
            # internally consistent.
            _m_ly_post = safe_float(getattr(updated_state, 'lyapunov_mastery', None))
            _bayes_a = safe_float(getattr(updated_state, 'bayesian_alpha', None))
            _bayes_b = safe_float(getattr(updated_state, 'bayesian_beta', None))
            _m_ka_post = safe_float(getattr(updated_state, 'kalman_mastery', None))

            # Posterior identity: m_bayesian_post = α_post / (α_post + β_post).
            _m_ba_post: Optional[float] = None
            if _bayes_a is not None and _bayes_b is not None and (_bayes_a + _bayes_b) > 0:
                _m_ba_post = float(_bayes_a) / (float(_bayes_a) + float(_bayes_b))
                _ab = float(_bayes_a) + float(_bayes_b)
                updated_state.bayesian_variance_after = (
                    float(_bayes_a) * float(_bayes_b) / (_ab * _ab * (_ab + 1.0))
                )
            updated_state.bayesian_mastery_after = _m_ba_post

            # Synthesis identity: m_ensemble = Σ w_i × m_i_post.
            # Use the weights snapshot we just persisted, not a stale
            # locals() copy, so the audit's per-row recomputation matches.
            _ens_m_post: Optional[float] = None
            if (
                _ens_w
                and _m_ly_post is not None
                and _m_ba_post is not None
                and _m_ka_post is not None
            ):
                _w_ly = safe_float(_ens_w.get('lyapunov')) or 0.0
                _w_ba = safe_float(_ens_w.get('bayesian')) or 0.0
                _w_ka = safe_float(_ens_w.get('kalman')) or 0.0
                _ens_m_post = _w_ly * _m_ly_post + _w_ba * _m_ba_post + _w_ka * _m_ka_post

            # Tier-3: optional inverse-variance fusion (HCIE_ENKF_FUSION=1, default off)
            _enkf_enabled = os.environ.get("HCIE_ENKF_FUSION", "").strip().lower() in ("1", "true", "yes")
            if _enkf_enabled:
                import importlib.util
                from pathlib import Path as _Path

                _enkf_path = _Path(__file__).resolve().parent / "enkf_inverse_variance.py"
                if _enkf_path.is_file():
                    _spec = importlib.util.spec_from_file_location("enkf_inverse_variance", _enkf_path)
                    _mod = importlib.util.module_from_spec(_spec)
                    _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
                    _var_ly = safe_float(getattr(updated_state, 'ensemble_variance_after', None))
                    _var_ba = safe_float(getattr(updated_state, 'bayesian_variance_after', None))
                    _var_ka = safe_float(getattr(updated_state, 'kalman_covariance_after', None))
                    _enkf_m, _enkf_w = _mod.inverse_variance_fuse(
                        {"lyapunov": _m_ly_post, "bayesian": _m_ba_post, "kalman": _m_ka_post},
                        {"lyapunov": _var_ly, "bayesian": _var_ba, "kalman": _var_ka},
                    )
                    if _enkf_m is not None:
                        _ens_m_post = _enkf_m
                        setattr(updated_state, "enkf_fusion_weights", _enkf_w)

            # V2-causal: canonical mastery = inverse-variance fusion of the two grounded learners
            # (Kalman+Bayesian) on the POST-update posteriors; Lyapunov disclosed but excluded.
            # This is the single governing fusion site (overwrites _ens_m_post -> updated_state.mastery
            # below). Flag off (V1 / sealed run-94a3b8ba) => skipped, weighted synthesis used verbatim.
            if v2_causal_fusion_enabled():
                _v2 = _LEARNER_FUSION.fuse(
                    masteries={"kalman": _m_ka_post, "bayesian": _m_ba_post, "lyapunov": _m_ly_post},
                    variances={
                        "kalman": safe_float(getattr(updated_state, 'kalman_covariance_after', None)),
                        "bayesian": safe_float(getattr(updated_state, 'bayesian_variance_after', None)),
                        "lyapunov": None,
                    },
                )
                _ens_m_post = _v2.mastery
                updated_state.ensemble_weights = dict(_v2.weights)
                setattr(updated_state, "v2_causal_fusion_weights", dict(_v2.weights))
                setattr(updated_state, "v2_causal_fusion_method", _v2.method)

            updated_state.ensemble_mastery_estimate = _ens_m_post
            # 🔥 STALENESS FIX (2026-05-31): previously the runtime mastery
            # (`updated_state.mastery` → `mastery_after`, "used for governance
            # decisions") was the PRE-update synthesis (Σ w·m_pre from
            # canonical_data at ~L4472) — it lagged one interaction and was the
            # WORST predictor of next-correct (corr 0.265 vs the post-update
            # synthesis 0.311; the per-learner Kalman alone is 0.332). We now
            # point the runtime mastery at the POST-update synthesis so both the
            # governance decision and the persisted `mastery_after` reflect THIS
            # interaction's learning. canonical_mastery_after stays equal to it
            # (single-layer identity). ⚠ This changes the Tier-1 bundle bit-for-bit
            # → requires a Phase-2 re-seal + re-validation.
            updated_state.canonical_mastery_after = _ens_m_post
            if _ens_m_post is not None:
                updated_state.mastery = _ens_m_post

            # Ensemble variance = Var([m_ly_post, m_ba_post, m_ka_post])
            # recomputed from the same post-update masteries so it is
            # internally consistent with the rest of the snapshot.
            if (
                _m_ly_post is not None
                and _m_ba_post is not None
                and _m_ka_post is not None
            ):
                _vals_post = [_m_ly_post, _m_ba_post, _m_ka_post]
                _mean_post = sum(_vals_post) / 3.0
                updated_state.ensemble_variance_after = (
                    sum((v - _mean_post) ** 2 for v in _vals_post) / 3.0
                )
            else:
                # Fallback: keep the upstream computed value if we cannot
                # reconstruct from per-learner post-update state.
                updated_state.ensemble_variance_after = safe_float(
                    locals().get('ensemble_variance')
                )

            # Kalman R is fixed at 0.1 by core/04_learners/kalman_learner.py.
            # Persist the value actually used so the audit can verify the
            # Kalman update without re-reading the learner source.
            _kal_cov = safe_float(getattr(updated_state, 'kalman_covariance', None))
            if _kal_cov is not None and _kal_cov >= 0.0:
                updated_state.kalman_R_after = 0.1

            if _ens_w:
                updated_state.ensemble_weight_lyapunov = safe_float(_ens_w.get('lyapunov'))
                updated_state.ensemble_weight_bayesian = safe_float(_ens_w.get('bayesian'))
                updated_state.ensemble_weight_kalman = safe_float(_ens_w.get('kalman'))

            # Per-learner JT contributions: m_i_post × |J_t|. Using the
            # same post-update masteries as the synthesis above so the
            # ensemble-attribution audit operates on a consistent row.
            if _m_ly_post is not None:
                updated_state.learner_jt_contribution_lyapunov = _m_ly_post * _jt_abs
            if _m_ba_post is not None:
                updated_state.learner_jt_contribution_bayesian = _m_ba_post * _jt_abs
            if _m_ka_post is not None:
                updated_state.learner_jt_contribution_kalman = _m_ka_post * _jt_abs

            # Weight-derivation method (matches the reconciled doc:
            # EMA-smoothed L1 normalization with α_ema = 0.1, W = 100).
            if hasattr(self, 'jt_ensemble') and self.jt_ensemble is not None:
                updated_state.ensemble_weight_method = 'ema_l1'
                updated_state.ensemble_ema_alpha = safe_float(
                    getattr(self.jt_ensemble, 'ema_alpha', None)
                )
                updated_state.ensemble_softmax_temperature = None
            else:
                updated_state.ensemble_weight_method = 'equal'
                updated_state.ensemble_ema_alpha = None
                updated_state.ensemble_softmax_temperature = None

            # Direct (pre-policy/bandit/transfer) learning gain.
            _direct = locals().get('direct_learning_gain')
            if _direct is not None:
                updated_state.mastery_delta_direct = safe_float(_direct)
            _t_amounts = locals().get('transfer_amounts') or {}
            if isinstance(_t_amounts, dict):
                _tot = 0.0
                for v in _t_amounts.values():
                    try:
                        _tot += float(v)
                    except (TypeError, ValueError):
                        pass
                updated_state.transfer_amount_total = _tot
        except Exception as e:
            logger.warning(f"⚠️ Failed to populate ensemble-semantics fields: {e}")

        # 🔥 PHASE A: Populate JT component decomposition (A3) — 6D + attribution + weights
        # Canonical key names from ConstitutionalJTGovernance.compute_jt:
        # {delta_m, transfer_realized, transfer_prospective, challenge, uncertainty, zpd}.
        # The historical write here used the wrong key ('transfer'), which
        # silently zeroed jt_transfer_contribution and starved every
        # downstream attribution / ablation / replay-diff audit. We pin
        # the keys explicitly so the schema is stable and JSON archaeology
        # is unnecessary.
        try:
            if 'contributions' in locals() and contributions:
                updated_state.jt_delta_m_contribution = safe_float(contributions.get('delta_m', 0.0))
                updated_state.jt_transfer_contribution = safe_float(
                    contributions.get('transfer_realized', contributions.get('transfer', 0.0))
                )
                updated_state.jt_transfer_prospective_contribution = safe_float(
                    contributions.get('transfer_prospective', 0.0)
                )
                updated_state.jt_challenge_contribution = safe_float(contributions.get('challenge', 0.0))
                updated_state.jt_uncertainty_contribution = safe_float(contributions.get('uncertainty', 0.0))
                updated_state.jt_zpd_contribution = safe_float(contributions.get('zpd', 0.0))
                updated_state.jt_unclamped = safe_float(J_t)
                updated_state.jt_clamped = safe_float(J_t)
                if 'attribution' in locals() and attribution:
                    updated_state.jt_attribution = {
                        str(k): safe_float(v) for k, v in attribution.items()
                    }
                if hasattr(self, 'jt_governance') and self.jt_governance is not None:
                    try:
                        updated_state.weights_snapshot = {
                            str(k): safe_float(v)
                            for k, v in dict(self.jt_governance.weights).items()
                        }
                    except Exception:
                        updated_state.weights_snapshot = None
        except Exception as e:
            logger.warning(f"⚠️ Failed to populate JT decomposition: {e}")

        # Tier 2.5 V2 signals (HCIE_REDESIGN_V2). Side-branch; default OFF.
        # Computed after V1 JT so V2 dims see the same `delta_m`, `mastery_before`,
        # and `cost` (legacy challenge value) the V1 path produced. Replay
        # determinism: V2 state is reset at run start via `reset_singletons_for_replay`.
        try:
            _v2_enabled = os.environ.get("HCIE_REDESIGN_V2", "").strip().lower() in ("1", "true", "yes")
            if _v2_enabled:
                import importlib.util as _v2_il
                from pathlib import Path as _V2Path

                _v2_path = _V2Path(__file__).resolve().parent / "jt_v2_signals.py"
                if _v2_path.is_file():
                    import sys as _sys
                    _v2_mod = _sys.modules.get("jt_v2_signals")
                    if _v2_mod is None:
                        _v2_spec = _v2_il.spec_from_file_location("jt_v2_signals", _v2_path)
                        _v2_mod = _v2_il.module_from_spec(_v2_spec)
                        # Python 3.10 dataclass introspection requires sys.modules registration.
                        _sys.modules["jt_v2_signals"] = _v2_mod
                        _v2_spec.loader.exec_module(_v2_mod)  # type: ignore[union-attr]

                    _v2_user_id = str(
                        (event_data or {}).get("user_id")
                        or (event_data or {}).get("learner_id")
                        or getattr(updated_state, "user_id", "unknown")
                    )
                    _v2_concept_id = str(
                        (event_data or {}).get("concept_id")
                        or (event_data or {}).get("skill_id")
                        or getattr(updated_state, "concept_id", "unknown")
                    )
                    _v2_correct = bool(
                        (event_data or {}).get("correct", False)
                        or getattr(updated_state, "correct", False)
                    )
                    _v2_assess = bool(
                        (event_data or {}).get("is_assessment", False)
                        or (event_data or {}).get("assessment", False)
                        or (event_data or {}).get("assessment_flag", False)
                    )
                    _v2_prereq_w = (event_data or {}).get("prereq_weights") or {}
                    _v2_legacy_challenge = safe_float(
                        getattr(updated_state, "jt_challenge_contribution", 0.0)
                    )

                    _v2_signals = _v2_mod.compute_v2_signals(
                        user_id=_v2_user_id,
                        concept_id=_v2_concept_id,
                        mastery_before=safe_float(
                            getattr(updated_state, "mastery_before", 0.0)
                        ),
                        delta_m=safe_float(updated_state.jt_delta_m_contribution),
                        correct=_v2_correct,
                        is_assessment=_v2_assess,
                        legacy_challenge_value=_v2_legacy_challenge,
                        population_prior=_v2_mod.get_population_prior(),
                        prereq_accumulator=_v2_mod.get_prereq_accumulator(),
                        challenge_trigger=_v2_mod.get_challenge_trigger(),
                        prereq_weights=_v2_prereq_w if isinstance(_v2_prereq_w, dict) else None,
                    )

                    updated_state.jt_baseline_difficulty_contribution = float(
                        _v2_signals.baseline_difficulty
                    )
                    updated_state.jt_challenge_event_contribution = float(
                        _v2_signals.challenge_event
                    )
                    updated_state.jt_population_prior_contribution = float(
                        _v2_signals.population_prior
                    )
                    updated_state.jt_t_realized_v2_contribution = float(
                        _v2_signals.t_realized_v2
                    )
                    updated_state.jt_v2_active = True
                    updated_state.jt_v2_state_snapshot = dict(_v2_signals.state_snapshot)
                    updated_state.jt_v2_challenge_event_fired = bool(
                        _v2_signals.challenge_event_fired
                    )
                    updated_state.jt_v2_challenge_event_reason = str(
                        _v2_signals.challenge_event_reason
                    )
        except Exception as e:
            logger.warning(f"⚠️ Failed to populate V2 signals (HCIE_REDESIGN_V2): {e}")
            try:
                updated_state.jt_v2_active = False
            except Exception:
                pass

        # 🔥 CRITICAL: Ensure behavioral η(t) is preserved in final result
        assert abs(updated_state.adaptive_rate - eta) < 1e-6, f"η override! expected={eta}, got={updated_state.adaptive_rate}"
        assert abs(updated_state.effective_learning_rate - eta) < 1e-6, f"η override! expected={eta}, got={updated_state.effective_learning_rate}"
        
        self._record_full_metrics(user_id, concept, event_data, mode, eta, event_id, updated_state)
        
        # Return the canonical result
        return updated_state
    

    def _record_full_metrics(self, user_id, concept, event_data, mode, eta, event_id, updated_state):
        """Direct gauge instrumentation for a learning event (extracted verbatim from _write_mode; side-effect only)."""
        # 🔥 DIRECT GAUGE INSTRUMENTATION - The missing piece!
        try:
            from core.learning.metrics import (
                adaptive_learning_rate_gauge, 
                record_learning_update,
                record_learning_efficiency_point,
                record_convergence_point,
                record_ablation_point,
                record_causal_pair,
                record_learner_states,
                record_full_learning_event,
                calculate_power_analysis,
                learning_curve_mastery
            )

            # Extract user_type from event_data or derive from user_id
            if event_data and 'user_type' in event_data:
                user_type = event_data['user_type']
            else:
                # 🔥 Derive from user_id
                if user_id.startswith('fast_learner'):
                    user_type = 'fast_learner'
                elif user_id.startswith('slow_learner'):
                    user_type = 'slow_learner'
                elif user_id.startswith('improving_learner'):
                    user_type = 'improving_learner'
                else:
                    user_type = 'unknown'

            # 🔥 UNIFIED METRICS: Single entry point for all metrics
            if hasattr(updated_state, 'mastery_delta'):
                mastery_before = updated_state.mastery - updated_state.mastery_delta
                mastery_after = updated_state.mastery

                # 🔥 GOVERNANCE: Validate OBSERVE read-only before metrics recording
                try:
                    from core.learning.governance_validator import assert_observe_readonly
                    from core.learning.metrics_governance import record_governance_validation
                    metrics_context = {
                        "J_value": getattr(updated_state, 'J_value', 0.0),
                        "adaptive_rate": getattr(updated_state, 'adaptive_rate', None),
                        "regret": 0.0  # Placeholder for future regret tracking
                    }
                    assert_observe_readonly(metrics_context)
                    record_governance_validation("observe_readonly", True)
                except ImportError:
                    pass
                except AssertionError as e:
                    from core.learning.metrics_governance import record_governance_validation, record_governance_violation
                    record_governance_validation("observe_readonly", False)
                    record_governance_violation("observe_readonly")

                # Record all metrics in one clean call
                record_full_learning_event(
                    user_id=user_id,
                    concept=concept,
                    user_type=user_type,
                    mode=mode,
                    eta=eta,
                    mastery_before=mastery_before,
                    mastery_after=mastery_after,
                    lyapunov=getattr(updated_state, 'lyapunov_mastery', 0.3),
                    bayesian_alpha=getattr(updated_state, 'bayesian_alpha', 3.0),
                    bayesian_beta=getattr(updated_state, 'bayesian_beta', 7.0),
                    kalman=getattr(updated_state, 'kalman_mastery', 0.3),
                    event_id=event_id if event_id else f"auto_{user_id}_{int(time.time())}",
                    # Cognitive state metrics (Unified Brain internals)
                    J_value=getattr(updated_state, 'J_value', 0.0),
                    zpd_score_val=getattr(updated_state, 'zpd_score', 0.5),
                    zpd_target_val=getattr(updated_state, 'zpd_target', 0.3),
                    zpd_alignment_error_val=getattr(updated_state, 'zpd_alignment_error', 0.0),
                    transfer_amount_val=getattr(updated_state, 'transfer_amount', 0.0),
                    transfer_efficiency_val=getattr(updated_state, 'transfer_efficiency', 0.0),
                    uncertainty_val=getattr(updated_state, 'uncertainty', 0.2),
                    confidence_val=getattr(updated_state, 'confidence', 0.8),
                    ensemble_weights_val=getattr(updated_state, 'ensemble_weights', None)
                )
                
                # 🔥 LONGITUDINAL: Track learning curves over time
                time_bucket = int(int(time.time()) / 3600)  # 1-hour buckets
                learning_curve_mastery.labels(
                    user_id=user_id,
                    concept=concept,
                    user_type=user_type,
                    mode=mode,
                    time_bucket=str(time_bucket)
                ).set(mastery_after)
                

        except Exception as e:
            pass

    def _persist_combined_state(self, user_id, concept, canonical_state, working_state, updated_state, _persisted_uncertainty, _persisted_ensemble_variance, write_enabled):
        """Persist combined canonical+learner state (extracted verbatim from _write_mode; side-effect; raises on write failure)."""
        # 🔥 BULLETPROOF: Batch write all states atomically (learner states + canonical state)
        # 🛡️ WRITE GUARD: Prevent double writes in shadow mode
        if write_enabled and self._learning_state_repo:
            try:
                # Prepare batch writes
                batched_writes = []
                
                # 🔥 FIX F-027/F-028: Use updated working state values instead of learner state objects
                # The working state has the updated learner results, but state_deltas might be stale
                # Merge working state learner-specific parameters into canonical state
                main_state = working_state.get_main_state()
                combined_state = canonical_state.copy()
                combined_state.update({
                    "bayesian_alpha": main_state.get("bayesian_alpha", 3.0),
                    "bayesian_beta": main_state.get("bayesian_beta", 7.0),
                    "kalman_mastery": main_state.get("kalman_mastery", 0.3),
                    "kalman_covariance": main_state.get("kalman_covariance", 0.1),
                    "lyapunov_mastery": main_state.get("lyapunov_mastery", 0.3),
                    "uncertainty": _persisted_uncertainty,
                    "ensemble_variance": _persisted_ensemble_variance,
                    "confidence": canonical_state.get("confidence"),
                    "J_value": canonical_state.get("J_value", 0.0),
                    # 🔥 FIX F-007: Persist ensemble weights to database
                    "ensemble_weights": getattr(updated_state, 'ensemble_weights', {"lyapunov": 0.33, "bayesian": 0.33, "kalman": 0.34}),
                })
                # 🔥 DEBUG: Log alpha/beta values being written
                logger.info(f"🔥 BATCH WRITE: {user_id}/{concept} α={combined_state.get('bayesian_alpha', 3.0):.4f}, β={combined_state.get('bayesian_beta', 7.0):.4f} (sum={combined_state.get('bayesian_alpha', 3.0) + combined_state.get('bayesian_beta', 7.0):.4f})")
                
                # Write single combined state
                batched_writes.append({
                    'table': 'learning_state',
                    'user_id': user_id,
                    'concept': concept,
                    'state_data': combined_state
                })
                
                # 🔥 CRITICAL: Set ownership context for experiment writes
                if self._learning_state_repo and self._learning_state_repo.ownership:
                    from core.ownership.ownership_enforcement import CognitionWriter
                    self._learning_state_repo.ownership.set_writer(CognitionWriter.EXPERIMENT)

                # 🔥 ATOMIC: Single transaction for all writes
                success = self._learning_state_repo.batch_save_states(batched_writes)

                # 🔥 CRITICAL: Clear ownership context after write
                if self._learning_state_repo and self._learning_state_repo.ownership:
                    self._learning_state_repo.ownership.clear_writer()
                
                if success:
                    pass
                else:
                    raise RuntimeError(f"Failed to batch write states for {user_id}/{concept}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to batch write states: {e}")
                raise
        
        else:
            # 🛡️ SHADOW MODE: Skip state write to prevent double mutation
            if not write_enabled:
                pass
            else:
                # 🔥 BULLETPROOF: Repository is required in write mode
                raise RuntimeError("Learning state repository required for write mode - cannot proceed without persistence")

    def _resolve_experiment_mode(self, user_id, event_data):
        """Resolve/assign the A/B experiment mode (extracted from _write_mode; mutates event_data in place)."""
        # 🔥 A/B EXPERIMENT: Assign user to experimental group
        import hashlib

        def assign_experiment_group(user_id: str) -> str:
            """Deterministic assignment to A/B groups for fair comparison"""
            hash_val = int(hashlib.md5(user_id.encode(), usedforsecurity=False).hexdigest(), 16)
            group_num = hash_val % 4
            
            if group_num == 0:
                return "adaptive"
            elif group_num == 1:
                return "fixed_low"
            elif group_num == 2:
                return "fixed_mid"
            else:
                return "fixed_high"
        
        # Extract or assign experiment mode
        if event_data and "experiment_mode" in event_data:
            mode = event_data["experiment_mode"]
        else:
            mode = assign_experiment_group(user_id)
            # Store for consistency if event_data is available
            if event_data is not None:
                event_data["experiment_mode"] = mode
        return mode
    def get_canonical_state_health(self):
        """
        🔥 Get canonical state health metrics for monitoring
        
        Returns:
            dict: Health metrics including miss rate
        """
        total_reads = self._canonical_state_reads
        total_misses = self._canonical_state_misses
        
        if total_reads == 0:
            miss_rate = 0.0
        else:
            miss_rate = total_misses / total_reads
        
        return {
            'total_reads': total_reads,
            'total_misses': total_misses,
            'miss_rate': miss_rate,
            'health': 'HEALTHY' if miss_rate == 0 else 'CRITICAL',
            'message': f"Canonical state miss rate: {miss_rate:.2%}" if miss_rate > 0 else "Perfect canonical state consistency"
        }
    
    def _extract_mastery_from_state(self, state, learner_type):
        """
        🔥 FIXED: Extract mastery from actual learner return types
        
        Handles: float, tuple, dict based on actual learner.get_state() behavior
        """
        if learner_type == "lyapunov":
            # Lyapunov returns float directly
            return state if isinstance(state, float) else state.get("mastery", 0.3) if isinstance(state, dict) else 0.3
        elif learner_type == "bayesian":
            # Bayesian returns tuple (alpha, beta)
            if isinstance(state, tuple) and len(state) >= 2:
                alpha, beta = state[0], state[1]
                return alpha / (alpha + beta) if (alpha + beta) > 0 else 0.3
            elif isinstance(state, dict):
                alpha = state.get("alpha", 1.0)
                beta = state.get("beta", 2.33)
                return alpha / (alpha + beta) if (alpha + beta) > 0 else 0.3
            else:
                return 0.3
        elif learner_type == "kalman":
            # Kalman returns tuple (mastery, covariance)
            if isinstance(state, tuple) and len(state) >= 1:
                return state[0]  # First element is mastery
            elif isinstance(state, dict):
                return state.get("mastery", 0.3)
            else:
                return 0.3
        else:
            return 0.3
    
    def _extract_learner_state(self, learner, user_id: str, concept: str, learner_type: LearnerType) -> LearnerState:
        """
        Extract learner state into typed format using the LearnerState protocol
        
        Args:
            learner: Learner instance
            user_id: User identifier
            concept: Learning concept
            learner_type: Type of learner (LYAPUNOV, BAYESIAN, KALMAN)
        
        Returns:
            LearnerState: Typed state object
        """
        try:
            # Get raw state from learner
            raw_state = learner.get_state(user_id, concept)
            
            if learner_type == LearnerType.LYAPUNOV:
                return LyapunovState(
                    mastery=raw_state.get("mastery", 0.3),
                    alpha=raw_state.get("alpha"),
                    beta=raw_state.get("beta"),
                    covariance=raw_state.get("covariance")
                )
            elif learner_type == LearnerType.BAYESIAN:
                mastery = raw_state.get("mastery")
                if not mastery:
                    alpha = raw_state.get("alpha", 1.0)
                    beta = raw_state.get("beta", 2.33)
                    mastery = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.3
                return BayesianState(
                    alpha=raw_state.get("alpha", 1.0),
                    beta=raw_state.get("beta", 2.33),
                    mastery=mastery
                )
            elif learner_type == LearnerType.KALMAN:
                return KalmanState(
                    mastery=raw_state.get("mastery", 0.3),
                    covariance=raw_state.get("covariance"),
                    mean=raw_state.get("mean")
                )
            else:
                # Unknown learner type - return default state
                return LearnerState(mastery=0.3)
        except Exception as e:
            return LearnerState(mastery=0.3)
    
    def _extract_mastery(self, state, learner_type):
        """
        🔥 FIXED: Normalize learner state interfaces
        
        Extract mastery from different learner state formats
        """
        if learner_type == "lyapunov":
            # Lyapunov returns state with mastery field
            return state.get("mastery", 0.3)
        elif learner_type == "bayesian":
            # Bayesian returns alpha/beta parameters
            alpha = state.get("alpha", 1.0)
            beta = state.get("beta", 2.33)
            return alpha / (alpha + beta) if (alpha + beta) > 0 else 0.0
        elif learner_type == "kalman":
            # Kalman returns state with mastery field
            return state.get("mastery", 0.3)
        else:
            # Default fallback
            return 0.3
    
    def get_research_metrics(self) -> Dict[str, float]:
        """
        Get research-grade metrics for objective function definition
        
        This provides the foundation for defining J with real measurable signals
        """
        return self.metrics_aggregator.get_research_summary()
    
    def get_objective_function(self) -> float:
        """
        🔥 PHASE 2: Get the current objective function value J
        
        This is the system's north star - what "good" means globally
        """
        return self.metrics_aggregator.compute_objective_function()
    
    def optimize_for_objective(self, candidate_actions: List[str]) -> str:
        """
        🔥 PHASE 2: Choose action that maximizes objective function J
        
        Instead of maximizing reward, maximize J
        """
        best_action = candidate_actions[0] if candidate_actions else ""
        best_J = float('-inf')
        
        for action in candidate_actions:
            # Simulate action and compute J
            simulated_J = self._simulate_action_for_objective(action)
            if simulated_J > best_J:
                best_J = simulated_J
                best_action = action
        
        return best_action
    
    def _simulate_action_for_objective(self, action: str) -> float:
        """
        Simulate action and compute objective function value
        
        This is where we shift from reward-driven to objective-driven decisions
        """
        # For now, use current J as baseline
        # In Phase 3, we'll implement full simulation
        return self.get_objective_function()
    
    def test_critical_transfer_scenario(self) -> Dict[str, float]:
        """
        🔥 CRITICAL TEST: transfer > 0 AND J increases because of it
        
        This is the moment where the system becomes truly causally optimized
        """
        
        # Test user with strong transfer potential
        test_user = 'critical_test_user'
        source_concept = 'k2_computing_systems_devices'  # Strong transfer source
        target_concept = 'k5_computing_systems_devices'  # Transfer target
        
        # Step 1: Build strong foundation in source concept
        for i in range(3):
            result = self.process_event(
                test_user + '_source_' + str(i),
                source_concept,
                {
                    "correct": True,
                    "response_time": 2.0,
                    "confidence": 0.9
                },
                write_enabled=True
            )
        
        # Step 2: Test transfer to target concept
        
        # Get J before transfer
        J_before = self.get_objective_function()
        
        # Process interaction in target concept (should trigger transfer)
        result = self.process_event(
            test_user + '_target',
            target_concept,
            {
                "correct": True,
                "response_time": 3.0,
                "confidence": 0.8
            },
            write_enabled=True
        )
        
        # Get J after transfer
        J_after = self.get_objective_function()
        
        # Analyze results
        enhanced_interactions = [i for i in self.metrics_aggregator.interaction_history if i.user_id.endswith('_enhanced')]
        target_interaction = enhanced_interactions[-1] if enhanced_interactions else None
        
        
        if target_interaction:
            
            
            # Critical test result
            transfer_visible = target_interaction.transfer_contribution > 0.001
            J_increased = (J_after - J_before) > 0.001
            
            return {
                'transfer_contribution': target_interaction.transfer_contribution,
                'J_before': J_before,
                'J_after': J_after,
                'J_delta': J_after - J_before,
                'transfer_visible': transfer_visible,
                'J_increased': J_increased,
                'success': transfer_visible and J_increased
            }
        else:
            return {'success': False}
    
    def test_phase3_jt_optimization(self) -> Dict[str, float]:
        """
        🔥 PHASE 3: Test J_t-driven bandit optimization
        
        Goal: Make E[J_t] increase over time through objective-driven learning
        """
        
        # Test user for objective optimization
        test_user = 'phase3_jt_user'
        concepts = ['k2_computing_systems_devices', 'k5_computing_systems_devices', 'k2_computing_systems_hardware_software']
        
        # Track J over time
        J_history = []
        
        
        for round_num in range(5):
            
            # Multiple interactions per round
            round_J_values = []
            for concept in concepts:
                result = self.process_event(
                    test_user + f'_round{round_num}_{concept}',
                    concept,
                    {
                        "correct": concept.startswith("k2"),  # K-2 concepts are easier
                        "response_time": 5.0 + random.random() * 3.0,
                        "confidence": 0.7 + random.random() * 0.3
                    },
                    write_enabled=True
                )
                
                # Get J_t from latest interaction
                enhanced_interactions = [i for i in self.metrics_aggregator.interaction_history 
                                       if i.user_id.endswith('_enhanced') and i.concept == concept]
                if enhanced_interactions:
                    latest_J_t = enhanced_interactions[-1].J_value
                    round_J_values.append(latest_J_t)
            
            # Calculate average J for this round
            if round_J_values:
                avg_J = sum(round_J_values) / len(round_J_values)
                J_history.append(avg_J)
                
                # Get global J
                global_J = self.get_objective_function()
            else:
                pass
        
        
        # Analyze J trend
        if len(J_history) >= 2:
            J_start = J_history[0]
            J_end = J_history[-1]
            J_improvement = J_end - J_start
            
            
            # Check for positive trend
            positive_trend = all(J_history[i] <= J_history[i+1] + 0.01 for i in range(len(J_history)-1))
            
            if J_improvement > 0.01 and positive_trend:
                return {
                    'J_start': J_start,
                    'J_end': J_end,
                    'J_improvement': J_improvement,
                    'positive_trend': positive_trend,
                    'success': True
                }
            elif J_improvement > 0:
                return {
                    'J_start': J_start,
                    'J_end': J_end,
                    'J_improvement': J_improvement,
                    'positive_trend': positive_trend,
                    'success': False
                }
            else:
                return {
                    'J_start': J_start,
                    'J_end': J_end,
                    'J_improvement': J_improvement,
                    'positive_trend': positive_trend,
                    'success': False
                }
        else:
            return {'success': False}
    
    def estimate_J_t_for_action(self, action: str, context: Dict[str, float]) -> float:
        """
        🔥 CAUSALLY VALID: Estimate E[J_t | action, context] without breaking validity
        
        Args:
            action: The action (concept) we're considering
            context: Context features (mastery, difficulty, etc.)
            
        Returns:
            Estimated J_t value for this action in this context
        """
        # Get historical interactions with similar contexts
        similar_interactions = []
        
        for interaction in self.metrics_aggregator.interaction_history:
            if not interaction.user_id.endswith('_enhanced'):
                continue  # Only use enhanced interactions for J_t estimation
                
            # Check context similarity
            hist_context = {
                'mastery': interaction.mastery_before,
                'difficulty': getattr(interaction, 'difficulty', 0.5)
            }
            
            # Calculate context similarity
            mastery_diff = abs(hist_context['mastery'] - context.get('mastery', 0.5))
            difficulty_diff = abs(hist_context['difficulty'] - context.get('difficulty', 0.5))
            
            # Only include similar contexts (causal validity)
            if mastery_diff < 0.1 and difficulty_diff < 0.1:
                # Weight by similarity and recency
                similarity_weight = 1.0 - (mastery_diff + difficulty_diff) / 0.2
                similar_interactions.append({
                    'J_t': interaction.J_value,
                    'weight': similarity_weight,
                    'action': interaction.concept
                })
        
        # Filter by action and compute weighted average
        action_interactions = [i for i in similar_interactions if i['action'] == action]
        
        if action_interactions:
            total_weight = sum(i['weight'] for i in action_interactions)
            weighted_J_t = sum(i['J_t'] * i['weight'] for i in action_interactions) / total_weight
            return weighted_J_t
        else:
            # Fallback to baseline estimate
            return self._baseline_J_t_estimate(action, context)
    
    def _baseline_J_t_estimate(self, action: str, context: Dict[str, float]) -> float:
        """
        Baseline J_t estimate when no similar historical data available
        """
        # Simple heuristic based on context
        mastery = context.get('mastery', 0.5)
        difficulty = context.get('difficulty', 0.5)
        
        # Optimal learning happens in ZPD (mastery ≈ difficulty)
        zpd_alignment = 1.0 - abs(mastery - difficulty)
        
        # Expected learning gain
        expected_learning = 0.05 * zpd_alignment
        
        # Expected transfer (simplified)
        expected_transfer = 0.01 * zpd_alignment
        
        # Expected cost
        expected_cost = 0.05
        
        # Baseline J_t
        baseline_J_t = 1.0 * expected_learning + 2.0 * expected_transfer - 0.5 * expected_cost
        
        return max(0.0, baseline_J_t)  # Ensure non-negative
    
    def compute_J_regret(self, user_id: str, chosen_action: str, context: Dict[str, float]) -> float:
        """
        🔥 J-ALIGNED REGRET: Compute regret over J_t, not reward
        
        Args:
            user_id: User identifier
            chosen_action: The action that was taken
            context: Context features
            
        Returns:
            J_regret = max_a E[J_t | a, context] - E[J_t | chosen_action, context]
        """
        # Get available actions (concepts)
        available_actions = ['k2_computing_systems_devices', 'k5_computing_systems_devices', 
                           'k2_computing_systems_hardware_software']
        
        # Estimate J_t for all actions in this context
        J_t_estimates = {}
        for action in available_actions:
            J_t_estimates[action] = self.estimate_J_t_for_action(action, context)
        
        # Find best action
        best_J_t = max(J_t_estimates.values())
        chosen_J_t = J_t_estimates.get(chosen_action, 0.0)
        
        # Compute J_regret
        J_regret = best_J_t - chosen_J_t
        
        return max(0.0, J_regret)  # Regret is non-negative
    
    def export_interaction_data(self) -> List[Dict]:
        """Export all interaction data for external analysis"""
        return self.metrics_aggregator.export_for_analysis()
    
    def _simulation_mode(self, user_id: str, concept: str, interaction: Dict[str, Any], timestamp: datetime) -> LearningResult:
        """Phase 14g (Slice 0a): quarantined.

        The simulation-mode path was a hidden write that called
        ``_write_mode(..., write_enabled=False, state_before={})`` and tagged
        ``processing_mode='simulation'``. It bypassed canonical state, did not
        emit outbox events, and was not replay-deterministic. Per the
        Semantic Honesty Law it is removed from public runtime API. The
        canonical path for "no side effects" experiments is ``ReplayEngine``
        (Slice 4c).
        """
        raise NotImplementedError(
            "_simulation_mode is not implemented in FINAL runtime topology "
            "(Phase 14g Slice 0a). Use ReplayEngine via /v3/experiments/.../replay."
        )
    
    def _calculate_ensemble_weights(self, learner_insights: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence-weighted ensemble weights"""
        weights = {}
        
        for learner_name, state in learner_insights.items():
            if "uncertainty" in state:
                uncertainty = state["uncertainty"]
                weights[learner_name] = 1.0 / (1.0 + uncertainty)
            else:
                weights[learner_name] = 1.0  # Default weight
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}
        
        return weights
    
    def _calculate_ensemble_variance(self, learner_insights: Dict[str, Any]) -> float:
        """Calculate variance between learner predictions"""
        mastery_values = []
        
        for learner_name, state in learner_insights.items():
            if "mastery" in state:
                mastery_values.append(state["mastery"])
        
        if len(mastery_values) > 1:
            return np.var(mastery_values)
        return 0.0
    
    def select_next_concept(self, 
                           user_id: str, 
                           available_concepts: List[str], 
                           policy_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Select next concept using policy-governed bandit selection.
        
        This replaces external random concept selection with UnifiedBrain governance,
        ensuring policies actually influence action selection.
        
        Args:
            user_id: User identifier
            available_concepts: List of available concepts to select from
            policy_config: Policy configuration (optional, uses current config if None)
            
        Returns:
            Selected concept
        """
        try:
            # Get mastery parameters for all concepts
            mastery_params = {}
            representation_params = {}
            difficulty_map = {}
            
            # Fetch current state for all available concepts
            for concept in available_concepts:
                state_result = self.process_event(
                    user_id=user_id,
                    concept=concept,
                    interaction=None,
                    mode="read"
                )
                state = state_result.get("state", {})
                
                # Extract mastery parameters (alpha, beta)
                alpha = state.get("alpha", 1.0)
                beta = state.get("beta", 1.0)
                mastery_params[concept] = (alpha, beta)
                
                # Extract representation parameters (default representation)
                arm = f"{concept}:default"
                rep_alpha = state.get("rep_alpha", 1.0)
                rep_beta = state.get("rep_beta", 1.0)
                representation_params[arm] = (rep_alpha, rep_beta)
                
                # Get difficulty
                difficulty = self._lookup_concept_difficulty(concept)
                difficulty_map[concept] = difficulty
            
            # Apply policy configuration if provided
            if policy_config and hasattr(self, 'bandit') and self.bandit:
                # Temporarily apply policy configuration
                original_exploration_rate = self.bandit.exploration_rate
                original_uncertainty_weight = self.bandit.uncertainty_weight
                
                if 'exploration_rate' in policy_config:
                    self.bandit.exploration_rate = policy_config['exploration_rate']
                if 'uncertainty_weight' in policy_config:
                    self.bandit.uncertainty_weight = policy_config['uncertainty_weight']
            
            # Select concept using bandit
            if hasattr(self, 'bandit') and self.bandit:
                selected_concept, selected_representation, score = self.bandit.select_arm(
                    user_id=user_id,
                    available_nodes=available_concepts,
                    mastery_params=mastery_params,
                    representation_params=representation_params,
                    difficulty_map=difficulty_map,
                    context={"policy": policy_config.get("policy", "hcie") if policy_config else "hcie"}
                )
                
                # Restore original bandit parameters
                if policy_config and hasattr(self, 'bandit') and self.bandit:
                    self.bandit.exploration_rate = original_exploration_rate
                    self.bandit.uncertainty_weight = original_uncertainty_weight
                
                return selected_concept
            else:
                # Fallback: random selection if bandit not available
                # 🔥 PRIORITY 2: Use deterministic RNG if available
                if self.deterministic and self.rng_manager:
                    import numpy as np
                    # Use deterministic bandit stream for random choice
                    rng_stream = self.rng_manager.get_bandit_stream()
                    index = int(rng_stream.integers(0, len(available_concepts)))
                    return available_concepts[index]
                else:
                    import numpy as np
                    return np.random.choice(available_concepts)
                
        except Exception as e:
            logger.error(f"Failed to select next concept: {e}")
            # Fallback: random selection on error
            # 🔥 PRIORITY 2: Use deterministic RNG if available
            if self.deterministic and self.rng_manager:
                import numpy as np
                # Use deterministic bandit stream for random choice
                rng_stream = self.rng_manager.get_bandit_stream()
                index = int(rng_stream.integers(0, len(available_concepts)))
                return available_concepts[index]
            else:
                import numpy as np
                return np.random.choice(available_concepts)
    
    def _get_user_policy(self, user_id: str) -> str:
        """Get active policy for user"""
        # This would integrate with your policy engine
        # For now, default to HCIE for cold start users
        return "hcie"  # TODO: Integrate with actual policy engine
    
    def _get_policy_multiplier(self, policy: str) -> float:
        """
        Get learning rate multiplier for policy
        
        🔥 PHASE 6 CONSTITUTIONAL PURIFICATION: All multipliers are neutral (1.0)
        - Old: Hardcoded priors (hcie=1.12, dag=1.05, random=0.97)
        - New: All neutral (1.0) - no inherent advantage/disadvantage
        - Policy effectiveness learned from JT history, not hardcoded priors
        """
        multipliers = {
            "hcie": 1.0,       # 🔥 PHASE 6: Neutral prior
            "heuristic": 1.0,  # 🔥 PHASE 6: Neutral prior
            "static": 1.0,     # 🔥 PHASE 6: Neutral prior
            "random": 1.0      # 🔥 PHASE 6: Neutral prior
        }
        return multipliers.get(policy, 1.0)
    
    def _lookup_concept_difficulty(self, concept: str) -> float:
        """Hardcoded difficulty lookup by concept-id prefix (NOT information-theoretic).

        Returns a fixed table value per grade band (k2/k5/k8/k12/practice) with a
        concept-length proxy fallback. This is a heuristic lookup, not a learned or
        information-theoretic measure — named accordingly.
        """
        # Fixed lookup table by grade-band prefix; higher band = higher difficulty.
        if concept.startswith('k2_'):
            return 0.3  # Elementary level
        elif concept.startswith('k5_'):
            return 0.5  # Middle school level  
        elif concept.startswith('k8_'):
            return 0.7  # High school level
        elif concept.startswith('k12_'):
            return 0.9  # Advanced level
        elif concept.startswith('practice_'):
            return 0.4  # Practice activities
        else:
            # Default: use concept length as proxy for complexity
            return min(0.9, 0.3 + len(concept) * 0.02)
    
    def _get_current_transfers(self, user_id: str, concept: str) -> Dict[str, float]:
        """Transfer is NOT computed in the brain hot path — returns {} by design.

        Cross-concept transfer is measured downstream by the transfer-measurement
        consumer over `transfer_events` (correlational, over the static prerequisite
        DAG). Kept as an empty seam so callers have a stable return shape.
        """
        return {}

    def _calculate_new_transfers(self, user_id: str, concept: str, interaction: Dict[str, Any]) -> Dict[str, float]:
        """Transfer is measured downstream, not here — returns {} by design.

        See `_get_current_transfers`: the transfer-measurement consumer owns this over
        `transfer_events`. Kept as an empty seam for caller shape stability.
        """
        return {}
    
    def _calculate_transfer_efficiency(self, user_id: str, concept: str) -> float:
        """Calculate transfer efficiency for user/concept"""
        # This would calculate transfer_amount / learning_gain
        # For now, return 0.0
        return 0.0  # TODO: Implement actual calculation


# Global instance for use across the system
unified_brain = UnifiedLearningBrain()


# Convenience functions for backward compatibility
def process_learning_event(user_id: str, concept: str, interaction: Optional[Dict[str, Any]] = None, mode: str = "write") -> LearningResult:
    """
    Convenience function for easy import and use

    Canonical modes (Slice 0a / Phase 14g):
    - API: process_learning_event(user_id, concept, mode="read")
    - Consumer: process_learning_event(user_id, concept, interaction, mode="write")

    Note: mode="simulation" was removed in Slice 0a. Use ReplayEngine for
    shadow / replay / experiment isolation.
    """
    return unified_brain.process_event(user_id, concept, interaction, mode)


def infer_user_state(user_id: str, concept: str) -> LearningResult:
    """Convenience function for read operations"""
    return process_learning_event(user_id, concept, mode="read")


def apply_learning_update(user_id: str, concept: str, interaction: Dict[str, Any]) -> LearningResult:
    """Convenience function for write operations"""
    # Ensure required keys present
    if isinstance(interaction, dict):
        interaction = dict(interaction)  # Copy to avoid mutation
        interaction.setdefault("user_id", user_id)
        interaction.setdefault("concept", concept)
    return process_learning_event(user_id, concept, interaction, mode="write")


def simulate_learning(user_id: str, concept: str, interaction: Dict[str, Any]) -> LearningResult:
    """Phase 14g (Slice 0a): quarantined.

    Routed to mode='simulation' which was a fake-live placeholder. Use
    ReplayEngine via /v3/experiments/.../replay for canonical shadow /
    replay / experiment isolation.
    """
    raise NotImplementedError(
        "simulate_learning() is not implemented in FINAL runtime topology "
        "(Phase 14g Slice 0a). Use ReplayEngine via /v3/experiments/.../replay."
    )


def _log_research_data(user_id: str, concept: str, interaction: Dict[str, Any], result: LearningResult) -> None:
    """
    Log research-grade mathematical data for interpretability
    
    Creates detailed mathematical logs suitable for research paper inclusion
    and statistical analysis of system performance.
    """
    try:
        # Create mathematical log entry
        log_entry = MathematicalLogEntry(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            concept=concept,
            event_type=interaction.get("event_type", "learning"),
            
            # Mathematical state
            mastery_before=result.mastery_before,
            mastery_after=result.mastery,
            learning_gain=result.learning_gain,
            uncertainty_before=result.uncertainty_before,
            uncertainty_after=result.uncertainty,
            
            # Ensemble calculations
            lyapunov_mastery=result.lyapunov_mastery,
            bayesian_mastery=result.bayesian_mastery,
            kalman_mastery=result.kalman_mastery,
            ensemble_variance=result.ensemble_variance,
            ensemble_weights=result.ensemble_weights,
            
            # Policy calculations
            policy=result.policy,
            policy_multiplier=result.policy_multiplier,
            base_learning_rate=0.08,  # η = 0.08
            adjusted_learning_rate=result.learning_rate,
            
            # Transfer calculations
            transfer_amount=result.transferred_mastery,
            transfer_sources=result.transfer_sources,
            transfer_efficiency=result.transfer_efficiency,
            dependency_weights=result.transfers_applied,
            
            # ZPD calculations
            difficulty=result.difficulty,
            zpd_target=result.zpd_target,
            zpd_alignment_error=result.zpd_alignment_error,
            zpd_score=result.zpd_score,
            
            # System performance
            processing_delay=result.processing_delay,
            approximation_gap=result.approximation_gap,
            consistency_lag=result.consistency_lag,
            
            # Mathematical formulas used
            formulas=[
                "lyapunov_update",
                "bayesian_update", 
                "kalman_update",
                "ensemble_weighted",
                "policy_multiplier",
                "transfer_amount",
                "zpd_alignment",
                "approximation_gap"
            ]
        )
        
        # Add experiment context if available
        if "experiment_id" in interaction:
            log_entry.experiment_id = interaction["experiment_id"]
        if "group_assignment" in interaction:
            log_entry.group_assignment = interaction["group_assignment"]
        
        # Log the research data
        research_logger.log_learning_event(log_entry)
        
    except Exception as e:
        # Don't let logging errors break the main system
        pass

    # ============================================================================
    # 🔥 PHASE 3B: GOVERNANCE SCORING WITH NAMESPACE ISOLATION
    # ============================================================================

    def governance_score_candidate(
        self,
        candidate_concept: str,
        state_data: Dict[str, Any],
        transfer_engine: Optional[Any] = None,
        include_prospective: bool = True
    ) -> Dict[str, Any]:
        """
        🔥 PHASE 3B: Compute expected governance score for a candidate concept

        This is the CONSTITUTIONAL AUTHORITY for pre-selection governance scoring.
        The bandit consumes this output but does not compute it.

        Expected governance = Σ w_i · N(component_i) for i ∈ {challenge, uncertainty, zpd, transfer_prospective}

        Namespace isolation:
        - Expected space: challenge, uncertainty, zpd, transfer_prospective
        - Realized space: delta_m, transfer_realized (computed post-interaction)

        Args:
            candidate_concept: Concept being evaluated
            state_data: Current state {mastery, uncertainty, zpd_score, ...}
            transfer_engine: TransferLearningEngine for prospective transfer
            include_prospective: Whether to include transfer_prospective (Stage B+)

        Returns:
            Dict with expected governance components and score
        """
        # Extract expected governance signals from state
        mastery = state_data.get('mastery', 0.3)
        uncertainty = state_data.get('uncertainty', 0.1)
        zpd_score = state_data.get('zpd_score', 0.5)
        challenge = state_data.get('challenge', 0.5)

        # Compute prospective transfer if engine provided and Stage B+ active
        transfer_prospective = 0.0
        structural_utility = 0.0
        learner_readiness = 0.0

        if include_prospective and transfer_engine is not None:
            zpd_readiness = state_data.get('zpd_readiness', zpd_score)

            prospective_result = transfer_engine.estimate_prospective_transfer(
                candidate_concept=candidate_concept,
                current_mastery=mastery,
                uncertainty=uncertainty,
                zpd_readiness=zpd_readiness
            )

            transfer_prospective = prospective_result['prospective_transfer']
            structural_utility = prospective_result['structural_utility']
            learner_readiness = prospective_result['learner_readiness']

        # Normalize expected governance components
        n_challenge = self.jt_governance.normalize_component("challenge", challenge)
        n_uncertainty = self.jt_governance.normalize_component("uncertainty", uncertainty)
        n_zpd = self.jt_governance.normalize_component("zpd", zpd_score)
        n_transfer_prospective = self.jt_governance.normalize_component("transfer_prospective", transfer_prospective)

        # Compute expected governance score (4D during Stage B: challenge, uncertainty, zpd, transfer_prospective)
        weights = self.jt_governance.weights_manager.weights
        expected_governance = (
            weights.get("w4", 0.15) * n_challenge +
            weights.get("w5", 0.15) * n_uncertainty +
            weights.get("w6", 0.15) * n_zpd +
            weights.get("w3", 0.15) * n_transfer_prospective
        )

        return {
            "expected_governance": float(expected_governance),
            "n_challenge": float(n_challenge),
            "n_uncertainty": float(n_uncertainty),
            "n_zpd": float(n_zpd),
            "n_transfer_prospective": float(n_transfer_prospective),
            "transfer_prospective_raw": float(transfer_prospective),
            "structural_utility": float(structural_utility),
            "learner_readiness": float(learner_readiness),
            "namespace": "expected",
            "schema_version": self.jt_governance.jt_schema_version
        }

    def compute_realized_jt(
        self,
        delta_m: float,
        transfer_realized: float,
        challenge: float,
        uncertainty: float,
        zpd: float
    ) -> Dict[str, Any]:
        """
        🔥 PHASE 3B: Compute realized JT (post-interaction governance)

        This computes the REALIZED governance signal after interaction occurs.
        Delta_m and transfer_realized are only available post-interaction.

        Realized governance = Σ w_i · N(component_i) for i ∈ {delta_m, transfer_realized, challenge, uncertainty, zpd}

        Namespace isolation:
        - Realized space: delta_m, transfer_realized
        - Expected space: challenge, uncertainty, zpd (can also be pre-computed)

        Args:
            delta_m: Observed mastery gain (post-interaction)
            transfer_realized: Observed transfer amount (post-interaction)
            challenge: Challenge score
            uncertainty: Uncertainty score
            zpd: ZPD score

        Returns:
            Dict with realized JT value and component breakdown
        """
        # Use the 6D compute_jt method with transfer_prospective=0 for realized-only
        jt_value, contributions = self.jt_governance.compute_jt(
            delta_m=delta_m,
            transfer_realized=transfer_realized,
            transfer_prospective=0.0,  # Not available in realized space
            challenge=challenge,
            uncertainty=uncertainty,
            zpd=zpd
        )

        return {
            "realized_jt": float(jt_value),
            "contributions": contributions,
            "delta_m": float(delta_m),
            "transfer_realized": float(transfer_realized),
            "namespace": "realized",
            "schema_version": self.jt_governance.jt_schema_version,
            "weights": self.jt_governance.weights_manager.weights.copy()
        }

    def rank_candidates(
        self,
        candidates: List[str],
        state_repo: Any,
        transfer_engine: Optional[Any] = None,
        include_prospective: bool = True
    ) -> List[Tuple[str, float]]:
        """
        🔥 PHASE 3C: Constitutional authority for candidate ranking

        The unified_brain is the SOLE AUTHORITY for governance computation.
        The bandit acts as CONSUMER/ORCHESTRATOR only.

        Args:
            candidates: List of concept UUIDs to rank
            state_repo: State repository for fetching concept states
            transfer_engine: TransferLearningEngine for prospective transfer
            include_prospective: Whether to include transfer_prospective in scoring

        Returns:
            Sorted list of (concept_uuid, governance_score) tuples, descending by score
        """
        scored_candidates = []

        for concept_uuid in candidates:
            # Fetch state for this concept
            state_data = state_repo.get_state(concept_uuid) if state_repo else {}

            # Compute governance score using constitutional method
            score_result = self.governance_score_candidate(
                candidate_concept=concept_uuid,
                state_data=state_data,
                transfer_engine=transfer_engine,
                include_prospective=include_prospective
            )

            scored_candidates.append((
                concept_uuid,
                score_result["expected_governance"],
                score_result
            ))

        # Sort by governance score (descending)
        # 🔥 PHASE 5A: Use sorted() for deterministic ordering
        ranked = sorted(scored_candidates, key=lambda x: (x[1], x[0]), reverse=True)

        # Return only (concept, score) pairs
        return [(concept, score) for concept, score, _ in ranked]

    def compare_6d_vs_5d_baseline(
        self,
        candidates: List[str],
        state_repo: Any,
        transfer_engine: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        🔥 PHASE 3D: Compare 6D governance (full) vs 5D baseline (realized-only)

        6D governance includes transfer_prospective (prospective transfer).
        5D baseline excludes transfer_prospective (only realized components).

        This comparison validates the causal contribution of the sixth dimension.

        Args:
            candidates: List of concept UUIDs to compare
            state_repo: State repository for fetching concept states
            transfer_engine: TransferLearningEngine for prospective transfer computation

        Returns:
            Dict with comparison results:
            - governance_loss_6d: loss when using full 6D governance
            - governance_loss_5d: loss when using 5D baseline
            - sixth_dimension_causal: True if 6D > 5D (prospective transfer helps)
            - expected_improvement: estimated improvement from prospective transfer
        """
        import numpy as np

        # Compute 6D rankings (with prospective transfer)
        ranked_6d = self.rank_candidates(
            candidates=candidates,
            state_repo=state_repo,
            transfer_engine=transfer_engine,
            include_prospective=True
        )

        # Compute 5D rankings (without prospective transfer)
        ranked_5d = self.rank_candidates(
            candidates=candidates,
            state_repo=state_repo,
            transfer_engine=None,  # Disables prospective transfer
            include_prospective=False
        )

        # Extract scores for comparison
        scores_6d = np.array([score for _, score in ranked_6d])
        scores_5d = np.array([score for _, score in ranked_5d])

        # Compute governance loss (variance of selection distribution)
        # Lower variance = more focused selection = better governance
        governance_loss_6d = 1.0 - np.var(scores_6d) if len(scores_6d) > 1 else 1.0
        governance_loss_5d = 1.0 - np.var(scores_5d) if len(scores_5d) > 1 else 1.0

        # Normalize to [0, 1] range
        governance_loss_6d = np.clip(governance_loss_6d, 0.0, 1.0)
        governance_loss_5d = np.clip(governance_loss_5d, 0.0, 1.0)

        # Rank correlation (Kendall's tau approximation using rank positions)
        concept_to_rank_6d = {c: i for i, (c, _) in enumerate(ranked_6d)}
        concept_to_rank_5d = {c: i for i, (c, _) in enumerate(ranked_5d)}

        rank_diffs = []
        for concept in candidates:
            if concept in concept_to_rank_6d and concept in concept_to_rank_5d:
                diff = abs(concept_to_rank_6d[concept] - concept_to_rank_5d[concept])
                rank_diffs.append(diff)

        avg_rank_displacement = np.mean(rank_diffs) if rank_diffs else 0.0
        max_rank_displacement = max(rank_diffs) if rank_diffs else 0.0

        # Sixth dimension causality: 6D should have lower loss (better discrimination)
        # and meaningful rank changes
        sixth_dimension_causal = (
            governance_loss_6d < governance_loss_5d  # 6D is better
            or avg_rank_displacement > 0.5  # Meaningful ranking changes
        )

        # Expected improvement from prospective transfer
        if transfer_engine is not None:
            prospective_scores = []
            for concept in candidates:
                state = state_repo.get_state(concept) if state_repo else {}
                result = transfer_engine.estimate_prospective_transfer(
                    candidate_concept=concept,
                    current_mastery=state.get('mastery', 0.3),
                    uncertainty=state.get('uncertainty', 0.1),
                    zpd_readiness=state.get('zpd_readiness', 0.5)
                )
                prospective_scores.append(result['prospective_transfer'])

            expected_improvement = np.mean(prospective_scores) if prospective_scores else 0.0
            prospective_variance = np.var(prospective_scores) if len(prospective_scores) > 1 else 0.0
        else:
            expected_improvement = 0.0
            prospective_variance = 0.0

        return {
            "governance_loss_6d": float(governance_loss_6d),
            "governance_loss_5d": float(governance_loss_5d),
            "loss_difference": float(governance_loss_5d - governance_loss_6d),
            "sixth_dimension_causal": bool(sixth_dimension_causal),
            "avg_rank_displacement": float(avg_rank_displacement),
            "max_rank_displacement": int(max_rank_displacement),
            "expected_improvement": float(expected_improvement),
            "prospective_variance": float(prospective_variance),
            "ranked_6d": ranked_6d,
            "ranked_5d": ranked_5d,
            "comparison_mode": "6d_vs_5d_baseline",
            "schema_version": self.jt_governance.jt_schema_version if hasattr(self, 'jt_governance') else "6D.1.0"
        }
