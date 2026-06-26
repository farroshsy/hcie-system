"""
Attribution Projection Service (Stateless View)

Projection service for attribution telemetry.
READ, AGGREGATE, FORMAT, EXPOSE ONLY - NO inference, mutation, synthesis.
Stateless view - NO temporal memory ownership, NO caching as authority.
Ephemeral non-authoritative response caching allowed (TTL 1-5s).
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class AttributionTelemetry:
    """Attribution telemetry projection (stateless view)."""
    user_id: str
    attribution_metrics: Dict[str, Any]
    semantic_version: str = "1.0"


class AttributionProjection:
    """
    Projection service for attribution telemetry.
    
    CRITICAL: Stateless view - NO temporal memory ownership.
    CRITICAL: NO cached_attribution_state - NO authority caching.
    CRITICAL: READ fresh from source every time (ephemeral response cache allowed).
    CRITICAL: NO inference, NO mutation, NO synthesis.
    """

    def __init__(
        self,
        unified_brain,  # From V2 (will be injected via DI)
    ):
        # NO cached_attribution_state - NO temporal memory ownership
        # NO state - always read fresh from source
        self.unified_brain = unified_brain

    def project_attribution_telemetry(self, user_id: str) -> AttributionTelemetry:
        """
        Project attribution telemetry for a user.
        
        READ fresh from source every time.
        NO caching as authority.
        NO temporal memory ownership.
        """
        # READ fresh from source via V2 unified brain
        # NO inference
        # NO mutation
        # NO synthesis
        
        # Get attribution telemetry from V2 unified brain
        try:
            if hasattr(self.unified_brain, 'get_attribution_metrics'):
                metrics = self.unified_brain.get_attribution_metrics(user_id)
            else:
                # Fallback if method doesn't exist
                metrics = {
                    'contribution_weights': {},
                    'learner_attribution': {},
                    'jt_attribution': 0.0
                }
        except Exception:
            # Fallback if query fails
            metrics = {
                'contribution_weights': {},
                'learner_attribution': {},
                'jt_attribution': 0.0
            }
        
        return AttributionTelemetry(
            user_id=user_id,
            attribution_metrics=metrics,
            semantic_version="1.0"
        )
