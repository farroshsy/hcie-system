"""
Auth Domain Events
Event-driven architecture for authentication system
"""

from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import json
import logging

logger = logging.getLogger(__name__)

class AuthEventType(str, Enum):
    USER_REGISTERED = "user_registered"
    USER_LOGGED_IN = "user_logged_in"
    TOKEN_REFRESHED = "token_refreshed"
    USER_PROFILE_UPDATED = "user_profile_updated"
    USER_LOGGED_OUT = "user_logged_out"
    PASSWORD_CHANGED = "password_changed"

@dataclass
class AuthEvent:
    """Base auth event"""
    user_id: str
    timestamp: datetime
    event_type: AuthEventType
    email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for Kafka"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        if self.metadata:
            data['metadata'] = self.metadata
        return data
    
    def to_json(self) -> str:
        """Convert event to JSON for Kafka"""
        return json.dumps(self.to_dict())

@dataclass
class UserRegisteredEvent(AuthEvent):
    """User registration event"""
    event_type: AuthEventType = AuthEventType.USER_REGISTERED
    name: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[str] = None
    experiment_group: Optional[str] = None
    
    def __post_init__(self):
        if not self.metadata:
            self.metadata = {}
        self.metadata.update({
            'name': self.name,
            'role': self.role,
            'tenant_id': self.tenant_id,
            'experiment_group': self.experiment_group
        })

@dataclass
class UserLoggedInEvent(AuthEvent):
    """User login event"""
    event_type: AuthEventType = AuthEventType.USER_LOGGED_IN
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    login_method: Optional[str] = None  # 'password', 'token', etc.
    
    def __post_init__(self):
        if not self.metadata:
            self.metadata = {}
        self.metadata.update({
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'login_method': self.login_method
        })

@dataclass
class TokenRefreshedEvent(AuthEvent):
    """Token refresh event"""
    event_type: AuthEventType = AuthEventType.TOKEN_REFRESHED
    token_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.metadata:
            self.metadata = {}
        self.metadata.update({
            'token_id': self.token_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        })

@dataclass
class UserProfileUpdatedEvent(AuthEvent):
    """User profile update event"""
    event_type: AuthEventType = AuthEventType.USER_PROFILE_UPDATED
    updated_fields: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.metadata:
            self.metadata = {}
        self.metadata.update({
            'updated_fields': self.updated_fields or {}
        })

class AuthEventProducer:
    """Kafka producer for auth events using existing HCIE infrastructure"""
    
    def __init__(self, kafka_producer=None):
        """Initialize with optional kafka producer injection"""
        # Use injected producer or get from messaging
        if kafka_producer:
            self.producer = kafka_producer
        else:
            try:
                from messaging import get_kafka_producer
                self.producer = get_kafka_producer()
            except ImportError:
                logger.warning("⚠️ HCIE messaging not available - auth events disabled")
                self.producer = None
        
        # Load event schemas
        try:
            from messaging.schema.events import (
                UserRegisteredEvent, UserLoggedInEvent, TokenRefreshedEvent,
                UserProfileUpdatedEvent, UserLoggedOutEvent, PasswordChangedEvent
            )
            self.UserRegisteredEvent = UserRegisteredEvent
            self.UserLoggedInEvent = UserLoggedInEvent
            self.TokenRefreshedEvent = TokenRefreshedEvent
            self.UserProfileUpdatedEvent = UserProfileUpdatedEvent
            self.UserLoggedOutEvent = UserLoggedOutEvent
            self.PasswordChangedEvent = PasswordChangedEvent
        except ImportError:
            logger.warning("⚠️ HCIE event schemas not available")
            self.UserRegisteredEvent = None
            self.UserLoggedInEvent = None
            self.TokenRefreshedEvent = None
            self.UserProfileUpdatedEvent = None
            self.UserLoggedOutEvent = None
            self.PasswordChangedEvent = None
    
    def emit_event(self, event):
        """Emit auth event to Kafka using HCIE event system"""
        if not self.producer:
            logger.warning("⚠️ Kafka producer not available - auth event not emitted")
            return
        
        try:
            # Send using existing producer
            success = self.producer.publish_event(event)
            
            if success:
                logger.info(f"📡 Auth event emitted: {event.event_type.value} for user {event.user_id}")
            else:
                logger.warning(f"⚠️ Failed to emit auth event: {event.event_type.value}")
            
        except Exception as e:
            logger.error(f"❌ Failed to emit auth event: {e}")
            # Don't fail the request - events are fire-and-forget
    
    def user_registered(self, user_id: str, email: str, name: str = None, role: str = None, 
                      tenant_id: str = None, experiment_group: str = None):
        """Emit user registration event"""
        if not self.UserRegisteredEvent:
            return
        
        event = self.UserRegisteredEvent(
            event_id=str(uuid.uuid4()),
            event_type=self.UserRegisteredEvent.event_type,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            email=email,
            name=name,
            role=role,
            tenant_id=tenant_id,
            experiment_group=experiment_group,
            source="auth_service"
        )
        self.emit_event(event)
    
    def user_logged_in(self, user_id: str, email: str, ip_address: str = None, 
                      user_agent: str = None, login_method: str = "password"):
        """Emit user login event"""
        if not self.UserLoggedInEvent:
            return
        
        event = self.UserLoggedInEvent(
            event_id=str(uuid.uuid4()),
            event_type=self.UserLoggedInEvent.event_type,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            login_method=login_method,
            source="auth_service"
        )
        self.emit_event(event)
    
    def token_refreshed(self, user_id: str, email: str, token_id: str = None, 
                       expires_at: datetime = None):
        """Emit token refresh event"""
        if not self.TokenRefreshedEvent:
            return
        
        event = self.TokenRefreshedEvent(
            event_id=str(uuid.uuid4()),
            event_type=self.TokenRefreshedEvent.event_type,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            email=email,
            token_id=token_id,
            expires_at=expires_at,
            source="auth_service"
        )
        self.emit_event(event)
    
    def user_profile_updated(self, user_id: str, email: str, updated_fields: Dict[str, Any]):
        """Emit user profile update event"""
        if not self.UserProfileUpdatedEvent:
            return
        
        event = self.UserProfileUpdatedEvent(
            event_id=str(uuid.uuid4()),
            event_type=self.UserProfileUpdatedEvent.event_type,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            email=email,
            updated_fields=updated_fields,
            source="auth_service"
        )
        self.emit_event(event)
