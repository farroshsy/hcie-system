"""
🔥 Lightweight Performance Instrumentation

Provides lightweight timing decorators and context managers for critical path monitoring.
Designed for low overhead and minimal token usage.

Usage:
    from infrastructure.experiment.timing import timed_operation, TimedOperation
    
    @timed_operation("transfer_lookup")
    def get_dependencies(self, concept):
        pass
    
    with TimedOperation("jt_computation"):
        jt = calculate_jt(...)
"""

import time
import logging
from functools import wraps
from contextlib import contextmanager
from typing import Callable, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# ============================================================================
# TIMING METRICS STORAGE
# ============================================================================

_timing_metrics = defaultdict(list)


class TimingMetrics:
    """Thread-safe timing metrics storage"""
    
    @classmethod
    def record(cls, operation: str, duration: float):
        """Record a timing metric"""
        _timing_metrics[operation].append(duration)
    
    @classmethod
    def get_stats(cls, operation: str) -> dict:
        """Get statistics for an operation"""
        durations = _timing_metrics.get(operation, [])
        if not durations:
            return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0, "total": 0.0}
        
        return {
            "count": len(durations),
            "mean": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations),
            "total": sum(durations),
        }
    
    @classmethod
    def get_all_stats(cls) -> dict:
        """Get statistics for all operations"""
        return {op: cls.get_stats(op) for op in _timing_metrics.keys()}
    
    @classmethod
    def clear(cls):
        """Clear all timing metrics"""
        _timing_metrics.clear()


# ============================================================================
# DECORATORS
# ============================================================================

def timed_operation(operation_name: str):
    """
    Decorator to time a function operation
    
    Args:
        operation_name: Name of the operation for metrics tracking
    
    Usage:
        @timed_operation("transfer_lookup")
        def get_dependencies(self, concept):
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start
                TimingMetrics.record(operation_name, duration)
                logger.debug(f"⏱️ {operation_name}: {duration:.4f}s")
        return wrapper
    return decorator


def timed_operation_if(condition: bool, operation_name: str):
    """
    Conditional decorator - only time if condition is true
    
    Args:
        condition: Boolean condition
        operation_name: Name of the operation for metrics tracking
    
    Usage:
        @timed_operation_if(RuntimeConfig.PROFILE, "jt_computation")
        def calculate_jt(self):
            pass
    """
    def decorator(func: Callable):
        if condition:
            return timed_operation(operation_name)(func)
        return func
    return decorator


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

@contextmanager
def TimedOperation(operation_name: str, log_threshold: Optional[float] = None):
    """
    Context manager to time a block of code
    
    Args:
        operation_name: Name of the operation for metrics tracking
        log_threshold: Optional threshold in seconds for warning logging
    
    Usage:
        with TimedOperation("jt_computation"):
            jt = calculate_jt(...)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        TimingMetrics.record(operation_name, duration)
        
        if log_threshold and duration > log_threshold:
            logger.warning(f"⏱️ SLOW {operation_name}: {duration:.4f}s (threshold: {log_threshold}s)")
        else:
            logger.debug(f"⏱️ {operation_name}: {duration:.4f}s")


# ============================================================================
# CRITICAL PATH TIMING
# ============================================================================

# Pre-defined operation names for critical paths
OPERATION_TRANSFER_LOOKUP = "transfer_lookup"
OPERATION_DB_COMMIT = "db_commit"
OPERATION_JT_COMPUTATION = "jt_computation"
OPERATION_REPLAY_HASH = "replay_hash"
OPERATION_DEPENDENCY_LOADING = "dependency_loading"
OPERATION_BANDIT_UPDATE = "bandit_update"
OPERATION_ENSEMBLE_UPDATE = "ensemble_update"


# ============================================================================
# SUMMARY REPORTING
# ============================================================================

def print_timing_summary():
    """Print a summary of all timing metrics"""
    stats = TimingMetrics.get_all_stats()
    
    if not stats:
        logger.info("📊 No timing metrics collected")
        return
    
    logger.info("📊 TIMING SUMMARY:")
    logger.info("=" * 60)
    
    # Sort by total time (descending)
    sorted_ops = sorted(stats.items(), key=lambda x: x[1]["total"], reverse=True)
    
    for op, metrics in sorted_ops:
        logger.info(
            f"  {op:30s} | "
            f"count={metrics['count']:4d} | "
            f"mean={metrics['mean']:6.4f}s | "
            f"min={metrics['min']:6.4f}s | "
            f"max={metrics['max']:6.4f}s | "
            f"total={metrics['total']:8.4f}s"
        )
    
    logger.info("=" * 60)


def get_slow_operations(threshold: float = 0.1) -> list:
    """
    Get operations with mean duration above threshold
    
    Args:
        threshold: Threshold in seconds
    
    Returns:
        List of (operation, mean_duration) tuples
    """
    stats = TimingMetrics.get_all_stats()
    slow_ops = [(op, metrics["mean"]) for op, metrics in stats.items() if metrics["mean"] > threshold]
    return sorted(slow_ops, key=lambda x: x[1], reverse=True)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example usage
    @timed_operation("example_operation")
    def example_function():
        time.sleep(0.1)
        return "done"
    
    result = example_function()
    
    with TimedOperation("example_block"):
        time.sleep(0.05)
    
    print_timing_summary()
    
    slow_ops = get_slow_operations(threshold=0.01)
    if slow_ops:
        print("\nSlow operations (>0.01s):")
        for op, duration in slow_ops:
            print(f"  {op}: {duration:.4f}s")
