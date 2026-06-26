"""
HCIE Learning Metrics - DEPRECATED

🔥 SEMANTIC NORMALIZATION IN PROGRESS:
This file is being split by responsibility as part of P2 semantic normalization.
Metrics are being moved to:
- metrics_governance.py: Governance and cognitive state observability
- metrics_runtime.py: Runtime learning signal metrics
- metrics_research.py: Research-specific metrics (power analysis, ablation, etc.)
- metrics_persistence.py: State validity and persistence governance

🔥 CURRENT STATUS:
This file remains for backward compatibility during migration.
DO NOT add new metrics to this file.
Import from the split files instead.
"""

from prometheus_client import (
    Counter as _PromCounter,
    Histogram as _PromHistogram,
    Gauge as _PromGauge,
    CollectorRegistry,
)

# Phase 9 split-residue fix:
# FINAL can be imported alongside BACKENDV2 during shim smoke tests. Use a
# module-local registry so duplicate metric names do not collide in the
# prometheus_client default registry at import time.
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

# ==============================
# 🧠 STATE VALIDITY METRICS
# ==============================

canonical_reads = Counter(
    "hcie_canonical_state_reads_total",
    "Total canonical state reads from Postgres"
)

canonical_misses = Counter(
    "hcie_canonical_state_misses_total", 
    "Total canonical state misses (cold starts)"
)

state_source_counter = Counter(
    "hcie_learning_state_source_total",
    "Total learning operations by state source",
    ["state_source"]  # canonical | default_fallback | error_fallback
)

cold_start_events = Counter(
    "hcie_cold_start_events_total",
    "Cold start occurrences"
)

# ==============================
# ⚡ LEARNING SIGNAL METRICS
# ==============================

learning_events = Counter(
    "hcie_learning_events_total",
    "Total learning events processed",
    ["concept", "user_type"]
)

mastery_updates = Counter(
    "hcie_mastery_updates_total",
    "Total mastery updates",
    ["concept", "user_type"]
)

mastery_delta_histogram = Histogram(
    "hcie_mastery_delta_histogram",
    "Mastery changes (ΔM) for learning gain analysis",
    ["concept", "user_type", "mode"],
    buckets=[-0.1, -0.05, -0.02, -0.01, 0, 0.01, 0.02, 0.05, 0.1]
)

mastery_delta_sum = Counter(
    "hcie_mastery_delta_sum_total",
    "Sum of mastery deltas (cumulative learning)",
    ["concept", "user_type", "mode"]
)

mastery_delta_count = Counter(
    "hcie_mastery_delta_count_total", 
    "Total number of mastery delta observations",
    ["concept", "user_type", "mode"]
)

mastery_delta_sq_sum = Counter(
    "hcie_mastery_delta_sq_sum_total",
    "Sum of squared mastery deltas for variance calculation",
    ["concept", "user_type", "mode"]
)

# Metrics health monitoring
metrics_success = Counter(
    "hcie_metrics_success_total",
    "Successful metric recordings"
)

metrics_failure = Counter(
    "hcie_metrics_failure_total", 
    "Failed metric recordings"
)

# Power analysis metrics
statistical_power = Gauge(
    "hcie_statistical_power",
    "Current statistical power (1 - β)",
    ["comparison"]
)

required_sample_size = Gauge(
    "hcie_required_sample_size", 
    "Required sample size for 80% power",
    ["comparison"]
)

effect_size_cohen_d = Gauge(
    "hcie_effect_size_cohen_d",
    "Cohen's d effect size",
    ["comparison"]
)

# Longitudinal tracking metrics
learning_curve_mastery = Gauge(
    "hcie_learning_curve_mastery",
    "Mastery over time for longitudinal analysis",
    ["user_id", "concept", "user_type", "mode", "time_bucket"]
)

convergence_rate = Gauge(
    "hcie_convergence_rate",
    "Rate of mastery convergence",
    ["user_id", "concept", "user_type", "mode"]
)

retention_score = Gauge(
    "hcie_retention_score",
    "Knowledge retention over time",
    ["user_id", "concept", "user_type", "mode"]
)

