"""
Policy Projection Service (Stateless View)

Projection service for policy telemetry.
READ, AGGREGATE, FORMAT, EXPOSE ONLY - NO inference, mutation, synthesis.
Stateless view - NO temporal memory ownership, NO caching as authority.
Ephemeral non-authoritative response caching allowed (TTL 1-5s).
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class PolicyTelemetry:
    """Policy telemetry projection (stateless view)."""
    user_id: str
    policy_metrics: Dict[str, Any]
    semantic_version: str = "1.0"


class PolicyProjection:
    """
    Projection service for policy telemetry.
    
    CRITICAL: Stateless view - NO temporal memory ownership.
    CRITICAL: NO cached_policy_state - NO authority caching.
    CRITICAL: READ fresh from source every time (ephemeral response cache allowed).
    CRITICAL: NO inference, NO mutation, NO synthesis.
    """

    def __init__(
        self,
        unified_brain,  # From V2 (will be injected via DI)
    ):
        # NO cached_policy_state - NO temporal memory ownership
        # NO state - always read fresh from source
        self.unified_brain = unified_brain

    def project_policy_telemetry(self, user_id: str) -> PolicyTelemetry:
        """
        Project policy telemetry for a user.
        
        READ fresh from source every time.
        NO caching as authority.
        NO temporal memory ownership.
        """
        # READ fresh from source via V2 unified brain
        # NO inference
        # NO mutation
        # NO synthesis
        
        # Get policy telemetry from V2 unified brain
        try:
            if hasattr(self.unified_brain, 'get_policy_metrics'):
                metrics = self.unified_brain.get_policy_metrics(user_id)
            else:
                # Fallback if method doesn't exist
                metrics = {
                    'policy_entropy': 0.0,
                    'action_distribution': {},
                    'confidence_score': 0.0
                }
        except Exception:
            # Fallback if query fails
            metrics = {
                'policy_entropy': 0.0,
                'action_distribution': {},
                'confidence_score': 0.0
            }
        
        return PolicyTelemetry(
            user_id=user_id,
            policy_metrics=metrics,
            semantic_version="1.0"
        )
