"""
🔥 CONTROLLED PROFILING: Performance monitoring for research validation

Usage:
    from infrastructure.experiment.profiler import profile_evaluation
    
    with profile_evaluation(output_file="/tmp/profile_stats"):
        run_evaluation()
"""

import cProfile
import pstats
import io
import logging
from contextlib import contextmanager
from typing import Optional
import time

logger = logging.getLogger(__name__)


@contextmanager
def profile_evaluation(output_file: Optional[str] = None, n_top: int = 30):
    """
    Profile evaluation runtime with cProfile
    
    Args:
        output_file: Save stats to file (optional)
        n_top: Number of top functions to log
    """
    profiler = cProfile.Profile()
    start_time = time.time()
    
    logger.info("🔥 PROFILING: Starting performance capture")
    profiler.enable()
    
    try:
        yield profiler
    finally:
        profiler.disable()
        elapsed = time.time() - start_time
        
        # Capture stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.strip_dirs()
        ps.sort_stats('cumulative')  # Sort by cumulative time
        ps.print_stats(n_top)
        
        # Log summary
        logger.info(f"🔥 PROFILING COMPLETE: {elapsed:.2f}s")
        logger.info(f"🔥 TOP {n_top} FUNCTIONS BY CUMULATIVE TIME:")
        
        # Write detailed stats
        if output_file:
            ps.dump_stats(output_file)
            logger.info(f"🔥 Profile saved to: {output_file}")
        
        # Print summary to log
        summary_lines = s.getvalue().split('\n')[:n_top+5]
        for line in summary_lines:
            if line.strip():
                logger.info(f"  {line}")


def profile_function(func):
    """
    Decorator to profile a specific function
    
    Usage:
        @profile_function
        def expensive_operation():
            pass
    """
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        
        start = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.time() - start
            profiler.disable()
            
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s)
            ps.strip_dirs().sort_stats('cumulative').print_stats(10)
            
            logger.info(f"🔥 FUNCTION PROFILE: {func.__name__} took {elapsed:.3f}s")
            logger.info(f"🔥 Top 10 callees:\n{s.getvalue()}")
    
    return wrapper


class SimpleTimer:
    """
    Simple context manager for timing code blocks
    
    Usage:
        with SimpleTimer("database_write"):
            db.write(data)
    """
    
    def __init__(self, name: str):
        self.name = name
        self.start = None
        self.elapsed = None
    
    def __enter__(self):
        self.start = time.time()
        return self
    
    def __exit__(self, *args):
        self.elapsed = time.time() - self.start
        logger.info(f"🔥 TIMER [{self.name}]: {self.elapsed:.4f}s")
