"""
Runtime API Package

Consolidates bounded runtime surfaces under a single entry point.
"""

from .governance import governance_router
from .mutations import mutations_router
from .events import events_router
from .replay import replay_router
from .lifecycle import lifecycle_router
from .trajectory import trajectory_router
from .authority import authority_router
from .objective import objective_router
from .recommendation import recommendation_router

__all__ = [
    'governance_router',
    'mutations_router',
    'events_router',
    'replay_router',
    'lifecycle_router',
    'trajectory_router',
    'authority_router',
    'objective_router',
    'recommendation_router'
]
