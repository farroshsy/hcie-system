"""
RNG Stream Manager

Provides isolated RNG streams for different concerns to prevent
accidental coupling between time evolution, noise, bandit selection,
exploration, and UUID generation.

Architecture Principle:
- Never share RNG streams between concerns
- Each concern has dedicated seeded RNG
- Prevents cascade failures when one stream is modified
"""
import numpy as np
import random


class RNGStreamManager:
    """
    Manages isolated RNG streams for different concerns.
    
    Prevents accidental coupling between:
    - rng_time: Time advancement
    - rng_noise: Exploration noise in cognition
    - rng_bandit: Bandit arm selection
    - rng_exploration: Exploration pressure
    - rng_uuid: UUID generation (if using RNG-based fallback)
    
    Critical: Never share streams between concerns.
    """
    
    def __init__(self, seed: int = 42):
        """
        Initialize RNG stream manager with isolated streams.
        
        Args:
            seed: Base seed for all streams
        """
        self.base_seed = seed
        
        # Create isolated RNG streams with different seeds
        # Use deterministic seed derivation: seed + concern_offset
        self.rng_time = np.random.RandomState(seed + 1)
        self.rng_noise = np.random.RandomState(seed + 2)
        self.rng_bandit = np.random.RandomState(seed + 3)
        self.rng_exploration = np.random.RandomState(seed + 4)
        self.rng_uuid = np.random.RandomState(seed + 5)
        
        # Python random module streams (for legacy code)
        self.random_time = random.Random(seed + 11)
        self.random_noise = random.Random(seed + 12)
        self.random_bandit = random.Random(seed + 13)
        self.random_exploration = random.Random(seed + 14)
        self.random_uuid = random.Random(seed + 15)
    
    def get_time_stream(self) -> np.random.RandomState:
        """Get RNG stream for time advancement."""
        return self.rng_time
    
    def get_noise_stream(self) -> np.random.RandomState:
        """Get RNG stream for exploration noise."""
        return self.rng_noise
    
    def get_bandit_stream(self) -> np.random.RandomState:
        """Get RNG stream for bandit selection."""
        return self.rng_bandit
    
    def get_exploration_stream(self) -> np.random.RandomState:
        """Get RNG stream for exploration pressure."""
        return self.rng_exploration
    
    def get_uuid_stream(self) -> np.random.RandomState:
        """Get RNG stream for UUID generation (fallback)."""
        return self.rng_uuid
    
    def reset_all(self):
        """Reset all RNG streams to initial state."""
        self.rng_time = np.random.RandomState(self.base_seed + 1)
        self.rng_noise = np.random.RandomState(self.base_seed + 2)
        self.rng_bandit = np.random.RandomState(self.base_seed + 3)
        self.rng_exploration = np.random.RandomState(self.base_seed + 4)
        self.rng_uuid = np.random.RandomState(self.base_seed + 5)
        
        self.random_time = random.Random(self.base_seed + 11)
        self.random_noise = random.Random(self.base_seed + 12)
        self.random_bandit = random.Random(self.base_seed + 13)
        self.random_exploration = random.Random(self.base_seed + 14)
        self.random_uuid = random.Random(self.base_seed + 15)
