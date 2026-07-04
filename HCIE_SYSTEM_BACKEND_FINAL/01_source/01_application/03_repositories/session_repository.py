"""
Session Service - Session Lifecycle Management

D1.5 - Semantic Read Authority Fix:
Postgres = authority, Memory = cache only.
Repository enforces PostgreSQL authority, no dual writes.

This service manages the lifecycle of learning sessions:
- Start session
- Pause session
- Complete session
- Abandon session

Key Design Principles:
- Session continuity across multiple task attempts
- Curriculum context tracking
- Session statistics aggregation
- Research metadata preservation
- Single source of truth (PostgreSQL)
"""

from typing import Optional
from datetime import datetime

from core.session.models import (
    LearningSession,
    SessionStatus
)

"""Extracted from `HCIE_SYSTEM_BACKENDV2/core/session/session_service.py` by tools/migrate/split_session_and_ux.py.

Symbols: SessionRepository.
"""

class SessionRepository:
    """
    Repository for session persistence.
    
    This is a placeholder implementation. In production, this would
    interface with PostgreSQL or another persistent store.
    """
    
    def __init__(self):
        self._sessions = {}
    
    def save(self, session: LearningSession):
        """Save a session."""
        self._sessions[session.id] = session
    
    def get(self, session_id: str) -> Optional[LearningSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)
    
    def get_active_by_user(self, user_id: str) -> Optional[LearningSession]:
        """Get the active session for a user."""
        for session in self._sessions.values():
            if session.user_id == user_id and session.status == SessionStatus.ACTIVE:
                return session
        return None
    
    def delete(self, session_id: str):
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]


# --- traceability ---------------------------------------------------------
__sliced_from__ = 'HCIE_SYSTEM_BACKENDV2/core/session/session_service.py'
__symbol_ranges__ = {
    'SessionRepository': (285, 315),
}