# Optional: distribution (better for research)
mastery_delta_distribution = Histogram(
    "hcie_mastery_delta_distribution",
    "Distribution of mastery delta",
    ["concept", "user_type"],
    buckets=[-1, -0.5, -0.1, 0, 0.1, 0.3, 0.5, 1]
)

# 🔥 RESEARCH: Joint metric for η(t) vs ΔM scatter plot analysis
learning_efficiency_scatter = Gauge(
    "hcie_learning_efficiency_point",
    "Joint η(t) and ΔM for scatter plot analysis",
    ["user_id", "concept", "user_type", "eta_bucket", "delta_bucket"]
)

# 🔥 CONVERGENCE: Track mastery progression over time
mastery_convergence_curve = Gauge(
    "hcie_mastery_convergence_curve",
    "Mastery value over time for convergence analysis",
    ["user_id", "concept", "user_type", "time_bucket"]
)

learning_events_counter = Counter(
    "hcie_learning_events_counter",
    "Count of learning events per user for time series analysis",
    ["user_id", "concept", "user_type"]
)

# 🔥 ABLATION: Compare adaptive vs fixed learning rates
ablation_learning_efficiency = Gauge(
    "hcie_ablation_learning_efficiency",
    "Learning efficiency comparison: adaptive vs fixed η(t)",
    ["user_id", "concept", "user_type", "mode", "eta_value"]
)

ablation_convergence_rate = Gauge(
    "hcie_ablation_convergence_rate",
    "Convergence rate comparison: adaptive vs fixed η(t)",
    ["user_type", "mode", "eta_value"]
)

# 🔥 CAUSAL: Raw η(t) and ΔM pairs for regression analysis
learning_efficiency_raw_eta = Gauge(
    "hcie_learning_efficiency_raw_eta",
    "Raw η(t) value for causal analysis",
    ["user_id", "concept", "user_type", "event_id"]
)

learning_efficiency_raw_delta = Gauge(
    "hcie_learning_efficiency_raw_delta",
    "Raw ΔM value for causal analysis", 
    ["user_id", "concept", "user_type", "event_id"]
)

# ==============================
# 🧠 LEARNER STATE METRICS
# ==============================

lyapunov_mastery = Gauge(
    "hcie_lyapunov_mastery",
    "Lyapunov learner mastery",
    ["concept", "user_type"]
)

bayesian_mastery = Gauge(
    "hcie_bayesian_mastery",
    "Bayesian learner mastery",
    ["concept", "user_type"]
)

kalman_mastery = Gauge(
    "hcie_kalman_mastery",
    "Kalman learner mastery",
    ["concept", "user_type"]
)

ensemble_variance = Gauge(
    "hcie_ensemble_variance",
    "Ensemble variance (uncertainty between learners)",
    ["concept", "user_type"]
)

# ==============================
# 🔥 CONSTITUTIONAL DECOMPOSITION METRICS
# ==============================

transfer_learning_events = Counter(
    "hcie_transfer_learning_events_total",
    "Transfer learning events (knowledge propagation)",
    ["concept", "user_type"]
)

cognitive_cost_events = Counter(
    "hcie_cognitive_cost_events_total",
    "Cognitive cost events (response time penalty)",
    ["concept", "user_type"]
)

zpd_alignment_events = Counter(
    "hcie_zpd_alignment_events_total",
    "ZPD alignment events (task-difficulty fit)",
    ["concept", "user_type"]
)

bandit_exploration_events = Counter(
    "hcie_bandit_exploration_events_total",
    "Bandit exploration events (governance confidence response)",
    ["concept", "user_type"]
)

duplicate_event_count = Counter(
    "hcie_duplicate_event_count",
    "Duplicate event count (replay consistency)",
    ["concept", "user_type"]
)

# ==============================
# 🔥 ADAPTIVE LEARNING METRICS
# ==============================

