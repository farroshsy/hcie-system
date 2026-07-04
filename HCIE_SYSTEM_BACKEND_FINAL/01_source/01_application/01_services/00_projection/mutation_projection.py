"""
Mutation Projection Service (Stateless View)

Projection service for canonical mutation topology.
READ, AGGREGATE, FORMAT, EXPOSE ONLY - NO inference, mutation, synthesis.
Stateless view - NO temporal memory ownership, NO caching as authority.
Ephemeral non-authoritative response caching allowed (TTL 1-5s).
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class MutationStatus:
    """Mutation status projection (stateless view)."""
    mutation_id: str
    mutation_status: str
    event_propagation_status: Dict[str, Any]
    semantic_version: str = "1.0"


class MutationProjection:
    """
    Projection service for canonical mutation topology.
    
    CRITICAL: Stateless view - NO temporal memory ownership.
    CRITICAL: NO cached_mutation_state - NO authority caching.
    CRITICAL: READ fresh from source every time (ephemeral response cache allowed).
    CRITICAL: NO inference, NO mutation, NO synthesis.
    CRITICAL: All adaptive state mutations must flow through canonical topology.
    """

    def __init__(
        self,
        unified_brain,  # From V2 (will be injected via DI)
        outbox,  # From V2 (will be injected via DI)
    ):
        # NO cached_mutation_state - NO temporal memory ownership
        # NO state - always read fresh from source
        self.brain = unified_brain
        self.outbox = outbox

    def project_mutation_status(self, mutation_id: str) -> MutationStatus:
        """
        Project mutation status for a mutation ID.
        
        READ fresh from source every time.
        NO caching as authority.
        NO temporal memory ownership.
        """
        # READ fresh from source via V2 outbox
        # NO inference
        # NO mutation
        # NO synthesis
        
        # Get mutation status from V2 outbox
        try:
            # Check if outbox has mutation tracking
            if hasattr(self.outbox, 'get_mutation_status'):
                status = self.outbox.get_mutation_status(mutation_id)
            else:
                # Fallback: check if mutation exists in outbox
                status = {
                    'status': 'unknown',
                    'event_propagation': {
                        'outbox_status': 'unknown',
                        'kafka_status': 'unknown',
                        'dlq_status': 'empty'
                    }
                }
        except Exception:
            # Fallback if query fails
            status = {
                'status': 'error',
                'event_propagation': {
                    'outbox_status': 'error',
                    'kafka_status': 'error',
                    'dlq_status': 'error'
                }
            }
        
        return MutationStatus(
            mutation_id=mutation_id,
            mutation_status=status.get('status', 'unknown'),
            event_propagation_status=status.get('event_propagation', {}),
            semantic_version="1.0"
        )
