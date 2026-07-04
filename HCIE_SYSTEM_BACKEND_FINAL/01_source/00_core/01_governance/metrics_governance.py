"""
HCIE Governance Metrics - Essential for Cognitive Governance Observatory

These metrics answer the 5 fundamental governance questions and are REQUIRED for
the cognitive governance observatory dashboard. They are operational semantics
that monitor the constitutional control architecture.

🔥 BRAIN GOVERNANCE:
- OBSERVE: All metrics here are READ-ONLY for dashboard/monitoring
- These metrics NEVER feed back into control decisions
- Control decisions are made in unified_brain.py based on JT optimization

🔥 5 CORE GOVERNANCE QUESTIONS:

1. Is cognition improving? (JT over time)
   - mastery_delta_sum, mastery_delta_count: Learning gain tracking
   - learning_curve_mastery: Mastery over time

2. Why is JT changing? (Constitutional decomposition)
   - transfer_learning_events: Knowledge propagation
   - cognitive_cost_events: Response time penalty
   - zpd_alignment_events: Task-difficulty fit
   - ensemble_variance: Uncertainty between learners

3. Is governance stable? (Control-theoretic stability)
   - learning_efficiency_raw_eta: Adaptive learning rate
   - control_path_entropy: Governance diversity
   - governance_violation_count: Architectural integrity
   - bandit_exploration_events: Exploration pressure

4. Are learners specializing? (JT-attributed ensemble)
   - lyapunov_mastery, bayesian_mastery, kalman_mastery: Learner contributions
   - ensemble_variance: Specialization indicators

5. Is the system behaving coherently? (Architectural integrity)
   - governance_violation_count: Governance violations
   - canonical_state_misses: State consistency
   - duplicate_event_count: Replay consistency
   - jt_dependency_ratio: Constitutional alignment
"""

from prometheus_client import (
    Counter as _PromCounter,
    Histogram as _PromHistogram,
    Gauge as _PromGauge,
    CollectorRegistry,
)

# Phase 9 split-residue fix: keep FINAL-only governance metrics out of the
# global registry when BACKENDV2 has already registered the same names.
_LOCAL_REGISTRY = CollectorRegistry(auto_describe=True)


def Counter(*args, **kwargs):
    kwargs.setdefault("registry", _LOCAL_REGISTRY)
    return _PromCounter(*args, **kwargs)


def Histogram(*args, **kwargs):
    kwargs.setdefault("registry", _LOCAL_REGISTRY)
    return _PromHistogram(*args, **kwargs)


def Gauge(*args, **kwargs):
    kwargs.setdefault("registry", _LOCAL_REGISTRY)
    return _PromGauge(*args, **kwargs)

# Import shared metrics from metrics.py to avoid duplication
# These metrics are defined in metrics.py and imported here for backward compatibility
from ..research.metrics import (
    canonical_reads,
    canonical_misses,
    state_source_counter,
    cold_start_events,
    learning_events,
    mastery_updates,
    mastery_delta_histogram,
    mastery_delta_sum,
    mastery_delta_count,
    lyapunov_mastery,
    bayesian_mastery,
    kalman_mastery,
    ensemble_variance,
    transfer_learning_events,
    cognitive_cost_events,
    zpd_alignment_events,
    bandit_exploration_events,
    duplicate_event_count,
    adaptive_learning_rate,
    learning_efficiency_raw_eta,
    learning_efficiency_raw_delta,
    learning_curve_mastery
)

# ==============================
# 🧠 STATE VALIDITY METRICS
# ==============================
# NOTE: These metrics are now imported from metrics.py to avoid Prometheus duplication
# Commented out registrations kept for reference during migration:

# canonical_reads = Counter(
#     "hcie_canonical_state_reads_total",
#     "Total canonical state reads from Postgres"
# )
#
# canonical_misses = Counter(
#     "hcie_canonical_state_misses_total",
#     "Total canonical state misses (cold starts)"
# )
#
# state_source_counter = Counter(
#     "hcie_learning_state_source_total",
#     "Total learning operations by state source",
#     ["state_source"]  # canonical | default_fallback | error_fallback
# )
#
# cold_start_events = Counter(
#     "hcie_cold_start_events_total",
#     "Cold start occurrences"
# )

# ==============================
# ⚡ LEARNING SIGNAL METRICS (Essential)
# ==============================
# NOTE: These metrics are now imported from metrics.py to avoid Prometheus duplication
# Commented out registrations kept for reference during migration:

