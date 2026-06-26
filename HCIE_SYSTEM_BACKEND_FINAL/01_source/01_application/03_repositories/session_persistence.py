"""
Session Runtime Repositories - Persistent Cognitive State Binding

D1.5 - Semantic Read Authority Fix:
Postgres = authority, Memory = acceleration artifact only.
Reads: Postgres → cache hydrate → return.
NEVER fallback semantically to stale memory.

Key Design Principles:
- Postgres is single source of truth
- Memory is ephemeral cache only (non-authoritative)
- No dual truth surfaces
- Replay-safe semantics
- Follows LearningStateRepository pattern
"""

from typing import Optional, List, Dict
from datetime import datetime, timedelta

from core.session.models import (
    LearningSession,
    TaskAttempt,
    AdaptationEvent,
    LearnerProjection,
    SessionStatus,
    TaskOutcome,
    AdaptationType
)


def get_postgres_session_repositories(postgres_store):
    """
    Get PostgreSQL session runtime repositories.
    
    Args:
        postgres_store: PostgreSQL store instance
    
    Returns:
        Dictionary of PostgreSQL repositories
    """
    try:
        from app.repositories.session_runtime_repository import (
            LearningSessionRepository,
            TaskAttemptRepository,
            AdaptationEventRepository,
            LearnerProjectionRepository,
            ConsumerProgressRepository
        )
        
        return {
            'learning_session': LearningSessionRepository(postgres_store),
            'task_attempt': TaskAttemptRepository(postgres_store),
            'adaptation_event': AdaptationEventRepository(postgres_store),
            'learner_projection': LearnerProjectionRepository(postgres_store),
            'consumer_progress': ConsumerProgressRepository(postgres_store)
        }
    except ImportError:
        return None


class LearnerProgressRepository:
    """
    Repository for learner progress persistence.
    
    D1.5 - Semantic Read Authority:
    Postgres = authority, Memory = cache only.
    Follows LearningStateRepository pattern.
    """
    
    def __init__(self, postgres_repo=None):
        self._cache = {}  # Ephemeral cache only (non-authoritative)
        self._postgres_repo = postgres_repo  # PostgreSQL authority
    
    def save(self, projection: LearnerProjection):
        """Save learner projection to PostgreSQL authority, update cache."""
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Write to PostgreSQL (authority)
        self._postgres_repo.save(projection)
        
        # Update cache (acceleration artifact)
        self._cache[projection.user_id] = projection
    
    def get(self, user_id: str) -> Optional[LearnerProjection]:
        """
        Get learner projection by user ID.
        
        Pattern: Postgres → cache hydrate → return.
        NEVER fallback semantically to stale memory.
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Try cache first (acceleration)
        if user_id in self._cache:
            return self._cache[user_id]
        
        # Hydrate from PostgreSQL (authority)
        projection = self._postgres_repo.get(user_id)
        
        # Cache result for future acceleration
        if projection:
            self._cache[user_id] = projection
        
        return projection
    
    def get_or_create(self, user_id: str) -> LearnerProjection:
        """
        Get or create learner projection.
        
        D1.5: Creates in PostgreSQL authority, not in-memory.
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Try to get from PostgreSQL
        projection = self.get(user_id)
        
        if projection:
            return projection
        
        # Create new projection in PostgreSQL
        new_projection = LearnerProjection(
            user_id=user_id,
            updated_at=datetime.utcnow()
        )
        
        self.save(new_projection)
        return new_projection
    
    def update_mastery(self, user_id: str, concept_id: str, mastery_value: float):
        """Update mastery for a specific concept."""
        projection = self.get_or_create(user_id)
        projection.concept_mastery[concept_id] = int(mastery_value * 100)  # Convert to 0-100 scale
        projection.updated_at = datetime.utcnow()
    
    def get_mastery(self, user_id: str, concept_id: str) -> float:
        """Get mastery for a specific concept (0-1 scale)."""
        projection = self.get(user_id)
        if projection and concept_id in projection.concept_mastery:
            return projection.concept_mastery[concept_id] / 100.0
        return 0.0
    
    def get_all_mastery(self, user_id: str) -> Dict[str, float]:
        """Get all mastery values (0-1 scale)."""
        projection = self.get(user_id)
        if not projection:
            return {}
        return {k: v / 100.0 for k, v in projection.concept_mastery.items()}