adaptive_learning_rate = Histogram(
    "hcie_adaptive_learning_rate",
    "Adaptive learning rate η(t) distribution",
    ["user_id", "concept", "user_type"],
    buckets=[0.01, 0.02, 0.04, 0.08, 0.12, 0.16, 0.20, 0.24, 0.28, 0.32]
)

adaptive_learning_rate_gauge = Gauge(
    "hcie_adaptive_learning_rate_gauge",
    "Current adaptive learning rate η(t) per learner and concept",
    ["user_id", "concept", "user_type", "mode"]
)

response_time_seconds = Histogram(
    "hcie_response_time_seconds",
    "Response time distribution",
    ["concept", "correct"],
    buckets=[1, 2, 5, 10, 20, 30, 60, 120]
)

correctness_impact = Gauge(
    "hcie_correctness_impact",
    "Impact of answer correctness on η(t)",
    ["concept"]
)

energy_violations = Counter(
    "hcie_energy_violations_total",
    "Energy constraint violations",
    ["constraint_type"]
)

# ==============================
# 🎰 BANDIT INTELLIGENCE METRICS
# ==============================

bandit_exploration = Counter(
    "hcie_bandit_exploration_total",
    "Bandit exploration decisions"
)

bandit_exploitation = Counter(
    "hcie_bandit_exploitation_total",
    "Bandit exploitation decisions"
)

bandit_actions = Counter(
    "hcie_bandit_actions_total",
    "Bandit action selections",
    ["concept"]
)

# ==============================
# 🧠 COGNITIVE STATE METRICS (Unified Brain)
# ==============================

objective_function_J = Gauge(
    "hcie_objective_function_J",
    "Objective function J_t value (optimization target)",
    ["user_id", "concept", "user_type", "mode"]
)

zpd_alignment_score = Gauge(
    "hcie_zpd_alignment_score",
    "Zone of Proximal Development alignment (0-1, higher = better alignment)",
    ["user_id", "concept", "user_type", "mode"]
)

zpd_target_difficulty = Gauge(
    "hcie_zpd_target_difficulty",
    "Concept difficulty (ZPD target)",
    ["concept"]
)

zpd_alignment_error = Gauge(
    "hcie_zpd_alignment_error",
    "Distance from optimal ZPD (lower = better)",
    ["user_id", "concept", "user_type", "mode"]
)

transfer_learning_amount = Gauge(
    "hcie_transfer_learning_amount",
    "Amount of knowledge transferred from prerequisite concepts",
    ["user_id", "concept", "user_type", "mode"]
)

transfer_learning_efficiency = Gauge(
    "hcie_transfer_learning_efficiency",
    "Efficiency of transfer learning (0-1, higher = better)",
    ["user_id", "concept", "user_type", "mode"]
)

uncertainty_gauge = Gauge(
    "hcie_uncertainty",
    "Model uncertainty (confidence complement)",
    ["user_id", "concept", "user_type", "mode"]
)

confidence_gauge = Gauge(
    "hcie_confidence",
    "Model confidence (1 - uncertainty)",
    ["user_id", "concept", "user_type", "mode"]
)

ensemble_weight_lyapunov = Gauge(
    "hcie_ensemble_weight_lyapunov",
    "Ensemble weight for Lyapunov learner",
    ["user_id", "concept", "user_type", "mode"]
)

ensemble_weight_bayesian = Gauge(
    "hcie_ensemble_weight_bayesian",
    "Ensemble weight for Bayesian learner",
    ["user_id", "concept", "user_type", "mode"]
)

ensemble_weight_kalman = Gauge(
    "hcie_ensemble_weight_kalman",
    "Ensemble weight for Kalman learner",
    ["user_id", "concept", "user_type", "mode"]
)

# ==============================
# GOVERNANCE METRICS (Architectural Observability)
# ==============================
# NOTE: Governance metrics moved to metrics_governance.py to avoid duplication
# Commented out registrations kept for reference during migration:

