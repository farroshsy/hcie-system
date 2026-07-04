"""
Deterministic Mode Configuration

Provides opt-in deterministic runtime configuration.

Architecture Principle:
- Determinism is opt-in (deterministic=False by default)
- Production traceability preserved when deterministic=False
- Entropy assumptions preserved when deterministic=False
- UUID semantics preserved when deterministic=False
- Audit semantics preserved when deterministic=False

🔥 GLOBAL DETERMINISTIC CONTEXT:
For automatic deterministic event metadata propagation across the system.
"""
from dataclasses import dataclass
from typing import Optional
import threading


# 🔥 GLOBAL DETERMINISTIC CONTEXT (thread-safe)
_global_deterministic_config: Optional['DeterministicModeConfig'] = None
_config_lock = threading.Lock()


@dataclass
class DeterministicModeConfig:
    """
    Configuration for deterministic runtime mode.
    
    Design Principle: Opt-in only (deterministic=False by default).
    
    If deterministic=False:
    - Production traceability preserved
    - Entropy assumptions preserved
    - UUID semantics preserved
    - Audit semantics preserved
    
    If deterministic=True:
    - Replay-safe UUID generation
    - Simulated time advancement
    - Isolated RNG streams
    - Scientific reproducibility
    """
    
    # Core determinism flag
    deterministic: bool = False
    
    # Seed for deterministic operations
    seed: int = 42
    
    # Layered determinism levels
    event_determinism: bool = True  # Same events → same state
    trajectory_determinism: bool = True  # Same seed → same actions
    full_determinism: bool = False  # Bitwise identical replay
    
    # Component flags
    deterministic_uuids: bool = True
    deterministic_time: bool = True
    deterministic_noise: bool = False  # Noise is intentional exploration
    
    @classmethod
    def experiment(cls, seed: int = 42) -> 'DeterministicModeConfig':
        """Config for experiment mode (full determinism)"""
        return cls(
            deterministic=True,
            seed=seed,
            deterministic_uuids=True,
            deterministic_time=True,
            trajectory_determinism=True  #  PRIORITY 2: Full trajectory determinism
        )
    
    @classmethod
    def replay_validation(cls, seed: int = 42) -> 'DeterministicModeConfig':
        """Config for replay validation (full determinism)"""
        return cls(
            deterministic=True,
            seed=seed,
            deterministic_uuids=True,
            deterministic_time=True,
            trajectory_determinism=True
        )
    
    @classmethod
    def production(cls) -> 'DeterministicModeConfig':
        """Config for production mode (no determinism)"""
        return cls(
            deterministic=False,
            seed=42,
            deterministic_uuids=False,
            deterministic_time=False,
            trajectory_determinism=False
        )


def set_global_deterministic_config(config: Optional[DeterministicModeConfig]):
    """Set global deterministic config (thread-safe)"""
    global _global_deterministic_config
    with _config_lock:
        _global_deterministic_config = config


def get_global_deterministic_config() -> Optional[DeterministicModeConfig]:
    """Get global deterministic config (thread-safe)"""
    with _config_lock:
        return _global_deterministic_config


def is_deterministic_mode() -> bool:
    """Check if system is in deterministic mode"""
    config = get_global_deterministic_config()
    return config.deterministic if config else False


def get_deterministic_seed() -> Optional[int]:
    """Get deterministic seed if in deterministic mode"""
    config = get_global_deterministic_config()
    return config.seed if config else None