class TaskAttemptRepository:
    """
    Repository for task attempt persistence.
    
    D1.5 - Semantic Read Authority:
    Postgres = authority, Memory = cache only.
    Follows LearningStateRepository pattern.
    """
    
    def __init__(self, postgres_repo=None):
        self._cache = {}  # Ephemeral cache only (non-authoritative)
        self._postgres_repo = postgres_repo  # PostgreSQL authority
    
    def save(self, attempt: TaskAttempt):
        """Save task attempt to PostgreSQL authority, update cache."""
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Write to PostgreSQL (authority)
        self._postgres_repo.save(attempt)
        
        # Update cache (acceleration artifact)
        if attempt.session_id not in self._cache:
            self._cache[attempt.session_id] = []
        self._cache[attempt.session_id].append(attempt)
    
    def get_by_id(self, attempt_id: str) -> Optional[TaskAttempt]:
        """
        Get task attempt by ID.
        
        Pattern: Postgres → cache hydrate → return.
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Try cache first (acceleration)
        for attempts in self._cache.values():
            for attempt in attempts:
                if attempt.id == attempt_id:
                    return attempt
        
        # Hydrate from PostgreSQL (authority)
        return self._postgres_repo.get_by_id(attempt_id)
    
    def get_by_session(self, session_id: str) -> List[TaskAttempt]:
        """
        Get all attempts for a session.
        
        Pattern: Postgres → cache hydrate → return.
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Try cache first (acceleration)
        if session_id in self._cache:
            return self._cache[session_id]
        
        # Hydrate from PostgreSQL (authority)
        attempts = self._postgres_repo.get_by_session(session_id)
        
        # Cache result for future acceleration
        if attempts:
            self._cache[session_id] = attempts
        
        return attempts or []
    
    def get_by_user(self, user_id: str, limit: int = 100) -> List[TaskAttempt]:
        """
        Get recent attempts for a user.
        
        Pattern: Postgres → return (no cache for user-wide queries).
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Always query PostgreSQL (authority)
        return self._postgres_repo.get_by_user(user_id, limit)
    
    def get_recent_performance(self, user_id: str, window_minutes: int = 60) -> Dict[str, float]:
        """
        Get recent performance metrics for a user.
        
        Pattern: Postgres → return (no cache for derived metrics).
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Always query PostgreSQL (authority)
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_attempts = self._postgres_repo.get_by_user(user_id, limit=1000)
        
        # Filter by time window
        recent_attempts = [
            a for a in recent_attempts
            if a.started_at >= cutoff
        ]
        
        if not recent_attempts:
            return {"accuracy": 0.0, "attempts": 0, "current_streak": 0, "best_streak": 0}
        
        correct_count = sum(1 for a in recent_attempts if a.outcome == TaskOutcome.CORRECT)
        accuracy = correct_count / len(recent_attempts)
        
        # Calculate streak
        current_streak = 0
        best_streak = 0
        temp_streak = 0
        
        for attempt in reversed(recent_attempts):  # Oldest to newest
            if attempt.outcome == TaskOutcome.CORRECT:
                temp_streak += 1
            else:
                best_streak = max(best_streak, temp_streak)
                temp_streak = 0
        
        current_streak = temp_streak
        best_streak = max(best_streak, current_streak)
        
        return {
            "accuracy": accuracy,
            "attempts": len(recent_attempts),
            "current_streak": current_streak,
            "best_streak": best_streak
        }
    
    def get_completed_task_ids(self, user_id: str) -> List[str]:
        """
        Get list of completed task IDs for a user.
        
        Pattern: Postgres → return (no cache for derived queries).
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Always query PostgreSQL (authority)
        attempts = self._postgres_repo.get_by_user(user_id, limit=1000)
        return [a.task_id for a in attempts if a.outcome == TaskOutcome.CORRECT]


class AdaptationEventRepository:
    """
    Repository for adaptation event persistence.
    
    D1.5 - Semantic Read Authority:
    Postgres = authority, Memory = cache only.
    Follows LearningStateRepository pattern.
    """
    
    def __init__(self, postgres_repo=None):
        self._cache = {}  # Ephemeral cache only (non-authoritative)
        self._postgres_repo = postgres_repo  # PostgreSQL authority
    
    def save(self, event: AdaptationEvent):
        """Save adaptation event to PostgreSQL authority, update cache."""
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Write to PostgreSQL (authority)
        self._postgres_repo.save(event)
        
        # Update cache (acceleration artifact)
        if event.session_id not in self._cache:
            self._cache[event.session_id] = []
        self._cache[event.session_id].append(event)
    
    def get_by_id(self, event_id: str) -> Optional[AdaptationEvent]:
        """
        Get adaptation event by ID.
        
        Pattern: Postgres → cache hydrate → return.
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Try cache first (acceleration)
        for events in self._cache.values():
            for event in events:
                if event.id == event_id:
                    return event
        
        # Hydrate from PostgreSQL (authority)
        return self._postgres_repo.get_by_id(event_id)
    
    def get_by_session(self, session_id: str) -> List[AdaptationEvent]:
        """
        Get all adaptation events for a session.
        
        Pattern: Postgres → cache hydrate → return.
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Try cache first (acceleration)
        if session_id in self._cache:
            return self._cache[session_id]
        
        # Hydrate from PostgreSQL (authority)
        events = self._postgres_repo.get_by_session(session_id)
        
        # Cache result for future acceleration
        if events:
            self._cache[session_id] = events
        
        return events or []
    
    def get_by_user(self, user_id: str, limit: int = 100) -> List[AdaptationEvent]:
        """
        Get recent adaptation events for a user.
        
        Pattern: Postgres → return (no cache for user-wide queries).
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Always query PostgreSQL (authority)
        return self._postgres_repo.get_by_user(user_id, limit)
    
    def get_by_type(self, user_id: str, adaptation_type: AdaptationType) -> List[AdaptationEvent]:
        """
        Get adaptation events of a specific type for a user.
        
        Pattern: Postgres → return (no cache for derived queries).
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Always query PostgreSQL (authority)
        user_events = self._postgres_repo.get_by_user(user_id, limit=1000)
        return [e for e in user_events if e.adaptation_type == adaptation_type]


class LearningSessionRepository:
    """
    Repository for learning session persistence.
    
    D1.5 - Semantic Read Authority:
    Postgres = authority, Memory = cache only.
    Follows LearningStateRepository pattern.
    """
    
    def __init__(self, postgres_repo=None):
        self._cache = {}  # Ephemeral cache only (non-authoritative)
        self._postgres_repo = postgres_repo  # PostgreSQL authority
    
    def save(self, session: LearningSession):
        """Save learning session to PostgreSQL authority, update cache."""
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Write to PostgreSQL (authority)
        self._postgres_repo.save(session)
        
        # Update cache (acceleration artifact)
        self._cache[session.id] = session
    
    def get(self, session_id: str) -> Optional[LearningSession]:
        """
        Get learning session by ID.
        
        Pattern: Postgres → cache hydrate → return.
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Try cache first (acceleration)
        if session_id in self._cache:
            return self._cache[session_id]
        
        # Hydrate from PostgreSQL (authority)
        session = self._postgres_repo.get(session_id)
        
        # Cache result for future acceleration
        if session:
            self._cache[session_id] = session
        
        return session
    
    def get_active_by_user(self, user_id: str) -> Optional[LearningSession]:
        """
        Get active session for a user.
        
        Pattern: Postgres → return (no cache for derived queries).
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Always query PostgreSQL (authority)
        return self._postgres_repo.get_active_by_user(user_id)
    
    def get_by_user(self, user_id: str, limit: int = 10) -> List[LearningSession]:
        """
        Get recent sessions for a user.
        
        Pattern: Postgres → return (no cache for derived queries).
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Always query PostgreSQL (authority)
        return self._postgres_repo.get_by_user(user_id, limit)
    
    def delete(self, session_id: str):
        """
        Delete a session.
        
        Pattern: Postgres authority, invalidate cache.
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Delete from PostgreSQL (authority)
        self._postgres_repo.delete(session_id)
        
        # Invalidate cache
        if session_id in self._cache:
            del self._cache[session_id]
    
    def update_status(self, session_id: str, status: SessionStatus):
        """
        Update session status.
        
        Pattern: Postgres authority, invalidate cache.
        """
        if not self._postgres_repo:
            raise RuntimeError("PostgreSQL repository required - no fallback to in-memory authority")
        
        # Update in PostgreSQL (authority)
        self._postgres_repo.update_status(session_id, status)
        
        # Invalidate cache to force fresh read next time
        if session_id in self._cache:
            del self._cache[session_id]