# governance_validation_success = Counter(
#     "hcie_governance_validation_success_total",
#     "Successful governance validations",
#     ["validation_type"]  # jt_centrality, control_validation, observe_readonly
# )
#
# governance_validation_failure = Counter(
#     "hcie_governance_validation_failure_total",
#     "Failed governance validations",
#     ["validation_type"]
# )
#
# governance_violation_count = Gauge(
#     "hcie_governance_violation_count",
#     "Current count of governance violations",
#     ["violation_type"]
# )
#
# jt_dependency_ratio = Gauge(
#     "hcie_jt_dependency_ratio",
#     "Ratio of control variables that are JT-driven (0-1)",
#     ["component"]  # eta, bandit, policy, ensemble
# )
#
# control_path_entropy = Gauge(
#     "hcie_control_path_entropy",
#     "Entropy of control path decisions (higher = more diverse paths)",
#     ["component"]
# )
#
# objective_alignment_score = Gauge(
#     "hcie_objective_alignment_score",
#     "Alignment of subsystems with JT objective (0-1, higher = better)",
#     ["subsystem"]  # bandit, ensemble, policy, transfer
# )

# ==============================
# PERSISTENCE GOVERNANCE METRICS
# ==============================
# NOTE: Persistence metrics moved to metrics_governance.py to avoid duplication
# Commented out registrations kept for reference during migration:

# persistence_write_success = Counter(
#     "hcie_persistence_write_success_total",
#     "Successful persistence writes",
#     ["persistence_type"]  # state, trace, metrics
# )
#
# persistence_write_failure = Counter(
#     "hcie_persistence_write_failure_total",
#     "Failed persistence writes",
#     ["persistence_type"]
# )
#
# persistence_consistency_violation = Counter(
#     "hcie_persistence_consistency_violation_total",
#     "Persistence consistency violations (false-positive success, rollback mismatch)",
#     ["violation_type"]
# )


class _NoopMetric:
    """Compatibility placeholder for metrics split into dedicated modules."""

    def labels(self, **_labels):
        return self

    def inc(self, *_args, **_kwargs):
        return None

    def set(self, *_args, **_kwargs):
        return None


governance_validation_success = _NoopMetric()
governance_validation_failure = _NoopMetric()
governance_violation_count = _NoopMetric()
jt_dependency_ratio = _NoopMetric()
control_path_entropy = _NoopMetric()
objective_alignment_score = _NoopMetric()
persistence_write_success = _NoopMetric()
persistence_write_failure = _NoopMetric()
persistence_consistency_violation = _NoopMetric()

# ==============================
# � UTILITY FUNCTIONS
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
    """Record state loading metrics"""
    if state_source == "canonical":
        canonical_reads.inc()
    else:
        canonical_misses.inc()
    
    state_source_counter.labels(state_source=state_source).inc()
    
    if cold_start:
        cold_start_events.inc()

def record_learning_update(mastery_before: float, mastery_after: float, concept: str, user_type: str, mode: str = "adaptive"):
    """Record learning update metrics"""
    learning_events.labels(concept=concept, user_type=user_type).inc()
    mastery_updates.labels(concept=concept, user_type=user_type).inc()
    
    # Handle None values for mastery
    if mastery_before is None:
        mastery_before = 0.0
    if mastery_after is None:
        mastery_after = 0.0
    
    # Record mastery delta for learning gain analysis
    mastery_delta = mastery_after - mastery_before
    mastery_delta_histogram.labels(concept=concept, user_type=user_type, mode=mode).observe(mastery_delta)
    
    # Handle negative deltas properly for Prometheus counters
    if mastery_delta >= 0:
        mastery_delta_sum.labels(concept=concept, user_type=user_type, mode=mode).inc(mastery_delta)
        mastery_delta_sq_sum.labels(concept=concept, user_type=user_type, mode=mode).inc(mastery_delta * mastery_delta)
    else:
        # For negative deltas, we need to use a gauge or handle differently
        # For now, just record the absolute value in the histogram
        # But still track variance using squared values
        mastery_delta_sq_sum.labels(concept=concept, user_type=user_type, mode=mode).inc(mastery_delta * mastery_delta)
    
    mastery_delta_count.labels(concept=concept, user_type=user_type, mode=mode).inc()

