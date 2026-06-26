"""
Projection WebSocket - B4.1 Frontend Semantic Runtime MVP

Streams ProjectionUpdated events to frontend (semantic projection terminal)

ARCHITECTURAL CONSTRAINTS:
- Frontend consumes ONLY ProjectionUpdated events via WebSocket
- Does NOT stream raw cognition or adaptation separately
- Validates event_type = "ProjectionUpdated" only (security constraint)
- Frontend is a semantic materialized-view renderer only
"""

import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)

class ProjectionConnectionManager:
    """Manage WebSocket connections for ProjectionUpdated events"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and track user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"🔌 Projection WebSocket connected: user={user_id}, total_connections={len(self.active_connections[user_id])}")
        
        # Send initial projection data
        await self.send_initial_projection(websocket, user_id)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"🔌 Projection WebSocket disconnected: user={user_id}")
    
    async def send_initial_projection(self, websocket: WebSocket, user_id: str):
        """Send initial projection data to newly connected client"""
        try:
            # For MVP, send a simple connection message
            # Full projection data will come via ProjectionUpdated events
            initial_message = {
                "type": "initial_projection",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to projection stream. Waiting for ProjectionUpdated events..."
            }
            
            await websocket.send_text(json.dumps(initial_message))
            logger.info(f"📨 Sent initial projection message to {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending initial projection: {e}")
    
    async def broadcast_projection_update(self, user_id: str, projection_event: Dict):
        """
        Broadcast ProjectionUpdated event to user's connections
        
        SECURITY CONSTRAINT: Only broadcasts ProjectionUpdated events
        """
        # Validate event type (security constraint)
        if projection_event.get("event_type") != "ProjectionUpdated":
            logger.warning(f"⚠️  Ignoring non-ProjectionUpdated event: {projection_event.get('event_type')}")
            return
        
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(projection_event))
                    logger.debug(f"📊 Sent ProjectionUpdated to {user_id}: {projection_event.get('event_id')}")
                except Exception as e:
                    logger.warning(f"❌ Failed to send to connection: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.disconnect(conn, user_id)

# Global projection connection manager
projection_manager = ProjectionConnectionManager()

async def projection_websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    Main WebSocket endpoint for ProjectionUpdated events
    
    Connect to: ws://localhost:8000/ws/projections/{user_id}
    
    Messages received:
    - {"type": "ping"} - Keep connection alive
    
    Messages sent:
    - Initial connection message
    - ProjectionUpdated events (cognition + adaptation enrichment)
    """
    await projection_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    # Respond to ping
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
            except json.JSONDecodeError:
                logger.warning(f"❌ Invalid JSON from WebSocket: {data}")
                continue
                
    except WebSocketDisconnect:
        projection_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"❌ Projection WebSocket error: {e}")
        projection_manager.disconnect(websocket, user_id)

# Helper function for broadcasting from projection_consumer
async def broadcast_projection_updated(user_id: str, projection_event: Dict):
    """
    Broadcast ProjectionUpdated event (call from projection_consumer)
    
    This function is called by projection_consumer.py when it emits
    a ProjectionUpdated event via the outbox.
    """
    await projection_manager.broadcast_projection_update(user_id, projection_event)