# learning_events = Counter(
#     "hcie_learning_events_total",
#     "Total learning events processed",
#     ["concept", "user_type"]
# )
#
# mastery_updates = Counter(
#     "hcie_mastery_updates_total",
#     "Total mastery updates",
#     ["concept", "user_type"]
# )
#
# mastery_delta_histogram = Histogram(
#     "hcie_mastery_delta_histogram",
#     "Mastery changes (ΔM) for learning gain analysis",
#     ["concept", "user_type", "mode"],
#     buckets=[-0.1, -0.05, -0.02, -0.01, 0, 0.01, 0.02, 0.05, 0.1]
# )
#
# mastery_delta_sum = Counter(
#     "hcie_mastery_delta_sum_total",
#     "Sum of mastery deltas (cumulative learning)",
#     ["concept", "user_type", "mode"]
# )
#
# mastery_delta_count = Counter(
#     "hcie_mastery_delta_count_total",
#     "Total number of mastery delta observations",
#     ["concept", "user_type", "mode"]
# )

# ==============================
# 🧠 LEARNER STATE METRICS (Essential)
# ==============================
# NOTE: These metrics are now imported from metrics.py to avoid Prometheus duplication
# Commented out registrations kept for reference during migration:

# lyapunov_mastery = Gauge(
#     "hcie_lyapunov_mastery",
#     "Lyapunov learner mastery (stability specialist)",
#     ["concept", "user_type"]
# )
#
# bayesian_mastery = Gauge(
#     "hcie_bayesian_mastery",
#     "Bayesian learner mastery (evidence specialist)",
#     ["concept", "user_type"]
# )
#
# kalman_mastery = Gauge(
#     "hcie_kalman_mastery",
#     "Kalman learner mastery (transition specialist)",
#     ["concept", "user_type"]
# )
#
# ensemble_variance = Gauge(
#     "hcie_ensemble_variance",
#     "Ensemble variance (uncertainty between learners)",
#     ["concept", "user_type"]
# )

# ==============================
# 🔥 CONSTITUTIONAL DECOMPOSITION METRICS (Essential)
# ==============================
# NOTE: These metrics are now imported from metrics.py to avoid Prometheus duplication
# Commented out registrations kept for reference during migration:

# transfer_learning_events = Counter(
#     "hcie_transfer_learning_events_total",
#     "Transfer learning events (knowledge propagation)",
#     ["concept", "user_type"]
# )
#
# cognitive_cost_events = Counter(
#     "hcie_cognitive_cost_events_total",
#     "Cognitive cost events (response time penalty)",
#     ["concept", "user_type"]
# )
#
# zpd_alignment_events = Counter(
#     "hcie_zpd_alignment_events_total",
#     "ZPD alignment events (task-difficulty fit)",
#     ["concept", "user_type"]
# )
#
# bandit_exploration_events = Counter(
#     "hcie_bandit_exploration_events_total",
#     "Bandit exploration events (governance confidence response)",
#     ["concept", "user_type"]
# )
#
# duplicate_event_count = Counter(
#     "hcie_duplicate_event_count",
#     "Duplicate event count (replay consistency)",
#     ["concept", "user_type"]
# )

# ==============================
# 🔥 ADAPTIVE LEARNING METRICS (Essential)
# ==============================
# NOTE: These metrics are now imported from metrics.py to avoid Prometheus duplication
# Commented out registrations kept for reference during migration:

# adaptive_learning_rate = Histogram(
#     "hcie_adaptive_learning_rate",
#     "Adaptive learning rate η(t) distribution",
#     ["user_id", "concept", "user_type"],
#     buckets=[0.01, 0.02, 0.04, 0.08, 0.12, 0.16, 0.20, 0.24, 0.28, 0.32]
# )
#
# learning_efficiency_raw_eta = Gauge(
#     "hcie_learning_efficiency_raw_eta",
#     "Raw η(t) value for governance stability monitoring",
#     ["user_id", "concept", "user_type", "event_id"]
# )
#
# learning_efficiency_raw_delta = Gauge(
#     "hcie_learning_efficiency_raw_delta",
#     "Raw ΔM value for governance stability monitoring",
#     ["user_id", "concept", "user_type", "event_id"]
# )

