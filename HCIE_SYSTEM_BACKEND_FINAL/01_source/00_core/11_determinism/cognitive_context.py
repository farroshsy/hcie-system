"""
Cognitive Context for Version-Controlled Cognition

This module implements explicit cognitive boundary semantics to enable:
- Branching adaptive timelines
- Deterministic replay
- Simulation isolation
- Interrupted trajectory equivalence

Core concept: Cognition is represented explicitly as a forkable organism
instead of implicitly inside services. This enables version-controlled cognition.
"""

import copy
import dataclasses
import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class CognitiveSnapshot:
    """
    Complete cognitive state snapshot for version-controlled cognition.
    
    Contains all replay-critical state required for:
    - Deterministic replay
    - Simulation forking
    - Trajectory restoration
    - Identity preservation validation
    """
    
    # Governance state (replay-critical)
    governance_weights: Dict[str, float] = field(default_factory=dict)
    normalization_state: Dict[str, Any] = field(default_factory=dict)
    component_history: Dict[str, Any] = field(default_factory=dict)
    
    # Bandit state (replay-critical)
    bandit_alpha_beta: Dict[str, tuple] = field(default_factory=dict)
    arm_rewards: Dict[str, List[float]] = field(default_factory=dict)
    arm_contexts: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    
    # Volatility state (replay-critical)
    volatility_history: List = field(default_factory=list)
    volatility_components: Dict[str, Any] = field(default_factory=dict)
    
    # Learner state (replay-critical)
    learner_priors: Dict[str, Any] = field(default_factory=dict)
    learner_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Transfer state (replay-critical)
    transfer_priors: Dict[str, Any] = field(default_factory=dict)
    transfer_history: List = field(default_factory=list)
    
    # Entropy state (replay-critical)
    entropy_seed: int = 42
    entropy_state: Optional[Dict[str, Any]] = None
    
    # Replay trajectory (replay-critical)
    jt_trajectory: List[float] = field(default_factory=list)
    replay_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    snapshot_id: str = ""
    timestamp: float = 0.0
    context_type: str = "production"  # production, simulation, evaluation, replay
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary for persistence."""
        return {
            'governance_weights': self.governance_weights,
            'normalization_state': self.normalization_state,
            'component_history': self.component_history,
            'bandit_alpha_beta': self.bandit_alpha_beta,
            'arm_rewards': self.arm_rewards,
            'arm_contexts': self.arm_contexts,
            'volatility_history': self.volatility_history,
            'volatility_components': self.volatility_components,
            'learner_priors': self.learner_priors,
            'learner_parameters': self.learner_parameters,
            'transfer_priors': self.transfer_priors,
            'transfer_history': self.transfer_history,
            'entropy_seed': self.entropy_seed,
            'entropy_state': self.entropy_state,
            'jt_trajectory': self.jt_trajectory,
            'replay_events': self.replay_events,
            'snapshot_id': self.snapshot_id,
            'timestamp': self.timestamp,
            'context_type': self.context_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CognitiveSnapshot':
        """Create snapshot from dictionary."""
        return cls(
            governance_weights=data.get('governance_weights', {}),
            normalization_state=data.get('normalization_state', {}),
            component_history=data.get('component_history', {}),
            bandit_alpha_beta=data.get('bandit_alpha_beta', {}),
            arm_rewards=data.get('arm_rewards', {}),
            arm_contexts=data.get('arm_contexts', {}),
            volatility_history=data.get('volatility_history', []),
            volatility_components=data.get('volatility_components', {}),
            learner_priors=data.get('learner_priors', {}),
            learner_parameters=data.get('learner_parameters', {}),
            transfer_priors=data.get('transfer_priors', {}),
            transfer_history=data.get('transfer_history', []),
            entropy_seed=data.get('entropy_seed', 42),
            entropy_state=data.get('entropy_state'),
            jt_trajectory=data.get('jt_trajectory', []),
            replay_events=data.get('replay_events', []),
            snapshot_id=data.get('snapshot_id', ''),
            timestamp=data.get('timestamp', 0.0),
            context_type=data.get('context_type', 'production')
        )


class CognitiveContext:
    """
    Explicit cognitive context for version-controlled cognition.
    
    Represents cognition as a forkable organism with explicit:
    - governance_state
    - learner_state
    - entropy_stream
    - persistence_scope
    - replay_mode
    - mutation_policy
    - lifecycle_contract
    """
    
    def __init__(self, seed: int = 42, context_type: str = "production"):
        """
        Initialize cognitive context.
        
        Args:
            seed: Entropy seed for compartment-local RNG
            context_type: Type of cognitive context (production, simulation, evaluation, replay)
        """
        # Compartment-local RNG (NOT global mutation)
        self.rng = np.random.default_rng(seed)
        self.entropy_seed = seed
        
        # Cognitive context type
        self.context_type = context_type
        
        # Governance state
        self.governance_state: Dict[str, Any] = {}
        
        # Learner state
        self.learner_state: Dict[str, Any] = {}
        
        # Bandit state
        self.bandit_state: Dict[str, Any] = {}
        
        # Volatility state
        self.volatility_state: Dict[str, Any] = {}
        
        # Transfer state
        self.transfer_state: Dict[str, Any] = {}
        
        # Replay trajectory
        self.jt_trajectory: List[float] = []
        self.replay_events: List[Dict[str, Any]] = []
        
        # Persistence scope
        self.persistence_enabled = (context_type == "production")
        self.redis_namespace = f"cognition_{context_type}"
        
        # Replay mode
        self.replay_mode = (context_type == "replay")
        
        # Mutation policy
        self.mutation_allowed = (context_type != "replay")
        
        # Lifecycle contract
        self.lifecycle_contract = {
            'reset_preserves_priors': True,
            'reset_destroys_artifacts': True,
            'reset_reseeds_entropy': True,
            'persistence_enabled': self.persistence_enabled,
            'mutation_allowed': self.mutation_allowed,
            'replay_mode': self.replay_mode
        }
    
    def snapshot(self) -> CognitiveSnapshot:
        """
        Capture complete cognitive state snapshot.
        
        Returns:
            CognitiveSnapshot containing all replay-critical state
        """
        import time
        import uuid
        
        snapshot = CognitiveSnapshot(
            governance_weights=self.governance_state.get('weights', {}),
            normalization_state=self.governance_state.get('normalization', {}),
            component_history=self.governance_state.get('history', {}),
            bandit_alpha_beta=self.bandit_state.get('alpha_beta', {}),
            arm_rewards=self.bandit_state.get('rewards', {}),
            arm_contexts=self.bandit_state.get('contexts', {}),
            volatility_history=self.volatility_state.get('history', []),
            volatility_components=self.volatility_state.get('components', {}),
            learner_priors=self.learner_state.get('priors', {}),
            learner_parameters=self.learner_state.get('parameters', {}),
            transfer_priors=self.transfer_state.get('priors', {}),
            transfer_history=self.transfer_state.get('history', []),
            entropy_seed=self.entropy_seed,
            entropy_state=None,  # TODO: Capture RNG state if needed
            jt_trajectory=self.jt_trajectory.copy(),
            replay_events=self.replay_events.copy(),
            snapshot_id=str(uuid.uuid4()),
            timestamp=time.time(),
            context_type=self.context_type
        )
        
        return snapshot
    
    def restore(self, snapshot: CognitiveSnapshot) -> None:
        """
        Restore cognitive state from snapshot.
        
        Args:
            snapshot: CognitiveSnapshot to restore from
        """
        # Restore governance state
        self.governance_state = {
            'weights': snapshot.governance_weights.copy(),
            'normalization': snapshot.normalization_state.copy(),
            'history': snapshot.component_history.copy()
        }
        
        # Restore bandit state
        self.bandit_state = {
            'alpha_beta': snapshot.bandit_alpha_beta.copy(),
            'rewards': {k: v.copy() for k, v in snapshot.arm_rewards.items()},
            'contexts': {k: v.copy() for k, v in snapshot.arm_contexts.items()}
        }
        
        # Restore volatility state
        self.volatility_state = {
            'history': snapshot.volatility_history.copy(),
            'components': snapshot.volatility_components.copy()
        }
        
        # Restore learner state
        self.learner_state = {
            'priors': snapshot.learner_priors.copy(),
            'parameters': snapshot.learner_parameters.copy()
        }
        
        # Restore transfer state
        self.transfer_state = {
            'priors': snapshot.transfer_priors.copy(),
            'history': snapshot.transfer_history.copy()
        }
        
        # Restore entropy
        self.entropy_seed = snapshot.entropy_seed
        self.rng = np.random.default_rng(snapshot.entropy_seed)
        
        # Restore trajectory
        self.jt_trajectory = snapshot.jt_trajectory.copy()
        self.replay_events = snapshot.replay_events.copy()
        
        # Restore context type
        self.context_type = snapshot.context_type
        self.persistence_enabled = (snapshot.context_type == "production")
        self.redis_namespace = f"cognition_{snapshot.context_type}"
        self.replay_mode = (snapshot.context_type == "replay")
        self.mutation_allowed = (snapshot.context_type != "replay")
    
    def fork(self, new_seed: Optional[int] = None) -> 'CognitiveContext':
        """
        Create isolated cognitive fork with independent entropy.
        
        Args:
            new_seed: New entropy seed for fork (if None, derive from current)
        
        Returns:
            New CognitiveContext with forked state
        """
        if new_seed is None:
            # Derive new seed from current seed
            new_seed = self.entropy_seed + 1
        
        # Create new context
        forked_context = CognitiveContext(
            seed=new_seed,
            context_type="simulation"  # Forks are simulation contexts
        )
        
        # Deep copy all state
        forked_context.governance_state = copy.deepcopy(self.governance_state)
        forked_context.learner_state = copy.deepcopy(self.learner_state)
        forked_context.bandit_state = copy.deepcopy(self.bandit_state)
        forked_context.volatility_state = copy.deepcopy(self.volatility_state)
        forked_context.transfer_state = copy.deepcopy(self.transfer_state)
        
        # Fork trajectory (start from current state, not empty)
        forked_context.jt_trajectory = self.jt_trajectory.copy()
        forked_context.replay_events = self.replay_events.copy()
        
        return forked_context
    
    def diff(self, other: 'CognitiveContext') -> Dict[str, Any]:
        """
        Compute difference between two cognitive contexts.
        
        Args:
            other: Another CognitiveContext to compare with
        
        Returns:
            Dictionary of differences
        """
        # KL divergence of governance weights
        kl_div = self._compute_kl_divergence(
            self.governance_state.get('weights', {}),
            other.governance_state.get('weights', {})
        )
        
        # Reservoir drift
        reservoir_drift = self._compute_reservoir_drift(
            self.governance_state.get('normalization', {}),
            other.governance_state.get('normalization', {})
        )
        
        # JT trajectory divergence
        jt_divergence = self._compute_trajectory_divergence(
            self.jt_trajectory,
            other.jt_trajectory
        )
        
        return {
            'governance_weight_kl_divergence': kl_div,
            'reservoir_drift': reservoir_drift,
            'jt_trajectory_divergence': jt_divergence,
            'entropy_seed_diff': abs(self.entropy_seed - other.entropy_seed),
            'context_type_diff': self.context_type != other.context_type
        }
    
    def _compute_kl_divergence(self, dist1: Dict[str, float], dist2: Dict[str, float]) -> float:
        """Compute KL divergence between two weight distributions."""
        epsilon = 1e-10
        kl_div = 0.0
        
        for key in dist1:
            p = max(dist1.get(key, 0.0), epsilon)
            q = max(dist2.get(key, 0.0), epsilon)
            kl_div += p * np.log(p / q)
        
        return kl_div
    
    def _compute_reservoir_drift(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> float:
        """Compute drift distance between normalization reservoirs."""
        drift = 0.0
        count = 0
        
        for key in state1:
            if isinstance(state1[key], (int, float)) and isinstance(state2.get(key), (int, float)):
                drift += abs(state1[key] - state2.get(key, 0.0))
                count += 1
        
        return drift / count if count > 0 else 0.0
    
    def _compute_trajectory_divergence(self, traj1: List[float], traj2: List[float]) -> float:
        """Compute divergence between JT trajectories."""
        if len(traj1) == 0 and len(traj2) == 0:
            return 0.0
        
        if len(traj1) != len(traj2):
            # For different lengths, compute divergence on overlapping portion
            min_len = min(len(traj1), len(traj2))
            if min_len == 0:
                return float('inf')  # No overlap
            return np.mean([abs(a - b) for a, b in zip(traj1[:min_len], traj2[:min_len])])
        
        return np.mean([abs(a - b) for a, b in zip(traj1, traj2)])


class SimulationContext:
    """
    Simulation fork context manager for adaptive cognition forking.
    
    Provides isolated cognitive compartment for simulation workloads:
    - All adaptive mutations isolated
    - Persistence disabled
    - Entropy forked
    - Redis namespace isolated
    
    Usage:
        with SimulationContext(snapshot):
            # Run simulation workload
            # All mutations isolated from production
            # Persistence disabled
            # Entropy forked
            pass
    """
    
    def __init__(self, snapshot: CognitiveSnapshot, new_seed: Optional[int] = None):
        """
        Initialize simulation context from snapshot.
        
        Args:
            snapshot: CognitiveSnapshot to fork from
            new_seed: New entropy seed for simulation (if None, derive from snapshot)
        """
        self.snapshot = snapshot
        self.new_seed = new_seed if new_seed is not None else snapshot.entropy_seed + 1
        
        # Store original state for restoration
        self.original_context: Optional[CognitiveContext] = None
        self.simulation_context: Optional[CognitiveContext] = None
    
    def __enter__(self) -> CognitiveContext:
        """
        Enter simulation context.
        
        Returns:
            Forked CognitiveContext for simulation
        """
        # Create simulation context from snapshot
        self.simulation_context = CognitiveContext(
            seed=self.new_seed,
            context_type="simulation"
        )
        
        # Restore from snapshot (this will restore state including context_type)
        self.simulation_context.restore(self.snapshot)
        
        # CRITICAL: Override simulation-specific properties AFTER restore
        # The restore() method overwrites context_type and entropy_seed from snapshot
        self.simulation_context.entropy_seed = self.new_seed
        self.simulation_context.rng = np.random.default_rng(self.new_seed)
        self.simulation_context.context_type = "simulation"  # Force simulation type
        
        # Disable persistence
        self.simulation_context.persistence_enabled = False
        
        # Isolate Redis namespace
        self.simulation_context.redis_namespace = f"simulation_{self.snapshot.snapshot_id}"
        
        # Disable mutation (for read-only simulation) or enable (for writable simulation)
        self.simulation_context.mutation_allowed = True  # Simulation allows mutation
        
        # Update lifecycle contract
        self.simulation_context.lifecycle_contract = {
            'reset_preserves_priors': False,  # Simulation reset destroys state
            'reset_destroys_artifacts': True,
            'reset_reseeds_entropy': True,
            'persistence_enabled': False,  # Simulation has no persistence
            'mutation_allowed': True,  # Simulation allows mutation
            'replay_mode': False
        }
        
        # DEBUG: Log final state
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"SimulationContext.__enter__ final state: entropy_seed={self.simulation_context.entropy_seed}, context_type={self.simulation_context.context_type}")
        
        return self.simulation_context
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit simulation context.
        
        Ensures simulation mutations do not leak to production.
        """
        # Simulation context is discarded on exit
        # No restoration needed - simulation context is ephemeral
        self.simulation_context = None
        
        return False  # Don't suppress exceptions
