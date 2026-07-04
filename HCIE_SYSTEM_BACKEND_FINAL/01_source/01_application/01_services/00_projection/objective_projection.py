"""
Objective Projection Service (Stateless View)

Projection service for objective function and canonical state health.
READ, AGGREGATE, FORMAT, EXPOSE ONLY - NO inference, mutation, synthesis.
Stateless view - NO temporal memory ownership, NO caching as authority.
Ephemeral non-authoritative response caching allowed (TTL 1-5s).
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ObjectiveState:
    """Objective function state projection (stateless view)."""
    objective_function_value: float
    canonical_state_health: Dict[str, Any]
    research_metrics: Dict[str, float]
    semantic_version: str = "1.0"


class ObjectiveProjection:
    """
    Projection service for objective function and canonical state health.
    
    CRITICAL: Stateless view - NO temporal memory ownership.
    CRITICAL: NO cached_objective_state - NO authority caching.
    CRITICAL: READ fresh from source every time (ephemeral response cache allowed).
    CRITICAL: NO inference, NO mutation, NO synthesis.
    """

    def __init__(
        self,
        unified_brain,  # From V2 (will be injected via DI)
    ):
        # NO cached_objective_state - NO temporal memory ownership
        # NO state - always read fresh from source
        self.unified_brain = unified_brain

    def project_objective_state(self) -> ObjectiveState:
        """
        Project objective function state and canonical state health.
        
        READ fresh from source every time.
        NO caching as authority.
        NO temporal memory ownership.
        """
        # READ fresh from source via V2 unified brain
        # NO inference
        # NO mutation
        # NO synthesis
        
        # Get objective function value (system's north star metric)
        try:
            objective_value = self.unified_brain.get_objective_function()
        except Exception:
            objective_value = 0.0
        
        # Get canonical state health (monitoring metrics)
        try:
            canonical_health = self.unified_brain.get_canonical_state_health()
        except Exception:
            canonical_health = {
                'total_reads': 0,
                'total_misses': 0,
                'miss_rate': 0.0,
                'health': 'UNKNOWN',
                'message': 'Unable to retrieve canonical state health'
            }
        
        # Get research metrics (objective function foundation)
        try:
            research_metrics = self.unified_brain.get_research_metrics()
        except Exception:
            research_metrics = {}
        
        return ObjectiveState(
            objective_function_value=objective_value,
            canonical_state_health=canonical_health,
            research_metrics=research_metrics,
            semantic_version="1.0"
        )
