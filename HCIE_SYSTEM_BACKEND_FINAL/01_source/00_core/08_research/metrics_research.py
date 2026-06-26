"""
HCIE Research Metrics - Optional for Experiments and Validation

These metrics are useful for research experiments, validation, and analysis but are NOT
required for the core cognitive governance observatory. They can be disabled in production
to reduce metric noise and improve interpretability.

🔥 RESEARCH METRICS (Optional):
- Statistical power analysis
- Effect size calculations
- Ablation studies
- Distribution analysis
- Longitudinal tracking
- Scatter plot analysis
- Convergence analysis

These metrics help validate the architecture but are not essential for operational governance.
"""

from prometheus_client import (
    Counter as _PromCounter,
    Histogram as _PromHistogram,
    Gauge as _PromGauge,
    CollectorRegistry,
)

# Phase 9 split-residue fix: this module is importable through the FINAL
# shim while BACKENDV2 may still be on sys.path. Keep research metrics out
# of the global Prometheus registry to prevent duplicate registration.
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
# 📊 METRICS HEALTH MONITORING
# ==============================

metrics_success = Counter(
    "hcie_metrics_success_total",
    "Successful metric recordings"
)

metrics_failure = Counter(
    "hcie_metrics_failure_total", 
    "Failed metric recordings"
)

# ==============================
# 🔬 STATISTICAL POWER METRICS
# ==============================

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

# ==============================
# 📈 LONGITUDINAL TRACKING METRICS
# ==============================

convergence_rate = Gauge(
    "hcie_convergence_rate",
    "Rate of mastery convergence",
    ["user_id", "concept", "user_type"]
)

retention_score = Gauge(
    "hcie_retention_score",
    "Knowledge retention over time",
    ["user_id", "concept", "user_type"]
)

# ==============================
# 📊 DISTRIBUTION METRICS
# ==============================

mastery_delta_distribution = Histogram(
    "hcie_mastery_delta_distribution",
    "Distribution of mastery delta",
    ["concept", "user_type"],
    buckets=[-1, -0.5, -0.1, 0, 0.1, 0.3, 0.5, 1]
)

# ==============================
# 🔬 JOINT METRIC FOR SCATTER PLOT ANALYSIS
# ==============================

learning_efficiency_scatter = Gauge(
    "hcie_learning_efficiency_point",
    "Joint η(t) and ΔM for scatter plot analysis",
    ["user_id", "concept", "user_type", "eta_bucket", "delta_bucket"]
)

# ==============================
# 🔥 CONVERGENCE TRACKING
# ==============================

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

# ==============================
# 🔥 ABLATION METRICS
# ==============================

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

# ==============================
# 🔥 VARIANCE METRICS
# ==============================

mastery_delta_sq_sum = Counter(
    "hcie_mastery_delta_sq_sum_total",
    "Sum of squared mastery deltas for variance calculation",
    ["concept", "user_type", "mode"]
)
