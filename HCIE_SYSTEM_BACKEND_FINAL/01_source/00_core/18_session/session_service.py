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

from typing import Optional, List
from datetime import datetime
import uuid

from core.session.models import (
    LearningSession,
    SessionStatus
)

"""Extracted from `HCIE_SYSTEM_BACKENDV2/core/session/session_service.py` by tools/migrate/split_session_and_ux.py.

Symbols: SessionService.
"""

class SessionService:
    """
    Service for managing learning session lifecycle.
    
    D1 - Full Persistence Closure:
    Now uses PostgreSQL repositories for durable session storage.
    
    This provides session-level continuity and statistics tracking.
    """
    
    def __init__(self, session_repository, postgres_repo=None):
        """
        Initialize session service.
        
        Args:
            session_repository: Repository for session persistence (in-memory fallback)
            postgres_repo: PostgreSQL repository for durable storage (optional)
        """
        self.session_repository = session_repository
        self._postgres_repo = postgres_repo  # PostgreSQL repository for D1 persistence closure
    
    def start_session(
        self,
        user_id: str,
        tenant_id: str,
        target_concepts: List[str],
        initial_concept_id: Optional[str] = None
    ) -> LearningSession:
        """
        Start a new learning session.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            target_concepts: List of concept IDs to learn in this session
            initial_concept_id: Optional starting concept (if None, uses first target)
        
        Returns:
            Created LearningSession
        """
        session_id = str(uuid.uuid4())
        
        # If no initial concept specified, use first target concept
        if initial_concept_id is None and target_concepts:
            initial_concept_id = target_concepts[0]
        
        session = LearningSession(
            id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            status=SessionStatus.ACTIVE,
            started_at=datetime.utcnow(),
            current_concept_id=initial_concept_id,
            target_concepts=target_concepts,
            tasks_completed=0,
            tasks_attempted=0,
            correct_count=0,
            current_streak=0,
            best_streak=0,
            research_metadata={
                "created_by": "session_service",
                "version": "1.0"
            }
        )
        
        # Persist session to PostgreSQL (repository enforces authority)
        self.session_repository.save(session)
        
        return session
    
    def pause_session(self, session_id: str) -> Optional[LearningSession]:
        """
        Pause an active session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Updated LearningSession or None if not found
        """
        session = self.session_repository.get(session_id)
        if session is None:
            return None
        
        if session.status != SessionStatus.ACTIVE:
            return session
        
        session.status = SessionStatus.PAUSED
        session.paused_at = datetime.utcnow()
        # Persist to PostgreSQL (repository enforces authority)
        self.session_repository.save(session)
        
        return session
    
    def resume_session(self, session_id: str) -> Optional[LearningSession]:
        """
        Resume a paused session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Updated LearningSession or None if not found
        """
        session = self.session_repository.get(session_id)
        if session is None:
            return None
        
        if session.status != SessionStatus.PAUSED:
            return session
        
        session.status = SessionStatus.ACTIVE
        # Persist to PostgreSQL (repository enforces authority)
        self.session_repository.save(session)
        
        return session
    
    def complete_session(self, session_id: str) -> Optional[LearningSession]:
        """
        Complete an active session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Updated LearningSession or None if not found
        """
        session = self.session_repository.get(session_id)
        if session is None:
            return None
        
        if session.status != SessionStatus.ACTIVE:
            return session
        
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        # Persist to PostgreSQL (repository enforces authority)
        self.session_repository.save(session)
        
        return session
    
    def abandon_session(self, session_id: str) -> Optional[LearningSession]:
        """
        Abandon an active or paused session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Updated LearningSession or None if not found
        """
        session = self.session_repository.get(session_id)
        if session is None:
            return None
        
        if session.status in [SessionStatus.COMPLETED, SessionStatus.ABANDONED]:
            return session
        
        session.status = SessionStatus.ABANDONED
        session.abandoned_at = datetime.utcnow()
        # Persist to PostgreSQL (repository enforces authority)
        self.session_repository.save(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[LearningSession]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
        
        Returns:
            LearningSession or None if not found
        """
        return self.session_repository.get(session_id)
    
    def get_active_session_for_user(self, user_id: str) -> Optional[LearningSession]:
        """
        Get the active session for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Active LearningSession or None if not found
        """
        return self.session_repository.get_active_by_user(user_id)
    
    def update_session_statistics(
        self,
        session_id: str,
        task_completed: bool = False,
        correct: bool = False
    ) -> Optional[LearningSession]:
        """
        Update session statistics after a task attempt.
        
        Args:
            session_id: Session identifier
            task_completed: Whether a task was completed
            correct: Whether the task was correct
        
        Returns:
            Updated LearningSession or None if not found
        """
        session = self.session_repository.get(session_id)
        if session is None:
            return None
        
        if task_completed:
            session.tasks_completed += 1
            session.tasks_attempted += 1
            
            if correct:
                session.correct_count += 1
                session.current_streak += 1
                if session.current_streak > session.best_streak:
                    session.best_streak = session.current_streak
            else:
                session.current_streak = 0
        else:
            session.tasks_attempted += 1
        
        self.session_repository.save(session)
        
        return session
    
    def advance_to_concept(
        self,
        session_id: str,
        new_concept_id: str
    ) -> Optional[LearningSession]:
        """
        Advance session to a new concept.
        
        Args:
            session_id: Session identifier
            new_concept_id: New concept identifier
        
        Returns:
            Updated LearningSession or None if not found
        """
        session = self.session_repository.get(session_id)
        if session is None:
            return None
        
        session.current_concept_id = new_concept_id
        self.session_repository.save(session)
        
        return session


# --- traceability ---------------------------------------------------------
__sliced_from__ = 'HCIE_SYSTEM_BACKENDV2/core/session/session_service.py'
__symbol_ranges__ = {
    'SessionService': (32, 283),
}