def calculate_power_analysis(
    comparison_name: str,
    mean1: float,
    mean2: float,
    var1: float,
    var2: float,
    n1: int,
    n2: int
):
    """
    Calculate statistical power and effect size metrics
    """
    try:
        # Pooled standard deviation
        pooled_sd = (( (n1 - 1) * var1 + (n2 - 1) * var2 ) / (n1 + n2 - 2)) ** 0.5
        
        # Cohen's d effect size
        if pooled_sd > 0:
            cohens_d = abs(mean1 - mean2) / pooled_sd
        else:
            cohens_d = 0.0
        
        # Required sample size for 80% power (simplified approximation)
        # n ≈ 16 / d² for two-tailed test with 80% power
        if cohens_d > 0:
            required_n = int(16 / (cohens_d ** 2))
        else:
            required_n = 1000  # Large number for zero effect
        
        # Current statistical power (simplified)
        # Power increases with sample size and effect size
        current_n = min(n1, n2)
        if required_n > 0:
            power = min(0.99, (current_n / required_n) * 0.8)
        else:
            power = 0.0
        
        # Record metrics
        effect_size_cohen_d.labels(comparison=comparison_name).set(cohens_d)
        required_sample_size.labels(comparison=comparison_name).set(required_n)
        statistical_power.labels(comparison=comparison_name).set(power)
        
        print(f"🔬 POWER ANALYSIS [{comparison_name}]:")
        print(f"  Effect size (Cohen's d): {cohens_d:.3f}")
        print(f"  Required n for 80% power: {required_n}")
        print(f"  Current power: {power:.3f}")
        
    except Exception as e:
        print(f"❌ Power analysis failed: {e}")

def record_full_learning_event(
    *,
    user_id: str,
    concept: str,
    user_type: str,
    mode: str,
    eta: float,
    mastery_before: float,
    mastery_after: float,
    lyapunov: float,
    bayesian_alpha: float,
    bayesian_beta: float,
    kalman: float,
    event_id: str,
    # Cognitive state metrics (optional for backward compatibility)
    J_value: float = 0.0,
    zpd_score_val: float = 0.5,
    zpd_target_val: float = 0.3,
    zpd_alignment_error_val: float = 0.0,
    transfer_amount_val: float = 0.0,
    transfer_efficiency_val: float = 0.0,
    uncertainty_val: float = 0.2,
    confidence_val: float = 0.8,
    ensemble_weights_val: dict = None
):
    """
    🔥 SINGLE SOURCE OF TRUTH for all metrics
    """
    try:
        delta_m = mastery_after - mastery_before

        # 1. Core learning
        record_learning_update(mastery_before, mastery_after, concept, user_type, mode)

        # 2. Adaptive rate
        adaptive_learning_rate_gauge.labels(
            user_id=user_id,
            concept=concept,
            user_type=user_type,
            mode=mode
        ).set(eta)

        # 3. Learner states + variance (ONLY PLACE variance is computed)
        record_learner_states(
            lyapunov_value=lyapunov,
            bayesian_alpha=bayesian_alpha,
            bayesian_beta=bayesian_beta,
            kalman_value=kalman,
            concept=concept,
            user_type=user_type,
            mode=mode
        )

        # 4. Cognitive state metrics (NEW - Unified Brain internals)
        objective_function_J.labels(
            user_id=user_id,
            concept=concept,
            user_type=user_type,
            mode=mode
        ).set(J_value)

        zpd_alignment_score.labels(
            user_id=user_id,
            concept=concept,
            user_type=user_type,
            mode=mode
        ).set(zpd_score_val)

        zpd_target_difficulty.labels(concept=concept).set(zpd_target_val)

        zpd_alignment_error.labels(
            user_id=user_id,
            concept=concept,
            user_type=user_type,
            mode=mode
        ).set(zpd_alignment_error_val)

        transfer_learning_amount.labels(
            user_id=user_id,
            concept=concept,
            user_type=user_type,
            mode=mode
        ).set(transfer_amount_val)

        transfer_learning_efficiency.labels(
            user_id=user_id,
            concept=concept,
            user_type=user_type,
            mode=mode
        ).set(transfer_efficiency_val)

        uncertainty_gauge.labels(
            user_id=user_id,
            concept=concept,
            user_type=user_type,
            mode=mode
        ).set(uncertainty_val)

        confidence_gauge.labels(
            user_id=user_id,
            concept=concept,
            user_type=user_type,
            mode=mode
        ).set(confidence_val)

        # Ensemble weights
        if ensemble_weights_val:
            ensemble_weight_lyapunov.labels(
                user_id=user_id,
                concept=concept,
                user_type=user_type,
                mode=mode
            ).set(ensemble_weights_val.get('lyapunov', 0.33))

            ensemble_weight_bayesian.labels(
                user_id=user_id,
                concept=concept,
                user_type=user_type,
                mode=mode
            ).set(ensemble_weights_val.get('bayesian', 0.33))

            ensemble_weight_kalman.labels(
                user_id=user_id,
                concept=concept,
                user_type=user_type,
                mode=mode
            ).set(ensemble_weights_val.get('kalman', 0.34))

        # 5. Causal pair (η, ΔM ONLY — no variance here)
        record_causal_pair(
            user_id=user_id,
            concept=concept,
            user_type=user_type,
            eta=eta,
            delta_m=delta_m,
            event_id=event_id
        )

        # 6. Scatter
        record_learning_efficiency_point(
            user_id, concept, user_type, eta, delta_m
        )

        # 7. Ablation
        record_ablation_point(
            user_id, concept, user_type, mode, eta, mastery_after, delta_m
        )

        metrics_success.inc()
        
    except Exception as e:
        metrics_failure.inc()
        print(f"❌ METRICS ERROR (safe): {e}")

