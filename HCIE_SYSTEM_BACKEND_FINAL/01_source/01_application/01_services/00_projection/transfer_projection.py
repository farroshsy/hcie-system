"""
Transfer Projection Service (Stateless View)

Projection service for transfer learning telemetry.
READ, AGGREGATE, FORMAT, EXPOSE ONLY - NO inference, mutation, synthesis.
Stateless view - NO temporal memory ownership, NO caching as authority.
Ephemeral non-authoritative response caching allowed (TTL 1-5s).
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class TransferTelemetry:
    """Transfer learning telemetry projection (stateless view)."""
    user_id: str
    transfer_metrics: Dict[str, Any]
    semantic_version: str = "1.0"


class TransferProjection:
    """
    Projection service for transfer learning telemetry.
    
    CRITICAL: Stateless view - NO temporal memory ownership.
    CRITICAL: NO cached_transfer_state - NO authority caching.
    CRITICAL: READ fresh from source every time (ephemeral response cache allowed).
    CRITICAL: NO inference, NO mutation, NO synthesis.
    """

    def __init__(
        self,
        unified_brain,  # From V2 (will be injected via DI)
    ):
        # NO cached_transfer_state - NO temporal memory ownership
        # NO state - always read fresh from source
        self.unified_brain = unified_brain

    def project_transfer_telemetry(self, user_id: str) -> TransferTelemetry:
        """
        Project transfer learning telemetry for a user.
        
        READ fresh from source every time.
        NO caching as authority.
        NO temporal memory ownership.
        """
        # READ fresh from source via V2 unified brain
        # NO inference
        # NO mutation
        # NO synthesis
        
        # Get transfer telemetry from V2 unified brain
        try:
            if hasattr(self.unified_brain, 'get_transfer_metrics'):
                metrics = self.unified_brain.get_transfer_metrics(user_id)
            else:
                # Fallback if method doesn't exist
                metrics = {
                    'transfer_effectiveness': 0.0,
                    'source_domain': 'unknown',
                    'target_domain': 'unknown'
                }
        except Exception:
            # Fallback if query fails
            metrics = {
                'transfer_effectiveness': 0.0,
                'source_domain': 'error',
                'target_domain': 'error'
            }
        
        return TransferTelemetry(
            user_id=user_id,
            transfer_metrics=metrics,
            semantic_version="1.0"
        )
