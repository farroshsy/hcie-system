"""
Session Management Utilities

Provides session management capabilities for user sessions,
including session creation, validation, expiration, and cleanup.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    """Status of a session"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    INVALID = "invalid"


class Session(BaseModel):
    """User session model"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique session identifier")
    user_id: str = Field(description="User identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    expires_at: datetime = Field(description="Session expiration time")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="Session status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="Client user agent")


class SessionManager:
    """
    Session manager for handling user sessions.
    
    Provides session creation, validation, expiration, and cleanup.
    Uses in-memory storage by default, can be extended to use Redis.
    """
    
    def __init__(
        self,
        default_ttl_minutes: int = 30,
        max_sessions_per_user: int = 5
    ):
        """
        Initialize session manager.
        
        Args:
            default_ttl_minutes: Default session TTL in minutes
            max_sessions_per_user: Maximum active sessions per user
        """
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        self.max_sessions_per_user = max_sessions_per_user
        self.sessions: Dict[str, Session] = {}
        self.user_sessions: Dict[str, List[str]] = {}
    
    def create_session(
        self,
        user_id: str,
        ttl_minutes: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Session:
        """
        Create a new session for a user.
        
        Args:
            user_id: User identifier
            ttl_minutes: Session TTL in minutes (uses default if not provided)
            metadata: Additional session metadata
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Created session
        """
        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self.default_ttl
        expires_at = datetime.utcnow() + ttl
        
        # Check if user has too many active sessions
        self._cleanup_expired_sessions(user_id)
        if len(self._get_active_sessions(user_id)) >= self.max_sessions_per_user:
            self._terminate_oldest_session(user_id)
        
        session = Session(
            user_id=user_id,
            expires_at=expires_at,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store session
        self.sessions[session.session_id] = session
        
        # Track user sessions
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session.session_id)
        
        logger.info(f"Created session {session.session_id} for user {user_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session if found and valid, None otherwise
        """
        session = self.sessions.get(session_id)
        
        if not session:
            return None
        
        # Check if session is expired
        if datetime.utcnow() > session.expires_at:
            session.status = SessionStatus.EXPIRED
            return None
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        
        return session
    
    def validate_session(self, session_id: str) -> bool:
        """
        Validate a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session is valid, False otherwise
        """
        session = self.get_session(session_id)
        return session is not None and session.status == SessionStatus.ACTIVE
    
    def terminate_session(self, session_id: str) -> bool:
        """
        Terminate a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was terminated, False otherwise
        """
        session = self.sessions.get(session_id)
        
        if not session:
            return False
        
        session.status = SessionStatus.TERMINATED
        
        # Remove from user sessions tracking
        if session.user_id in self.user_sessions:
            self.user_sessions[session.user_id] = [
                s_id for s_id in self.user_sessions[session.user_id]
                if s_id != session_id
            ]
        
        logger.info(f"Terminated session {session_id} for user {session.user_id}")
        return True
    
    def extend_session(
        self,
        session_id: str,
        ttl_minutes: Optional[int] = None
    ) -> bool:
        """
        Extend session expiration.
        
        Args:
            session_id: Session identifier
            ttl_minutes: New TTL in minutes (uses default if not provided)
            
        Returns:
            True if session was extended, False otherwise
        """
        session = self.sessions.get(session_id)
        
        if not session or session.status != SessionStatus.ACTIVE:
            return False
        
        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self.default_ttl
        session.expires_at = datetime.utcnow() + ttl
        session.last_activity = datetime.utcnow()
        
        logger.info(f"Extended session {session_id} to {session.expires_at}")
        return True
    
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of active sessions
        """
        self._cleanup_expired_sessions(user_id)
        
        session_ids = self.user_sessions.get(user_id, [])
        sessions = []
        
        for session_id in session_ids:
            session = self.sessions.get(session_id)
            if session and session.status == SessionStatus.ACTIVE:
                sessions.append(session)
        
        return sessions
    
    def cleanup_expired_sessions(self, user_id: Optional[str] = None) -> int:
        """
        Clean up expired sessions.
        
        Args:
            user_id: Optional user ID to clean up only for that user
            
        Returns:
            Number of sessions cleaned up
        """
        if user_id:
            return self._cleanup_expired_sessions(user_id)
        else:
            total_cleaned = 0
            for uid in list(self.user_sessions.keys()):
                total_cleaned += self._cleanup_expired_sessions(uid)
            return total_cleaned
    
    def _cleanup_expired_sessions(self, user_id: str) -> int:
        """Clean up expired sessions for a specific user."""
        session_ids = self.user_sessions.get(user_id, [])
        cleaned = 0
        
        for session_id in list(session_ids):
            session = self.sessions.get(session_id)
            
            if session and datetime.utcnow() > session.expires_at:
                session.status = SessionStatus.EXPIRED
                session_ids.remove(session_id)
                cleaned += 1
                logger.debug(f"Cleaned up expired session {session_id}")
        
        if cleaned > 0:
            self.user_sessions[user_id] = session_ids
        
        return cleaned
    
    def _terminate_oldest_session(self, user_id: str):
        """Terminate the oldest active session for a user."""
        session_ids = self.user_sessions.get(user_id, [])
        
        if not session_ids:
            return
        
        # Find oldest session
        oldest_session = None
        oldest_session_id = None
        
        for session_id in session_ids:
            session = self.sessions.get(session_id)
            if session and session.status == SessionStatus.ACTIVE:
                if oldest_session is None or session.created_at < oldest_session.created_at:
                    oldest_session = session
                    oldest_session_id = session_id
        
        if oldest_session_id:
            self.terminate_session(oldest_session_id)
    
    def _get_active_sessions(self, user_id: str) -> List[Session]:
        """Get active sessions for a user."""
        session_ids = self.user_sessions.get(user_id, [])
        active_sessions = []
        
        for session_id in session_ids:
            session = self.sessions.get(session_id)
            if session and session.status == SessionStatus.ACTIVE:
                active_sessions.append(session)
        
        return active_sessions
    
    def get_session_count(self, user_id: Optional[str] = None) -> int:
        """
        Get session count.
        
        Args:
            user_id: Optional user ID to count only for that user
            
        Returns:
            Number of active sessions
        """
        if user_id:
            return len(self.get_user_sessions(user_id))
        else:
            return sum(len(self.get_user_sessions(uid)) for uid in self.user_sessions.keys())


# Global session manager instance
_global_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance.
    
    Returns:
        SessionManager instance
    """
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager
