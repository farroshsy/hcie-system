"""
Real-time WebSocket endpoints for learning updates

Provides live updates to frontend when learning events are processed.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import json
import logging
import asyncio

from app.api.dependencies import get_current_user_websocket

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/realtime", tags=["realtime"])

# Connection manager for WebSocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"🔗 WebSocket connected for user: {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"🔌 WebSocket disconnected for user: {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user's WebSocket connections"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.active_connections[user_id].discard(conn)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected clients"""
        for user_id, connections in self.active_connections.items():
            for connection in connections.copy():
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    self.active_connections[user_id].discard(connection)

manager = ConnectionManager()

@router.websocket("/updates/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time learning updates
    
    Frontend connects to this endpoint to receive:
    - Learning progress updates
    - Achievement notifications
    - Recommendation changes
    - System status updates
    """
    await manager.connect(websocket, user_id)
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "Connected to learning updates",
            "user_id": user_id,
            "timestamp": asyncio.get_event_loop().time()
        }))
        
        # Keep connection alive and listen for client messages
        while True:
            try:
                # Receive message from client (could be ping, status requests, etc.)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle client messages
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": asyncio.get_event_loop().time()
                    }))
                elif message.get("type") == "status_request":
                    # Send current status (could be expanded)
                    await websocket.send_text(json.dumps({
                        "type": "status",
                        "status": "connected",
                        "user_id": user_id,
                        "timestamp": asyncio.get_event_loop().time()
                    }))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"❌ WebSocket error for user {user_id}: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, user_id)

# Helper function to be called by the learning consumer
async def notify_learning_update(user_id: str, concept: str, mastery: float, delta: float):
    """
    Send learning progress update to user's WebSocket connections
    
    This function should be called by the learning consumer after processing events.
    """
    message = {
        "type": "learning_update",
        "user_id": user_id,
        "concept": concept,
        "mastery": mastery,
        "delta": delta,
        "timestamp": asyncio.get_event_loop().time(),
        "insight": {
            "message": "Great progress!" if delta > 0 else "Keep practicing!",
            "level": "improving" if delta > 0 else "stable"
        }
    }
    
    await manager.send_personal_message(message, user_id)

async def notify_achievement(user_id: str, achievement: dict):
    """
    Send achievement notification to user's WebSocket connections
    """
    message = {
        "type": "achievement",
        "user_id": user_id,
        "achievement": achievement,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await manager.send_personal_message(message, user_id)

async def notify_recommendation_change(user_id: str, new_concept: str, reason: str):
    """
    Send recommendation change notification
    """
    message = {
        "type": "recommendation_change",
        "user_id": user_id,
        "new_concept": new_concept,
        "reason": reason,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await manager.send_personal_message(message, user_id)

# Export functions for use by other modules
__all__ = [
    'manager',
    'notify_learning_update',
    'notify_achievement', 
    'notify_recommendation_change'
]