def safe_float(value, default=0.0):
    """Convert value to float with None guard"""
    return default if value is None else float(value)

def record_learner_states(lyapunov_value: float, bayesian_alpha: float, 
                         bayesian_beta: float, kalman_value: float, concept: str, user_type: str, mode: str = "adaptive"):
    """Record learner state metrics"""
    # Apply None guards before any arithmetic
    lyapunov_value = safe_float(lyapunov_value)
    bayesian_alpha = safe_float(bayesian_alpha)
    bayesian_beta = safe_float(bayesian_beta, 1.0)  # Default to 1.0 to avoid division by zero
    kalman_value = safe_float(kalman_value)
    
    lyapunov_mastery.labels(concept=concept, user_type=user_type).set(lyapunov_value)
    
    # Convert Bayesian alpha/beta to mastery value
    bayesian_sum = bayesian_alpha + bayesian_beta
    if bayesian_sum > 0:
        bayesian_value = bayesian_alpha / bayesian_sum
    else:
        bayesian_value = 0.0
    bayesian_mastery.labels(concept=concept, user_type=user_type).set(bayesian_value)
    
    kalman_mastery.labels(concept=concept, user_type=user_type).set(kalman_value)
    
    # Calculate ensemble variance
    variance = (lyapunov_value**2 + bayesian_value**2 + kalman_value**2) / 3 - \
               ((lyapunov_value + bayesian_value + kalman_value) / 3)**2
    ensemble_variance.labels(concept=concept, user_type=user_type).set(variance)

def record_learning_efficiency_point(user_id: str, concept: str, user_type: str, eta: float, delta_m: float):
    """Record joint η(t) and ΔM for scatter plot analysis"""
    
    # Bucket η(t) for better visualization
    eta_buckets = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
    eta_bucket = "low"
    for i, bucket in enumerate(eta_buckets[1:]):
        if eta <= bucket:
            eta_bucket = f"{eta_buckets[i]:.2f}-{bucket:.2f}"
            break
    else:
        eta_bucket = f"{eta_buckets[-1]:.2f}+"
    
    # Bucket ΔM for better visualization
    delta_buckets = [-0.1, 0.0, 0.01, 0.02, 0.03, 0.05, 0.1]
    delta_bucket = "negative"
    for i, bucket in enumerate(delta_buckets[1:]):
        if delta_m <= bucket:
            delta_bucket = f"{delta_buckets[i]:.2f}-{bucket:.2f}"
            break
    else:
        delta_bucket = f"{delta_buckets[-1]:.2f}+"
    
    # Record the joint point
    learning_efficiency_scatter.labels(
        user_id=user_id,
        concept=concept,
        user_type=user_type,
        eta_bucket=eta_bucket,
        delta_bucket=delta_bucket
    ).set(1.0)  # Use 1.0 as a marker value

