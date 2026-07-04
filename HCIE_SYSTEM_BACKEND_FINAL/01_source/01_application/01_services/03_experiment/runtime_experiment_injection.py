"""
Runtime Experiment Injection

Injects experiment assignment into adaptation runtime for multi-policy pedagogical execution.
This is the critical transition from single canonical policy to competing pedagogical policies.

Architecture:
- ProjectionUpdated → adaptation engine → experiment registry lookup → assigned policy version → execute policy variant
- Experiment lineage attached to all canonical events (TaskAttemptSubmitted, CognitionUpdated, AdaptationGenerated, ProjectionUpdated)
- Policy execution identity persisted for replay reconstruction
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib

from app.services.experiment.experiment_registry import (
    ExperimentRegistry,
    get_experiment_registry
)

logger = logging.getLogger(__name__)


class ExperimentContext:
    """
    Experiment context for a single learner interaction.
    
    Contains all experiment lineage metadata needed for:
    - Replay reconstruction
    - Offline evaluation
    - Cohort comparison
    - Semantic trajectory analysis
    """
    
    def __init__(
        self,
        user_id: str,
        experiment_id: Optional[str] = None,
        policy_version: Optional[str] = None,
        cohort_id: Optional[str] = None,
        assignment_hash: Optional[str] = None,
        experiment_seed: Optional[str] = None
    ):
        self.user_id = user_id
        self.experiment_id = experiment_id
        self.policy_version = policy_version
        self.cohort_id = cohort_id
        self.assignment_hash = assignment_hash
        self.experiment_seed = experiment_seed
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event metadata"""
        return {
            "experiment_id": self.experiment_id,
            "policy_version": self.policy_version,
            "cohort_id": self.cohort_id,
            "assignment_hash": self.assignment_hash,
            "experiment_seed": self.experiment_seed,
            "timestamp": self.timestamp.isoformat()
        }
    
    def is_active(self) -> bool:
        """Check if this context represents an active experiment assignment"""
        return self.experiment_id is not None and self.policy_version is not None


class RuntimeExperimentInjector:
    """
    Injects experiment assignment into adaptation runtime.
    
    This service bridges the gap between:
    - Experiment registry (metadata + assignment)
    - Adaptation engine (pedagogical policy execution)
    
    Critical for multi-policy pedagogical runtime.
    """
    
    def __init__(self, experiment_registry: Optional[ExperimentRegistry] = None):
        self._experiment_registry = experiment_registry or get_experiment_registry()
        self._context_cache: Dict[str, ExperimentContext] = {}  # user_id -> ExperimentContext
    
    def get_experiment_context(
        self,
        user_id: str,
        experiment_seed: Optional[str] = None
    ) -> ExperimentContext:
        """
        Get experiment context for a learner.
        
        This is the critical injection point where experiment assignment
        is retrieved and attached to the adaptation runtime.
        
        Args:
            user_id: Learner identifier
            experiment_seed: Optional seed for deterministic assignment
        
        Returns:
            ExperimentContext with experiment lineage metadata
        """
        # Check cache first
        cache_key = f"{user_id}:{experiment_seed or 'default'}"
        if cache_key in self._context_cache:
            return self._context_cache[cache_key]
        
        # Get experiment assignment from registry
        experiment_id = self._experiment_registry.assign_user_to_experiment(user_id, experiment_seed)
        
        if not experiment_id:
            # No active experiment assignment
            context = ExperimentContext(user_id=user_id)
        else:
            # Get policy assignment for this experiment
            policy_version = self._experiment_registry.assign_policy_for_user(user_id, experiment_id)
            
            # Build assignment hash for replay determinism
            assignment_key = f"{user_id}:{experiment_seed or 'default'}"
            assignment_hash = hashlib.sha256(assignment_key.encode('utf-8')).hexdigest()[:16]
            
            # Build cohort_id from experiment_id + policy_version
            cohort_id = f"{experiment_id}:{policy_version}"
            
            context = ExperimentContext(
                user_id=user_id,
                experiment_id=experiment_id,
                policy_version=policy_version,
                cohort_id=cohort_id,
                assignment_hash=assignment_hash,
                experiment_seed=experiment_seed
            )
        
        # Cache context
        self._context_cache[cache_key] = context
        
        return context
    
    def inject_into_adaptation(
        self,
        user_id: str,
        adaptation_inputs: Dict[str, Any],
        experiment_seed: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inject experiment context into adaptation execution.
        
        This is the critical method that enables multi-policy runtime.
        It adds policy_version to adaptation inputs so the adaptation engine
        can execute the correct policy variant.
        
        Args:
            user_id: Learner identifier
            adaptation_inputs: Original adaptation inputs (cognition state, etc.)
            experiment_seed: Optional seed for deterministic assignment
        
        Returns:
            Adaptation inputs with experiment context injected
        """
        context = self.get_experiment_context(user_id, experiment_seed)
        
        # Inject experiment lineage into adaptation inputs
        enriched_inputs = {
            **adaptation_inputs,
            "experiment_context": context.to_dict()
        }
        
        # If active experiment, inject policy_version for policy routing
        if context.is_active():
            enriched_inputs["policy_version"] = context.policy_version
            logger.debug(
                f"Injected experiment context for user {user_id}: "
                f"experiment={context.experiment_id}, policy={context.policy_version}"
            )
        
        return enriched_inputs
    
    def attach_to_event(
        self,
        user_id: str,
        event_payload: Dict[str, Any],
        experiment_seed: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Attach experiment lineage to canonical event payload.
        
        This ensures all canonical events (TaskAttemptSubmitted, CognitionUpdated,
        AdaptationGenerated, ProjectionUpdated) carry experiment lineage for:
        - Replay reconstruction
        - Offline evaluation
        - Cohort comparison
        - Semantic trajectory analysis
        
        Args:
            user_id: Learner identifier
            event_payload: Original event payload
            experiment_seed: Optional seed for deterministic assignment
        
        Returns:
            Event payload with experiment lineage attached
        """
        context = self.get_experiment_context(user_id, experiment_seed)
        
        # Attach experiment lineage to event metadata
        enriched_payload = {
            **event_payload,
            "experiment_lineage": context.to_dict()
        }
        
        return enriched_payload
    
    def clear_context(self, user_id: str, experiment_seed: Optional[str] = None) -> None:
        """
        Clear cached experiment context for a user.
        
        Useful for testing or when experiment assignment changes.
        """
        cache_key = f"{user_id}:{experiment_seed or 'default'}"
        if cache_key in self._context_cache:
            del self._context_cache[cache_key]
            logger.debug(f"Cleared experiment context for user {user_id} (seed: {experiment_seed or 'default'})")
    
    def get_policy_version_for_user(
        self,
        user_id: str,
        experiment_seed: Optional[str] = None
    ) -> Optional[str]:
        """
        Get assigned policy version for a user.
        
        This is the critical routing method for multi-policy runtime.
        
        Args:
            user_id: Learner identifier
            experiment_seed: Optional seed for deterministic assignment
        
        Returns:
            Policy version if assigned to active experiment, None otherwise
        """
        context = self.get_experiment_context(user_id, experiment_seed)
        return context.policy_version if context.is_active() else None


# Global injector instance
_runtime_experiment_injector = None


def get_runtime_experiment_injector() -> RuntimeExperimentInjector:
    """Get global runtime experiment injector instance"""
    global _runtime_experiment_injector
    if _runtime_experiment_injector is None:
        _runtime_experiment_injector = RuntimeExperimentInjector()
    return _runtime_experiment_injector
