"""
Ownership Enforcement - Phase E1

Transforms documentation law into runtime-enforced architectural law.

Canonical Write Boundary:
Only UnifiedBrain and ReplayEngine may mutate canonical cognition fields.
Everything else becomes read-only derived topology.

This prevents:
- accidental direct writes
- projection-layer mutations
- service-layer cognition drift
- replay corruption via side writes
- "temporary hacks" during future development
"""

import logging
from typing import Set, Optional, Callable, Any
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)


class CognitionWriter(Enum):
    """Approved cognition writers"""
    UNIFIED_BRAIN = "unified_brain"
    REPLAY_ENGINE = "replay_engine"
    EXPERIMENT = "experiment"  # For research experiments with real infrastructure
    # Future approved writers can be added here


class OwnershipViolationError(Exception):
    """Raised when unauthorized code attempts to write canonical cognition state"""
    pass


class OwnershipEnforcement:
    """
    Runtime ownership enforcement for canonical cognition state.
    
    Enforces the architectural law:
    Only UnifiedBrain and ReplayEngine may mutate canonical cognition fields.
    """
    
    # Approved cognition writers registry
    APPROVED_WRITERS: Set[CognitionWriter] = {
        CognitionWriter.UNIFIED_BRAIN,
        CognitionWriter.REPLAY_ENGINE,
        CognitionWriter.EXPERIMENT
    }
    
    # Canonical cognitive fields that require ownership enforcement
    CANONICAL_FIELDS = {
        'mastery', 'uncertainty', 'zpd_score',
        'bayesian_alpha', 'bayesian_beta',
        'kalman_mastery', 'kalman_covariance',
        'lyapunov_mastery'
    }
    
    # Runtime adaptive control fields (Tier 2 - not enforced)
    CONTROL_FIELDS = {
        'J_value', 'adaptive_rate'
    }
    
    def __init__(self, enabled: bool = True):
        """
        Initialize ownership enforcement.
        
        Args:
            enabled: Whether enforcement is active (can be disabled for debugging)
        """
        self.enabled = enabled
        self._current_writer: Optional[CognitionWriter] = None
    
    def set_writer(self, writer: CognitionWriter):
        """
        Set the current cognition writer context.
        
        This should be called at the entry point of approved writers
        to establish ownership context for the duration of processing.
        
        Args:
            writer: The approved cognition writer
        """
        if self.enabled and writer not in self.APPROVED_WRITERS:
            raise OwnershipViolationError(
                f"Unauthorized cognition writer: {writer}. "
                f"Approved writers: {self.APPROVED_WRITERS}"
            )
        self._current_writer = writer
        logger.debug(f"🔒 Ownership context set: {writer}")
    
    def clear_writer(self):
        """Clear the current cognition writer context."""
        self._current_writer = None
    
    def assert_canonical_write_permission(self, caller_module: str, operation: str = "write"):
        """
        Assert that the current context has permission to write canonical cognition state.
        
        Args:
            caller_module: Module name attempting the write (for logging)
            operation: Operation being performed (e.g., "write", "update", "delete")
        
        Raises:
            OwnershipViolationError: If unauthorized write attempted
        """
        if not self.enabled:
            logger.debug(f"⚠️  Ownership enforcement disabled - allowing {operation} from {caller_module}")
            return
        
        if self._current_writer is None:
            raise OwnershipViolationError(
                f"Unauthorized canonical cognition {operation} attempted by {caller_module}. "
                f"No ownership context established. "
                f"Approved writers: {self.APPROVED_WRITERS}. "
                f"Call set_writer() with approved writer before mutating canonical cognition state."
            )
        
        logger.debug(f"✅ Canonical {operation} permitted: {caller_module} → {self._current_writer}")
    
    def validate_state_mutation(self, state_data: dict, caller_module: str):
        """
        Validate that state mutation only affects allowed fields for the current writer.
        
        Args:
            state_data: State data being written
            caller_module: Module name attempting the write
        
        Raises:
            OwnershipViolationError: If unauthorized field mutation attempted
        """
        if not self.enabled:
            return
        
        # Check if canonical fields are being mutated
        canonical_mutations = self.CANONICAL_FIELDS.intersection(state_data.keys())
        
        if canonical_mutations:
            self.assert_canonical_write_permission(caller_module, f"mutation of {canonical_mutations}")
    
    def check_read_only_access(self, caller_module: str):
        """
        Log read-only access to canonical cognition state.
        
        Args:
            caller_module: Module name accessing the state
        """
        logger.debug(f"📖 Read-only access: {caller_module} → canonical cognition state")


# Global ownership enforcement instance
_ownership_enforcement = OwnershipEnforcement(enabled=True)


def get_ownership_enforcement() -> OwnershipEnforcement:
    """Get the global ownership enforcement instance."""
    return _ownership_enforcement


def with_ownership(writer: CognitionWriter):
    """
    Decorator to establish ownership context for a function.
    
    Usage:
        @with_ownership(CognitionWriter.UNIFIED_BRAIN)
        def update_cognition(user_id, concept, state):
            # Function can now safely write canonical cognition state
            pass
    
    Args:
        writer: The approved cognition writer
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            enforcement = get_ownership_enforcement()
            try:
                enforcement.set_writer(writer)
                return func(*args, **kwargs)
            finally:
                enforcement.clear_writer()
        return wrapper
    return decorator


def assert_canonical_write(caller_module: str):
    """
    Assert permission to write canonical cognition state.
    
    Convenience function for quick ownership checks.
    
    Args:
        caller_module: Module name attempting the write
    """
    enforcement = get_ownership_enforcement()
    enforcement.assert_canonical_write_permission(caller_module)


def validate_state_write(state_data: dict, caller_module: str):
    """
    Validate state write operation.
    
    Convenience function for validating state mutations.
    
    Args:
        state_data: State data being written
        caller_module: Module name attempting the write
    """
    enforcement = get_ownership_enforcement()
    enforcement.validate_state_mutation(state_data, caller_module)