# ==============================
# 🔥 LONGITUDINAL TRACKING (Essential)
# ==============================
# NOTE: These metrics are now imported from metrics.py to avoid Prometheus duplication
# Commented out registrations kept for reference during migration:

# learning_curve_mastery = Gauge(
#     "hcie_learning_curve_mastery",
#     "Mastery over time for longitudinal analysis",
#     ["user_id", "concept", "user_type", "mode", "time_bucket"]
# )

# ==============================
# 🔥 GOVERNANCE METRICS (Essential)
# ==============================

governance_validation_success = Counter(
    "hcie_governance_validation_success_total",
    "Successful governance validations",
    ["validation_type"]  # jt_centrality, control_validation, observe_readonly
)

governance_validation_failure = Counter(
    "hcie_governance_validation_failure_total",
    "Failed governance validations",
    ["validation_type"]
)

governance_violation_count = Gauge(
    "hcie_governance_violation_count",
    "Current count of governance violations",
    ["violation_type"]
)

jt_dependency_ratio = Gauge(
    "hcie_jt_dependency_ratio",
    "Ratio of control variables that are JT-driven (0-1)",
    ["component"]  # eta, bandit, policy, ensemble
)

control_path_entropy = Gauge(
    "hcie_control_path_entropy",
    "Entropy of control path decisions (higher = more diverse paths)",
    ["component"]
)

objective_alignment_score = Gauge(
    "hcie_objective_alignment_score",
    "Alignment of subsystems with JT objective (0-1, higher = better)",
    ["subsystem"]  # bandit, ensemble, policy, transfer
)

# ==============================
# 🔥 PERSISTENCE GOVERNANCE METRICS (Essential)
# ==============================

persistence_write_success = Counter(
    "hcie_persistence_write_success_total",
    "Successful persistence writes",
    ["persistence_type"]  # state, trace, metrics
)

persistence_write_failure = Counter(
    "hcie_persistence_write_failure_total",
    "Failed persistence writes",
    ["persistence_type"]
)

persistence_consistency_violation = Counter(
    "hcie_persistence_consistency_violation_total",
    "Persistence consistency violations (false-positive success, rollback mismatch)",
    ["violation_type"]
)

# ==============================
# 🔥 UTILITY FUNCTIONS
# ==============================

def start_metrics_server(port: int = 8002):
    """Start Prometheus metrics server for learning consumer"""
    from prometheus_client import start_http_server
    start_http_server(port)

def record_governance_validation(validation_type: str, success: bool):
    """Record governance validation result"""
    if success:
        governance_validation_success.labels(validation_type=validation_type).inc()
    else:
        governance_validation_failure.labels(validation_type=validation_type).inc()

def record_governance_violation(violation_type: str):
    """Record governance violation"""
    governance_violation_count.labels(violation_type=violation_type).inc()

def record_jt_dependency(component: str, ratio: float):
    """Record JT dependency ratio for a component"""
    jt_dependency_ratio.labels(component=component).set(ratio)

def record_control_path_entropy(component: str, entropy: float):
    """Record control path entropy for a component"""
    control_path_entropy.labels(component=component).set(entropy)

def record_objective_alignment(subsystem: str, score: float):
    """Record objective alignment score for a subsystem"""
    objective_alignment_score.labels(subsystem=subsystem).set(score)

def record_persistence_write(persistence_type: str, success: bool):
    """Record persistence write result"""
    if success:
        persistence_write_success.labels(persistence_type=persistence_type).inc()
    else:
        persistence_write_failure.labels(persistence_type=persistence_type).inc()

def record_persistence_violation(violation_type: str):
    """Record persistence consistency violation"""
    persistence_consistency_violation.labels(violation_type=violation_type).inc()

def record_state_load(state_source: str, cold_start: bool = False):
    """Record state load event"""
    state_source_counter.labels(state_source=state_source).inc()
    if cold_start:
        cold_start_events.inc()

def record_ensemble_variance(concept: str, user_type: str, mode: str, variance: float):
    """Record ensemble variance for governance monitoring"""
    ensemble_variance.labels(concept=concept, user_type=user_type, mode=mode).set(variance)

def record_learning_event(concept: str, user_type: str):
    """Record learning event"""
    learning_events.labels(concept=concept, user_type=user_type).inc()

def record_mastery_update(concept: str, user_type: str):
    """Record mastery update"""
    mastery_updates.labels(concept=concept, user_type=user_type).inc()
