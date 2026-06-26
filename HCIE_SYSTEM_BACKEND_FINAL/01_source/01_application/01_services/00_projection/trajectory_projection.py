"""
Trajectory Projection Service (Stateless View)

Projection service for trajectory state and history.
READ, AGGREGATE, FORMAT, EXPOSE ONLY - NO inference, mutation, synthesis.
Stateless view - NO temporal memory ownership, NO caching as authority.
Ephemeral non-authoritative response caching allowed (TTL 1-5s).
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class TrajectoryState:
    """Trajectory state projection (stateless view)."""
    user_id: str
    trajectory_data: list[float]
    trajectory_metadata: Dict[str, Any]
    semantic_version: str = "1.0"


class TrajectoryProjection:
    """
    Projection service for trajectory state and history.
    
    CRITICAL: Stateless view - NO temporal memory ownership.
    CRITICAL: NO cached_trajectory_state - NO authority caching.
    CRITICAL: READ fresh from source every time (ephemeral response cache allowed).
    CRITICAL: NO inference, NO mutation, NO synthesis.
    """

    def __init__(
        self,
        postgres_store,  # From V2 (will be injected via DI)
    ):
        # NO cached_trajectory_state - NO temporal memory ownership
        # NO state - always read fresh from source
        self.store = postgres_store

    def project_trajectory_state(self, user_id: str) -> TrajectoryState:
        """
        Project trajectory state for a user.
        
        READ fresh from source every time.
        NO caching as authority.
        NO temporal memory ownership.
        """
        # READ fresh from source via V2 postgres store
        # NO inference
        # NO mutation
        # NO synthesis
        
        # Get trajectory from V2 postgres store
        try:
            query = """
                SELECT jt_value, metadata, timestamp
                FROM trajectory_records
                WHERE user_id = %s
                ORDER BY timestamp ASC
                LIMIT 100
            """
            trajectories = self.store.execute_read(query, (user_id,))
            
            if trajectories:
                trajectory_data = [t['jt_value'] for t in trajectories]
                # Get metadata from the most recent record
                trajectory_metadata = trajectories[-1].get('metadata', {})
            else:
                trajectory_data = []
                trajectory_metadata = {}
        except Exception:
            # Fallback if query fails
            trajectory_data = []
            trajectory_metadata = {}
        
        return TrajectoryState(
            user_id=user_id,
            trajectory_data=trajectory_data,
            trajectory_metadata=trajectory_metadata,
            semantic_version="1.0"
        )
