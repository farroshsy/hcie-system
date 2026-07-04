#!/usr/bin/env python3
"""
Outbox Worker - Separate process for outbox event processing
Decoupled from API service for better resource isolation
"""

import os
import sys
import logging
import signal
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
from app.infrastructure.messaging.event_bus import KafkaEventBus
from app.infrastructure.kafka.kafka_factory import DefaultKafkaProducerFactory
from app.infrastructure.kafka.kafka_factory import KafkaFactory
from config.env import settings

logger = logging.getLogger(__name__)

class OutboxWorkerService:
    """Outbox worker service running in separate process"""
    
    def __init__(self):
        self.running = False
        self.outbox_pattern = None
        self.health_check_interval = 30  # seconds
        self.last_health_check = None
        
    def initialize(self):
        """Initialize outbox worker with dependencies"""
        try:
            logger.info("🔄 Initializing outbox worker...")
            
            # Create Kafka factory
            kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
            kafka_producer = kafka_factory.create_producer()
            
            # Create event bus
            event_bus = KafkaEventBus(kafka_producer)
            
            # Create outbox pattern (will use existing singleton or create new)
            from storage.postgres_store.interaction_store import PostgresInteractionStore
            postgres_store = PostgresInteractionStore()
            
            self.outbox_pattern = get_outbox_pattern(postgres_store, event_bus=event_bus)
            
            logger.info("✅ Outbox worker initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize outbox worker: {e}")
            return False
    
    def start(self):
        """Start the outbox worker"""
        if not self.initialize():
            logger.error("❌ Failed to initialize - exiting")
            return False
        
        self.running = True
        logger.info("🚀 Starting outbox worker...")
        
        # Start background processor
        self.outbox_pattern.start_background_processor(
            interval_seconds=getattr(settings, 'outbox_poll_interval', 5),
            worker_id=f"outbox-worker-{os.getpid()}"
        )
        
        # Health check loop
        self.health_check_loop()
        
        return True
    
    def health_check_loop(self):
        """Periodic health checks"""
        while self.running:
            try:
                self.last_health_check = time.time()
                
                # Check outbox health
                health = self.outbox_pattern.get_health_status()
                
                # Log health metrics
                logger.info(f"📊 Health check - Running: {health['running']}, "
                           f"Processed: {health['processed_count']}, "
                           f"Errors: {health['error_count']}, "
                           f"Thread: {health['thread_alive']}")
                
                # Check if outbox is healthy
                if not health['running'] or not health['thread_alive']:
                    logger.warning("⚠️ Outbox worker unhealthy - attempting restart")
                    self.restart_processor()
                
                # ✅ Check EventBus health
                if not self.outbox_pattern.event_bus.is_healthy():
                    logger.warning("⚠️ EventBus unhealthy - attempting restart")
                    self.restart_processor()
                
                # Sleep until next health check
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"❌ Health check failed: {e}")
                time.sleep(self.health_check_interval)
    
    def restart_processor(self):
        """Restart the outbox processor"""
        try:
            logger.info("🔄 Restarting outbox processor...")
            
            # Stop current processor
            self.outbox_pattern.stop_background_processor()
            
            # Wait a moment before restart
            time.sleep(2)
            
            # Start new processor
            self.outbox_pattern.start_background_processor(
                interval_seconds=getattr(settings, 'outbox_poll_interval', 5),
                worker_id=f"outbox-worker-{os.getpid()}"
            )
            
            logger.info("✅ Outbox processor restarted successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to restart processor: {e}")
    
    def stop(self):
        """Stop the outbox worker"""
        logger.info("🛑 Stopping outbox worker...")
        self.running = False
        
        if self.outbox_pattern:
            self.outbox_pattern.stop_background_processor()
        
        logger.info("✅ Outbox worker stopped")

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
    worker = OutboxWorkerService()
    
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
