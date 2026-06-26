"""
Lifecycle Projection Service (Stateless View)

Projection service for lifecycle state and transitions.
READ, AGGREGATE, FORMAT, EXPOSE ONLY - NO inference, mutation, synthesis.
Stateless view - NO temporal memory ownership, NO caching as authority.
Ephemeral non-authoritative response caching allowed (TTL 1-5s).
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class LifecycleState:
    """Lifecycle state projection (stateless view)."""
    user_id: str
    lifecycle_state: str
    state_transitions: list[Dict[str, Any]]
    semantic_version: str = "1.0"


class LifecycleProjection:
    """
    Projection service for lifecycle state and transitions.
    
    CRITICAL: Stateless view - NO temporal memory ownership.
    CRITICAL: NO cached_lifecycle_state - NO authority caching.
    CRITICAL: READ fresh from source every time (ephemeral response cache allowed).
    CRITICAL: NO inference, NO mutation, NO synthesis.
    """

    def __init__(
        self,
        session_service,  # From V2 (will be injected via DI)
    ):
        # NO cached_lifecycle_state - NO temporal memory ownership
        # NO state - always read fresh from source
        self.session_service = session_service

    def project_lifecycle_state(self, user_id: str) -> LifecycleState:
        """
        Project lifecycle state for a user.
        
        READ fresh from source every time.
        NO caching as authority.
        NO temporal memory ownership.
        """
        # READ fresh from source via V2 session service
        # NO inference
        # NO mutation
        # NO synthesis
        
        # Get lifecycle state from V2 session service
        try:
            if hasattr(self.session_service, 'get_lifecycle_state'):
                state = self.session_service.get_lifecycle_state(user_id)
            else:
                # Fallback if method doesn't exist
                state = {
                    'user_id': user_id,
                    'lifecycle_state': 'unknown',
                    'transitions': []
                }
        except Exception:
            # Fallback if query fails
            state = {
                'user_id': user_id,
                'lifecycle_state': 'error',
                'transitions': []
            }
        
        return LifecycleState(
            user_id=user_id,
            lifecycle_state=state.get('lifecycle_state', 'unknown'),
            state_transitions=state.get('transitions', []),
            semantic_version="1.0"
        )
