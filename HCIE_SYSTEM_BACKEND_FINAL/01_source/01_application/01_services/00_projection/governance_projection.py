"""
Governance Projection Service (Stateless View)

Projection service for governance state and trajectory.
READ, AGGREGATE, FORMAT, EXPOSE ONLY - NO inference, mutation, synthesis.
Stateless view - NO temporal memory ownership, NO caching as authority.
Ephemeral non-authoritative response caching allowed (TTL 1-5s).
"""

from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GovernanceState:
    """Governance state projection (stateless view)."""
    governance_weights: Dict[str, float]
    normalization_state: Dict[str, Any]
    component_history: Dict[str, Any]
    semantic_version: str = "1.0"


@dataclass
class GovernanceTrajectory:
    """Governance trajectory projection (stateless view)."""
    jt_trajectory: list[float]
    component_history: Dict[str, Any]
    semantic_version: str = "1.0"


class GovernanceProjection:
    """
    Projection service for governance state and trajectory.
    
    CRITICAL: Stateless view - NO temporal memory ownership.
    CRITICAL: NO cached_governance_snapshot - NO authority caching.
    CRITICAL: READ fresh from source every time (ephemeral response cache allowed).
    CRITICAL: NO inference, NO mutation, NO synthesis.
    """

    def __init__(
        self,
        constitutional_jt_governance,  # From V2 (will be injected via DI)
        postgres_store,  # From V2 (will be injected via DI)
    ):
        # NO cached_governance_snapshot - NO temporal memory ownership
        # NO state - always read fresh from source
        self.governance = constitutional_jt_governance
        self.store = postgres_store

    def project_state(self, user_id: str) -> GovernanceState:
        """
        Project governance state for a user.
        
        READ fresh from source every time.
        NO caching as authority.
        NO temporal memory ownership.
        """
        # READ fresh from source via V2 governance system
        # NO inference
        # NO mutation
        # NO synthesis
        
        # Get governance state from V2 ConstitutionalJTGovernance
        # The governance object has methods to get state
        try:
            # Access governance weights and state
            governance_weights = self.governance.get_weights() if hasattr(self.governance, 'get_weights') else {}
            normalization_state = self.governance.get_normalization_state() if hasattr(self.governance, 'get_normalization_state') else {}
            component_history = self.governance.get_component_history() if hasattr(self.governance, 'get_component_history') else {}
        except Exception:
            # Fallback if methods don't exist
            governance_weights = {}
            normalization_state = {}
            component_history = {}
        
        return GovernanceState(
            governance_weights=governance_weights,
            normalization_state=normalization_state,
            component_history=component_history,
            semantic_version="1.0"
        )

    def project_trajectory(self, user_id: str) -> GovernanceTrajectory:
        """
        Project governance trajectory for a user.
        
        READ fresh from source every time.
        NO caching as authority.
        NO temporal memory ownership.
        """
        # READ fresh from source via V2 store
        # NO inference
        # NO mutation
        # NO synthesis
        
        # Get trajectory from V2 postgres store
        try:
            # Query trajectory from database
            query = """
                SELECT jt_value, component_history, timestamp
                FROM trajectory_records
                WHERE user_id = %s
                ORDER BY timestamp ASC
                LIMIT 100
            """
            trajectories = self.store.execute_read(query, (user_id,))
            
            if trajectories:
                jt_trajectory = [t['jt_value'] for t in trajectories]
                # Get component history from the most recent record
                component_history = trajectories[-1].get('component_history', {})
            else:
                jt_trajectory = []
                component_history = {}
        except Exception:
            # Fallback if query fails
            jt_trajectory = []
            component_history = {}
        
        return GovernanceTrajectory(
            jt_trajectory=jt_trajectory,
            component_history=component_history,
            semantic_version="1.0"
        )
