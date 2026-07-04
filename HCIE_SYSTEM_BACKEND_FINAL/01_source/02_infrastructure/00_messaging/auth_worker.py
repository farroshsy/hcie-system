"""
Kafka Auth Event Worker
Consumes auth events and handles downstream processing
"""

import logging
import time
import threading
from typing import Optional, Set
from concurrent.futures import ThreadPoolExecutor

from .consumer.kafka_consumer import HCIEKafkaConsumer
from messaging.schema.events import (
    UserRegisteredEvent, UserLoggedInEvent, TokenRefreshedEvent,
    UserProfileUpdatedEvent, UserLoggedOutEvent, PasswordChangedEvent,
    EventType
)

logger = logging.getLogger(__name__)

# Import Redis for idempotency tracking
try:
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("⚠️ Redis not available - idempotency tracking disabled")

# Import services
try:
    from app.domains.user.service import UserService
    from app.domains.experiment.service import ExperimentService
except ImportError:
    logger.warning("⚠️ Domain services not available")
    UserService = None
    ExperimentService = None

# ❌ REMOVED: HCIEKafkaConsumer import - worker should not know about Kafka implementation

logger = logging.getLogger(__name__)

class AuthEventWorker:
    """Kafka worker for auth event processing with explicit DI - NO config leakage"""
    
    def __init__(self, user_service=None, experiment_service=None, redis_client=None, kafka_consumer=None):
        self.consumer = kafka_consumer  # ✅ Injected, not created
        self.running = False
        self.thread = None
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="auth-events")
        
        # Explicit dependency injection
        self.user_service = user_service
        self.experiment_service = experiment_service
        
        # Idempotency tracking - inject Redis client, don't create it
        self.processed_events: Set[str] = set()
        self.redis_client = redis_client
        if self.redis_client:
            logger.info("✅ Redis client injected for idempotency")
        else:
            logger.warning("⚠️ No Redis client provided - using in-memory idempotency")
        
        if self.consumer:
            logger.info("✅ Kafka consumer injected")
        else:
            logger.warning("⚠️ No Kafka consumer provided")
    
    # ❌ REMOVED: _init_idempotency_store() - Redis client injected from DI
    
    def _mark_event_processed_atomic(self, event_id: str, ttl: int = 86400) -> bool:
        """Atomically check and mark event as processed (race-condition safe)"""
        if self.redis_client:
            try:
                key = f"processed_event:{event_id}"
                # Atomic SET NX EX - returns True if set, False if already exists
                was_set = self.redis_client.set(key, "1", nx=True, ex=ttl)
                if was_set:
                    logger.debug(f"✅ Marked event as processed: {event_id}")
                else:
                    logger.debug(f"⚠️ Event already processed: {event_id}")
                return was_set
            except Exception as e:
                logger.warning(f"⚠️ Redis atomic idempotency failed: {e}")
                # Fallback to memory (not atomic, but best effort)
                if event_id in self.processed_events:
                    return False
                self.processed_events.add(event_id)
                return True
        else:
            # Fallback to memory (not atomic)
            if event_id in self.processed_events:
                return False
            self.processed_events.add(event_id)
            return True
        
    def start(self):
        """Start the auth event worker"""
        if self.running:
            logger.warning("Auth event worker already running")
            return
        
        if not self.consumer:
            raise RuntimeError("❌ Kafka consumer not provided - cannot start worker")
        
        try:
            # Register event handlers
            self._register_event_handlers()
            
            self.running = True
            self.thread = threading.Thread(target=self._run_worker, daemon=True)
            self.thread.start()
            logger.info("🔥 Auth event worker started (consumer injected)")
        except Exception as e:
            logger.error(f"❌ Failed to start auth event worker: {e}")
    
    def _register_event_handlers(self):
        """Register event handlers for auth events"""
        # User registration handler
        self.consumer.register_handler(EventType.USER_REGISTERED, self._handle_user_registered)
        
        # User login handler
        self.consumer.register_handler(EventType.USER_LOGGED_IN, self._handle_user_logged_in)
        
        # Token refresh handler
        self.consumer.register_handler(EventType.TOKEN_REFRESHED, self._handle_token_refreshed)
        
        # Profile update handler
        self.consumer.register_handler(EventType.USER_PROFILE_UPDATED, self._handle_profile_updated)
        
        # User logout handler
        self.consumer.register_handler(EventType.USER_LOGGED_OUT, self._handle_user_logged_out)
        
        # Password change handler
        self.consumer.register_handler(EventType.PASSWORD_CHANGED, self._handle_password_changed)
        
        logger.info("📝 Auth event handlers registered")
    
    def _handle_user_registered(self, event: UserRegisteredEvent):
        """Handle user registration event with correct idempotency order"""
        # Check if already processed (no marking yet)
        if self._is_event_processed(event.event_id):
            logger.debug(f"⚠️ Event {event.event_id} already processed, skipping")
            return
        
        try:
            logger.info(f"👤 Processing user registration: {event.email}")
            
            # ❌ REMOVED: Direct cross-domain call - violates ownership rules
            # This should be handled by Experiment Service consuming the event
            # if self.experiment_service and event.tenant_id:
            #     assignment = self.experiment_service.assign_user_to_experiment(...)
            
            # Send welcome email (placeholder for email service)
            self._send_welcome_email(event)
            
            # Track registration analytics
            self._track_registration_analytics(event)
            
            # ✅ Mark as processed ONLY AFTER successful processing
            self._mark_event_processed(event.event_id)
            logger.info(f"✅ Processed registration event: {event.event_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling user registration: {e}")
            # Don't mark as processed - allow retry
    
    def _handle_user_logged_in(self, event: UserLoggedInEvent):
        """Handle user login event with correct idempotency order"""
        # Check if already processed (no marking yet)
        if self._is_event_processed(event.event_id):
            logger.debug(f"⚠️ Event {event.event_id} already processed, skipping")
            return
        
        try:
            logger.info(f"🔐 Processing user login: {event.email}")
            
            # Track login analytics
            self._track_login_analytics(event)
            
            # Update user last active (already done in auth service)
            
            # Check for suspicious activity (placeholder)
            self._check_login_anomaly(event)
            
            # ✅ Mark as processed ONLY AFTER successful processing
            self._mark_event_processed(event.event_id)
            logger.info(f"✅ Processed login event: {event.event_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling user login: {e}")
            # Don't mark as processed - allow retry
    
    def _handle_token_refreshed(self, event: TokenRefreshedEvent):
        """Handle token refresh event with correct idempotency order"""
        # Check if already processed (no marking yet)
        if self._is_event_processed(event.event_id):
            logger.debug(f"⚠️ Event {event.event_id} already processed, skipping")
            return
        
        try:
            logger.info(f"🔄 Processing token refresh: {event.email}")
            
            # Track token usage analytics
            self._track_token_analytics(event)
            
            # ✅ Mark as processed ONLY AFTER successful processing
            self._mark_event_processed(event.event_id)
            logger.info(f"✅ Processed token refresh event: {event.event_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling token refresh: {e}")
            # Don't mark as processed - allow retry
    
    def _handle_profile_updated(self, event: UserProfileUpdatedEvent):
        """Handle user profile update event with correct idempotency order"""
        # Check if already processed (no marking yet)
        if self._is_event_processed(event.event_id):
            logger.debug(f"⚠️ Event {event.event_id} already processed, skipping")
            return
        
        try:
            logger.info(f"✏️ Processing profile update: {event.email}")
            
            # Invalidate user cache
            if self.user_service:
                self.user_service.cache_manager.invalidate_user_profile(event.user_id)
            
            # Track profile update analytics
            self._track_profile_analytics(event)
            
            # ✅ Mark as processed ONLY AFTER successful processing
            self._mark_event_processed(event.event_id)
            logger.info(f"✅ Processed profile update event: {event.event_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling profile update: {e}")
            # Don't mark as processed - allow retry
    
    def _handle_user_logged_out(self, event: UserLoggedOutEvent):
        """Handle user logout event with correct idempotency order"""
        # Check if already processed (no marking yet)
        if self._is_event_processed(event.event_id):
            logger.debug(f"⚠️ Event {event.event_id} already processed, skipping")
            return
        
        try:
            logger.info(f"🚪 Processing user logout: {event.email}")
            
            # Track session analytics
            self._track_session_analytics(event)
            
            # ✅ Mark as processed ONLY AFTER successful processing
            self._mark_event_processed(event.event_id)
            logger.info(f"✅ Processed logout event: {event.event_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling user logout: {e}")
            # Don't mark as processed - allow retry
    
    def _handle_password_changed(self, event: PasswordChangedEvent):
        """Handle password change event with correct idempotency order"""
        # Check if already processed (no marking yet)
        if self._is_event_processed(event.event_id):
            logger.debug(f"⚠️ Event {event.event_id} already processed, skipping")
            return
        
        try:
            logger.info(f"🔒 Processing password change: {event.email}")
            
            # Invalidate all user sessions/tokens
            self._invalidate_user_sessions(event.user_id)
            
            # Send security notification
            self._send_security_notification(event)
            
            # ✅ Mark as processed ONLY AFTER successful processing
            self._mark_event_processed(event.event_id)
            logger.info(f"✅ Processed password change event: {event.event_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling password change: {e}")
            # Don't mark as processed - allow retry
    
    def _send_welcome_email(self, event: UserRegisteredEvent):
        """Send welcome email to new user"""
        # Placeholder for email service integration
        logger.info(f"📧 Welcome email queued for: {event.email}")
    
    def _track_registration_analytics(self, event: UserRegisteredEvent):
        """Track registration analytics"""
        # Placeholder for analytics service
        logger.info(f"📊 Registration tracked: {event.email} ({event.role})")
    
    def _track_login_analytics(self, event: UserLoggedInEvent):
        """Track login analytics"""
        # Placeholder for analytics service
        logger.info(f"📊 Login tracked: {event.email} ({event.login_method})")
    
    def _track_token_analytics(self, event: TokenRefreshedEvent):
        """Track token analytics"""
        # Placeholder for analytics service
        logger.info(f"📊 Token refresh tracked: {event.email}")
    
    def _track_profile_analytics(self, event: UserProfileUpdatedEvent):
        """Track profile update analytics"""
        # Placeholder for analytics service
        logger.info(f"📊 Profile update tracked: {event.email} - {list(event.updated_fields.keys())}")
    
    def _track_session_analytics(self, event: UserLoggedOutEvent):
        """Track session analytics"""
        # Placeholder for analytics service
        logger.info(f"📊 Session tracked: {event.email} ({event.session_duration}s)")
    
    def _check_login_anomaly(self, event: UserLoggedInEvent):
        """Check for login anomalies"""
        # Placeholder for anomaly detection
        if event.ip_address:
            logger.info(f"🔍 Login anomaly check: {event.email} from {event.ip_address}")
    
    def _invalidate_user_sessions(self, user_id: str):
        """Invalidate all user sessions"""
        # Placeholder for session invalidation
        logger.info(f"🚫 Sessions invalidated for user: {user_id}")
    
    def _send_security_notification(self, event: PasswordChangedEvent):
        """Send security notification"""
        # Placeholder for security notification
        logger.info(f"🔔 Security notification sent: {event.email}")
    
    def _run_worker(self):
        """Main worker loop"""
        logger.info("🔄 Auth event worker loop started")
        
        while self.running:
            try:
                # Process events with timeout
                self.consumer.consume_messages(timeout_ms=1000)
                time.sleep(0.1)  # Small delay to prevent busy loop
                
            except Exception as e:
                logger.error(f"❌ Error in auth event worker loop: {e}")
                time.sleep(1)  # Back off on error
        
        logger.info("🛑 Auth event worker loop stopped")
    
    def stop(self):
        """Stop the auth event worker"""
        if not self.running:
            return
        
        logger.info("🛑 Stopping auth event worker...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        if self.consumer:
            self.consumer.close()
        
        self.executor.shutdown(wait=True)
        logger.info("✅ Auth event worker stopped")

# Global worker instance
_auth_worker_instance: Optional[AuthEventWorker] = None

def create_auth_event_worker(user_service=None, experiment_service=None, redis_client=None, kafka_consumer=None) -> AuthEventWorker:
    """Create auth event worker with explicit dependency injection"""
    return AuthEventWorker(
        user_service=user_service, 
        experiment_service=experiment_service,
        redis_client=redis_client,
        kafka_consumer=kafka_consumer
    )

def get_auth_event_worker() -> AuthEventWorker:
    """Get singleton auth event worker (legacy - use create_auth_event_worker instead)"""
    global _auth_worker_instance
    if _auth_worker_instance is None:
        _auth_worker_instance = AuthEventWorker()
    return _auth_worker_instance

def start_auth_event_worker(user_service=None, experiment_service=None, redis_client=None, kafka_consumer=None):
    """Start the auth event worker with dependencies"""
    worker = create_auth_event_worker(user_service, experiment_service, redis_client, kafka_consumer)
    worker.start()
    return worker

def stop_auth_event_worker():
    """Stop the auth event worker"""
    global _auth_worker_instance
    if _auth_worker_instance:
        _auth_worker_instance.stop()
        _auth_worker_instance = None
