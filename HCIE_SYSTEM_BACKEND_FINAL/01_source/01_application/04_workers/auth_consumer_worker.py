#!/usr/bin/env python3
"""
Auth Consumer Worker - Separate process for auth event consumption
Decoupled from API service for better resource isolation
"""

import os
import sys
import logging
import signal
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging import HCIEKafkaConsumer
from app.domains.user.service import UserService
from app.domains.experiment.service import ExperimentService
from storage.redis_store.redis_store import RedisFeatureStore
from config.env import settings

logger = logging.getLogger(__name__)

class AuthConsumerWorkerService:
    """Auth consumer worker service running in separate process"""
    
    def __init__(self):
        self.running = False
        self.consumer = None
        self.user_service = None
        self.experiment_service = None
        self.redis_client = None
        self.health_check_interval = 30  # seconds
        self.last_health_check = None
        
    def initialize(self):
        """Initialize auth consumer worker with dependencies"""
        try:
            logger.info("🔄 Initializing auth consumer worker...")
            
            # Create Redis client
            self.redis_client = RedisFeatureStore(settings)
            
            # Create Kafka consumer via factory (proper DI)
            from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
            
            kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
            self.consumer = kafka_factory.create_consumer(group_id="auth-event-consumer")
            
            # Subscribe to auth topics via consumer (standard pattern)
            auth_topics = ["hcie.auth.user_registered", "hcie.auth.user_logged_in", 
                          "hcie.auth.token_refreshed", "hcie.auth.user_profile_updated",
                          "hcie.auth.user_logged_out", "hcie.auth.password_changed"]
            
            self.consumer.subscribe(auth_topics)
            
            logger.info(f"✅ Subscribed to auth topics: {auth_topics}")
            
            # Create services
            from storage.postgres_store.interaction_store import PostgresInteractionStore
            postgres_store = PostgresInteractionStore()
            from app.repositories.user_repository import UserRepository
            user_repo = UserRepository(postgres_store)
            
            self.user_service = UserService(user_repo=user_repo)
            self.experiment_service = ExperimentService(experiment_repo=None, user_repo=user_repo)
            
            # Register event handlers
            self._register_event_handlers()
            
            logger.info("✅ Auth consumer worker initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize auth consumer worker: {e}")
            return False
    
    def _register_event_handlers(self):
        """Register event handlers for auth events"""
        from messaging.schema.events import (
            UserRegisteredEvent, UserLoggedInEvent, TokenRefreshedEvent,
            UserProfileUpdatedEvent, UserLoggedOutEvent, PasswordChangedEvent
        )
        
        # User registration handler
        self.consumer.register_handler("user_registered", self._handle_user_registered)
        
        # User login handler
        self.consumer.register_handler("user_logged_in", self._handle_user_logged_in)
        
        # Token refresh handler
        self.consumer.register_handler("token_refreshed", self._handle_token_refreshed)
        
        # Profile update handler
        self.consumer.register_handler("user_profile_updated", self._handle_user_profile_updated)
        
        # Logout handler
        self.consumer.register_handler("user_logged_out", self._handle_user_logged_out)
        
        # Password change handler
        self.consumer.register_handler("password_changed", self._handle_password_changed)
        
        logger.info("✅ Auth event handlers registered")
    
    def _handle_user_registered(self, event_data):
        """Handle user registration event with idempotency protection"""
        try:
            event_id = event_data.get('event_id')
            user_id = event_data.get('user_id')
            
            # ✅ Idempotency check - skip if already processed
            if self._is_event_processed(event_id):
                logger.info(f"⏭️ Skipping already processed event: {event_id}")
                return
            
            logger.info(f"👤 Processing user registration: {user_id}")
            
            if self.user_service:
                # Process user registration logic
                # TODO: Add actual business logic here
                pass
            
            # ✅ Mark event as processed
            self._mark_event_processed(event_id)
            
        except Exception as e:
            logger.error(f"❌ Failed to handle user registration: {e}")
    
    def _is_event_processed(self, event_id: str) -> bool:
        """Check if event has been processed (idempotency)"""
        try:
            if not self.redis_client:
                return False
            
            # Use Redis set for processed event IDs with TTL
            key = f"processed_events:{event_id}"
            exists = self.redis_client.redis_client.exists(key)
            
            if exists:
                logger.info(f"⏭️ Event {event_id} already processed - skipping")
            return exists
        except Exception as e:
            logger.warning(f"⚠️ Failed to check event processing status: {e}")
            return False
    
    def _mark_event_processed(self, event_id: str):
        """Mark event as processed (idempotency)"""
        try:
            if not self.redis_client:
                return
            
            # Store in Redis with expiration (7 days)
            key = f"processed_events:{event_id}"
            self.redis_client.redis_client.setex(key, 7 * 24 * 3600, "1")
            logger.debug(f"📝 Marked event {event_id} as processed")
        except Exception as e:
            logger.warning(f"⚠️ Failed to mark event as processed: {e}")
    
    def _get_processed_events_count(self) -> int:
        """Get count of processed events (for monitoring)"""
        try:
            if not self.redis_client:
                return 0
            
            # Count keys with processed_events prefix
            pattern = "processed_events:*"
            keys = self.redis_client.redis_client.keys(pattern)
            return len(keys)
        except Exception as e:
            logger.warning(f"⚠️ Failed to count processed events: {e}")
            return 0
    
    def _handle_user_logged_in(self, event_data):
        """Handle user login event"""
        try:
            logger.info(f"🔐 Processing user login: {event_data.get('user_id')}")
            
            if self.user_service:
                # Process login logic
                pass  # Add business logic here
            
        except Exception as e:
            logger.error(f"❌ Failed to handle user login: {e}")
    
    def _handle_token_refreshed(self, event_data):
        """Handle token refresh event"""
        try:
            logger.info(f"🔄 Processing token refresh: {event_data.get('user_id')}")
            
            # Process token refresh logic
            pass  # Add business logic here
            
        except Exception as e:
            logger.error(f"❌ Failed to handle token refresh: {e}")
    
    def _handle_user_profile_updated(self, event_data):
        """Handle user profile update event"""
        try:
            logger.info(f"👤 Processing profile update: {event_data.get('user_id')}")
            
            if self.user_service:
                # Process profile update logic
                pass  # Add business logic here
            
        except Exception as e:
            logger.error(f"❌ Failed to handle profile update: {e}")
    
    def _handle_user_logged_out(self, event_data):
        """Handle user logout event"""
        try:
            logger.info(f"👋 Processing user logout: {event_data.get('user_id')}")
            
            # Process logout logic
            pass  # Add business logic here
            
        except Exception as e:
            logger.error(f"❌ Failed to handle user logout: {e}")
    
    def _handle_password_changed(self, event_data):
        """Handle password change event"""
        try:
            logger.info(f"🔒 Processing password change: {event_data.get('user_id')}")
            
            # Process password change logic
            pass  # Add business logic here
            
        except Exception as e:
            logger.error(f"❌ Failed to handle password change: {e}")
    
    def start(self):
        """Start the auth consumer worker"""
        if not self.initialize():
            logger.error("❌ Failed to initialize - exiting")
            return False
        
        self.running = True
        logger.info("🚀 Starting auth consumer worker...")
        
        # Start consuming messages
        try:
            self.consumer.start_consuming()
            logger.info("✅ Auth consumer started successfully")
            
            # Health check loop
            self.health_check_loop()
            
        except Exception as e:
            logger.error(f"❌ Failed to start consumer: {e}")
            return False
        
        return True
    
    def health_check_loop(self):
        """Periodic health checks"""
        while self.running:
            try:
                self.last_health_check = time.time()
                
                # Check consumer health
                consumer_healthy = self.consumer and self.consumer.is_running()
                
                # Check Redis health
                redis_healthy = self.redis_client and self.redis_client.redis_available
                
                # Log health metrics
                logger.info(f"📊 Health check - Consumer: {consumer_healthy}, Redis: {redis_healthy}")
                
                # Restart if unhealthy
                if not consumer_healthy or not redis_healthy:
                    logger.warning("⚠️ Auth consumer unhealthy - attempting restart")
                    self.restart_consumer()
                
                # Sleep until next health check
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"❌ Health check failed: {e}")
                time.sleep(self.health_check_interval)
    
    def restart_consumer(self):
        """Restart the consumer"""
        try:
            logger.info("🔄 Restarting auth consumer...")
            
            # Stop current consumer
            if self.consumer:
                self.consumer.stop()
            
            # Wait a moment before restart
            time.sleep(2)
            
            # Re-initialize
            if self.initialize():
                self.consumer.start_consuming()
                logger.info("✅ Auth consumer restarted successfully")
            else:
                logger.error("❌ Failed to restart consumer")
            
        except Exception as e:
            logger.error(f"❌ Failed to restart consumer: {e}")
    
    def stop(self):
        """Stop the auth consumer worker"""
        logger.info("🛑 Stopping auth consumer worker...")
        self.running = False
        
        if self.consumer:
            self.consumer.stop()
        
        logger.info("✅ Auth consumer worker stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"📡 Received signal {signum} - shutting down...")
    worker.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=getattr(settings, 'log_level', 'INFO'),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and start worker
    worker = AuthConsumerWorkerService()
    
    try:
        success = worker.start()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt - shutting down...")
        worker.stop()
    except Exception as e:
        logger.error(f"❌ Worker crashed: {e}")
        worker.stop()
        sys.exit(1)
