"""
Simulated Time Provider

Provides deterministic time advancement for replay mode.

Architecture Principle:
- Separate wall-clock time from causal runtime time
- Time evolution decoupled from RNG sequence
- Prevents accidental coupling: time ↔ RNG
"""
from datetime import datetime, timedelta
from typing import Optional
import numpy as np


class SimulatedTimeProvider:
    """
    Provides deterministic time for replay mode.
    
    In deterministic mode, time advances by fixed increments
    instead of using the real system clock.
    
    Critical Design Decision:
    - Time variation uses dedicated RNG stream (rng_time)
    - Prevents coupling between time evolution and other concerns
    - Adding one extra RNG call elsewhere won't change timestamps
    """
    
    def __init__(self, seed: int = 42, start_time: Optional[datetime] = None, 
                 rng_stream: Optional[np.random.RandomState] = None):
        """
        Initialize simulated time provider.
        
        Args:
            seed: Seed for deterministic time variation
            start_time: Starting time (default: 2026-01-01 00:00:00)
            rng_stream: Dedicated RNG stream for time variation
                        (prevents coupling with other concerns)
        """
        self.seed = seed
        self.current_time = start_time or datetime(2026, 1, 1, 0, 0, 0)
        self.base_increment = timedelta(seconds=1.0)  # 1 second per interaction
        
        # Use dedicated RNG stream for time variation
        # This prevents coupling: time evolution ↔ other RNG sequences
        if rng_stream is not None:
            self.rng = rng_stream
        else:
            self.rng = np.random.RandomState(seed)
    
    def now(self) -> datetime:
        """
        Get current simulated time.
        
        Returns:
            Current simulated time
        """
        return self.current_time
    
    def advance(self, seconds: Optional[float] = None):
        """
        Advance simulated time.
        
        Args:
            seconds: Seconds to advance (default: use base_increment with variation)
        
        Design Note:
            - Uses dedicated rng_time stream for variation
            - Prevents coupling: adding RNG calls elsewhere won't change timestamps
            - Small variation (0.8-1.2x) for realism without breaking determinism
        """
        if seconds is None:
            # Add small random variation for realism
            # CRITICAL: Use dedicated rng_time stream
            variation = self.rng.uniform(0.8, 1.2)
            seconds = self.base_increment.total_seconds() * variation
        
        self.current_time += timedelta(seconds=seconds)
    
    def reset(self):
        """Reset time to start and reseed RNG."""
        self.current_time = datetime(2026, 1, 1, 0, 0, 0)
        self.rng = np.random.RandomState(self.seed)