def record_convergence_point(user_id: str, concept: str, user_type: str, mastery: float, event_count: int):
    """Record mastery progression for convergence curve analysis"""
    import time
    
    # Time bucket (5-minute intervals for convergence analysis)
    time_bucket = str(int(time.time() // 300))  # 5-minute buckets
    
    # Record mastery value at this time point
    mastery_convergence_curve.labels(
        user_id=user_id,
        concept=concept,
        user_type=user_type,
        time_bucket=time_bucket
    ).set(mastery)
    
    # Count learning events
    learning_events_counter.labels(
        user_id=user_id,
        concept=concept,
        user_type=user_type
    ).inc()

def record_ablation_point(user_id: str, concept: str, user_type: str, mode: str, eta: float, mastery: float, delta_m: float):
    """Record ablation study comparison between adaptive and fixed η(t)"""
    
    # Format η value for label
    eta_str = f"{eta:.3f}"
    
    # Learning efficiency (ΔM per η unit)
    efficiency = delta_m / eta if eta > 0 else 0
    ablation_learning_efficiency.labels(
        user_id=user_id,
        concept=concept,
        user_type=user_type,
        mode=mode,
        eta_value=eta_str
    ).set(efficiency)
    
    # Convergence rate (mastery achieved)
    ablation_convergence_rate.labels(
        user_type=user_type,
        mode=mode,
        eta_value=eta_str
    ).set(mastery)

def record_causal_pair(user_id: str, concept: str, user_type: str, eta: float, delta_m: float, event_id: str):
    """Record raw η(t) and ΔM pairs for causal regression analysis"""
    
    # Store raw values with event_id for pairing
    learning_efficiency_raw_eta.labels(
        user_id=user_id,
        concept=concept,
        user_type=user_type,
        event_id=event_id
    ).set(eta)
    
    learning_efficiency_raw_delta.labels(
        user_id=user_id,
        concept=concept,
        user_type=user_type,
        event_id=event_id
    ).set(delta_m)
    
    print(f"🔬 CAUSAL: η={eta:.4f}, ΔM={delta_m:.4f} [{user_type}] event={event_id[:8]}")
    
    # Note: Ensemble variance is recorded separately in record_learner_states
    # to avoid duplicate computation and maintain single source of truth

def record_adaptive_metrics(user_id: str, concept: str, eta: float, response_time: float, is_correct: bool, user_type: str = "unknown"):
    """Record adaptive learning metrics"""
    try:
        adaptive_learning_rate.labels(user_id=user_id, concept=concept, user_type=user_type).observe(eta)
    except Exception as e:
        print(f"⚠️ Histogram registration failed: {e}")
    
    # Use gauge as fallback
    adaptive_learning_rate_gauge.labels(user_id=user_id, concept=concept, user_type=user_type).set(eta)
    response_time_seconds.labels(concept=concept, correct=is_correct).observe(response_time)
    
    # Record impact: correctness factor (1.2 for correct, 0.8 for incorrect)
    correctness_factor = 1.2 if is_correct else 0.8
    correctness_impact.labels(concept=concept).set(correctness_factor)

def record_energy_violation(constraint_type: str = "energy"):
    """Record energy constraint violation"""
    energy_violations.labels(constraint_type=constraint_type).inc()

def record_bandit_decision(concept: str, is_exploration: bool):
    """Record bandit decision metrics"""
    bandit_actions.labels(concept=concept).inc()
    
    if is_exploration:
        bandit_exploration.inc()
    else:
        bandit_exploitation.inc()
