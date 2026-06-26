"""
Replay Projection Service (Stateless View)

Projection service for replay state and results.
READ, AGGREGATE, FORMAT, EXPOSE ONLY - NO inference, mutation, synthesis.
Stateless view - NO temporal memory ownership, NO caching as authority.
Ephemeral non-authoritative response caching allowed (TTL 1-5s).
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ReplayState:
    """Replay state projection (stateless view)."""
    replay_id: str
    replay_status: str
    replay_results: Dict[str, Any]
    semantic_version: str = "1.0"


class ReplayProjection:
    """
    Projection service for replay state and results.
    
    CRITICAL: Stateless view - NO temporal memory ownership.
    CRITICAL: NO cached_replay_state - NO authority caching.
    CRITICAL: READ fresh from source every time (ephemeral response cache allowed).
    CRITICAL: NO inference, NO mutation, NO synthesis.
    """

    def __init__(
        self,
        replay_engine,  # From V2 (will be injected via DI)
    ):
        # NO cached_replay_state - NO temporal memory ownership
        # NO state - always read fresh from source
        self.replay_engine = replay_engine

    def project_replay_status(self, replay_id: str) -> ReplayState:
        """
        Project replay status for a replay ID.
        
        READ fresh from source every time.
        NO caching as authority.
        NO temporal memory ownership.
        """
        # READ fresh from source via V2 replay engine
        # NO inference
        # NO mutation
        # NO synthesis
        
        # Get replay status from V2 replay engine
        try:
            if hasattr(self.replay_engine, 'get_replay_status'):
                status = self.replay_engine.get_replay_status(replay_id)
            else:
                # Fallback if method doesn't exist
                status = {
                    'replay_id': replay_id,
                    'status': 'unknown',
                    'results': {}
                }
        except Exception:
            # Fallback if query fails
            status = {
                'replay_id': replay_id,
                'status': 'error',
                'results': {}
            }
        
        return ReplayState(
            replay_id=replay_id,
            replay_status=status.get('status', 'unknown'),
            replay_results=status.get('results', {}),
            semantic_version="1.0"
        )
