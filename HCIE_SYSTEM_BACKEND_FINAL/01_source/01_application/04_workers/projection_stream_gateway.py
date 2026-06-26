"""
B4.1.1 - Projection Stream Gateway

Consumes ProjectionUpdated events from Kafka and broadcasts to WebSocket clients.

Canonical Event Topology:
ProjectionConsumer → Outbox → Kafka → Projection Stream Gateway → WebSocket Clients

ARCHITECTURAL CONSTRAINTS:
- WebSocket streaming derives from canonical event topology, NOT process memory adjacency
- Eliminates semantic bifurcation risk from direct asyncio.create_task broadcast
- Enables replay, CDC reconstruction, DLQ replay, and multi-instance scaling
- Consumer reads ONLY from Kafka "projections" topic
- Broadcasts ONLY ProjectionUpdated events (security constraint)
"""

import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ProjectionStreamGateway:
    """
    Projection Stream Gateway Consumer
    
    Consumes ProjectionUpdated events from Kafka "projections" topic
    and broadcasts to WebSocket clients via projection_manager.
    
    This replaces direct asyncio.create_task broadcast in projection_consumer
    with canonical event topology for replay safety and multi-instance scaling.
    """
    
    def __init__(self):
        self.running = False
        self.consumer = None
        self.processed_count = 0
        self.error_count = 0
        self.projection_manager = None
        
    def initialize(self) -> bool:
        """Initialize Kafka consumer and WebSocket connection manager"""
        try:
            from messaging.consumer.kafka_consumer import HCIEKafkaConsumer
            from app.api.websocket.projection_websocket import projection_manager
            
            self.projection_manager = projection_manager
            
            # Create consumer for "projections" topic
            bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            group_id = "projection-stream-gateway"
            
            self.consumer = HCIEKafkaConsumer(
                bootstrap_servers=bootstrap_servers,
                topic_prefix="",  # No prefix for "projections" topic
                group_id=group_id,
                auto_offset_reset="latest"
            )
            
            # Manually subscribe to "projections" topic
            self.consumer.consumer.subscribe(["projections"])
            
            logger.info("✅ Projection Stream Gateway initialized")
            logger.info(f"   Kafka: {bootstrap_servers}")
            logger.info(f"   Group: {group_id}")
            logger.info("   Topic: projections")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Projection Stream Gateway: {e}")
            return False
    
    async def broadcast_to_websocket(self, user_id: str, projection_event: Dict):
        """
        Broadcast ProjectionUpdated event to WebSocket clients
        
        This is the canonical WebSocket delivery path.
        """
        try:
            if self.projection_manager:
                await self.projection_manager.broadcast_projection_update(user_id, projection_event)
                logger.debug(f"🔌 Gateway broadcasted to WebSocket: user={user_id}, event={projection_event.get('event_id')}")
        except Exception as e:
            logger.error(f"❌ Failed to broadcast to WebSocket: {e}")
    
    def process_projection_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process ProjectionUpdated event from Kafka and broadcast to WebSocket
        
        Returns True if successful, False otherwise
        """
        try:
            # Extract event data
            event_id = event_data.get("event_id")
            event_type = event_data.get("event_type")
            user_id = event_data.get("user_id")
            
            # Validate event type (security constraint)
            if event_type != "ProjectionUpdated":
                logger.warning(f"⚠️  Gateway ignoring non-ProjectionUpdated event: {event_type}")
                return False
            
            if not user_id:
                logger.warning(f"⚠️  Gateway event missing user_id: {event_id}")
                return False
            
            # Broadcast to WebSocket (async in event loop)
            asyncio.create_task(self.broadcast_to_websocket(user_id, event_data))
            
            self.processed_count += 1
            logger.info(f"📊 Gateway processed ProjectionUpdated: {event_id} for user={user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Gateway failed to process event: {e}")
            self.error_count += 1
            return False
    
    async def _run_loop(self):
        """Async inner loop — runs inside asyncio.run() so create_task works."""
        self.running = True
        logger.info("🚀 Starting Projection Stream Gateway loop...")
        try:
            while self.running:
                # poll() is blocking; run in executor to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                message_batch = await loop.run_in_executor(
                    None, lambda: self.consumer.poll(timeout_ms=1000)
                )

                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            if isinstance(message.value, dict):
                                event_data = message.value
                            elif isinstance(message.value, bytes):
                                event_data = json.loads(message.value.decode('utf-8'))
                            else:
                                event_data = json.loads(str(message.value))

                            self.process_projection_event(event_data)

                        except json.JSONDecodeError as e:
                            logger.error(f"❌ Gateway JSON decode error: {e}")
                            self.error_count += 1
                        except Exception as e:
                            logger.error(f"❌ Gateway message processing error: {e}")
                            self.error_count += 1

                if self.processed_count > 0 and self.processed_count % 100 == 0:
                    logger.info(f"📊 Gateway stats: processed={self.processed_count}, errors={self.error_count}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"❌ Gateway loop error: {e}")
        finally:
            self.running = False
            if self.consumer:
                self.consumer.close()
            logger.info("🛑 Projection Stream Gateway stopped")

    def run(self):
        """Main consumer loop"""
        if not self.initialize():
            logger.error("❌ Failed to initialize, exiting")
            return
        asyncio.run(self._run_loop())
    
    def stop(self):
        """Stop the gateway"""
        self.running = False
        logger.info("⏹️  Stopping Projection Stream Gateway...")


def main():
    """Entry point for running the Projection Stream Gateway"""
    import logging as _logging
    _logging.basicConfig(
        level=_logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    gateway = ProjectionStreamGateway()
    gateway.run()


if __name__ == "__main__":
    main()
