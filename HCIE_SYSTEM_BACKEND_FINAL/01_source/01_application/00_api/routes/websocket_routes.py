"""
WebSocket Routes - Real-time learning updates
"""

from fastapi import APIRouter, WebSocket
from app.api.websocket.learning_websocket import websocket_endpoint, manager
from app.api.websocket.projection_websocket import projection_websocket_endpoint, projection_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/learning/{user_id}")
async def learning_websocket(websocket: WebSocket, user_id: str):
    """
    Real-time learning updates WebSocket endpoint
    
    Connect to: ws://localhost:8000/ws/learning/{user_id}
    
    Messages received:
    - {"type": "ping"} - Keep connection alive
    - {"type": "subscribe_concept", "concept": "k2_algorithms"} - Subscribe to concept updates
    
    Messages sent:
    - Initial learning state for all concepts
    - Real-time mastery updates
    - Adaptive rate changes
    - ZPD alignment updates
    """
    await websocket_endpoint(websocket, user_id)

@router.websocket("/projections/{user_id}")
async def projection_websocket(websocket: WebSocket, user_id: str):
    """
    B4.1 Projection WebSocket - Streams ProjectionUpdated events to frontend
    
    Connect to: ws://localhost:8000/ws/projections/{user_id}
    
    Messages received:
    - {"type": "ping"} - Keep connection alive
    
    Messages sent:
    - Initial connection message
    - ProjectionUpdated events (cognition + adaptation enrichment)
    
    ARCHITECTURAL CONSTRAINTS:
    - Streams ONLY ProjectionUpdated events
    - Validates event_type = "ProjectionUpdated" (security constraint)
    - Frontend is semantic materialized-view renderer only
    """
    await projection_websocket_endpoint(websocket, user_id)

@router.get("/connections")
async def get_connection_status():
    """
    Get current WebSocket connection status
    """
    try:
        learning_connection_count = sum(len(connections) for connections in manager.active_connections.values())
        projection_connection_count = sum(len(connections) for connections in projection_manager.active_connections.values())
        learning_active_users = list(manager.active_connections.keys())
        projection_active_users = list(projection_manager.active_connections.keys())
        
        return {
            "success": True,
            "data": {
                "learning_connections": {
                    "total_connections": learning_connection_count,
                    "active_users": learning_active_users,
                    "connections_per_user": {user: len(connections) for user, connections in manager.active_connections.items()}
                },
                "projection_connections": {
                    "total_connections": projection_connection_count,
                    "active_users": projection_active_users,
                    "connections_per_user": {user: len(connections) for user, connections in projection_manager.active_connections.items()}
                }
            },
            "message": f"Learning: {len(learning_active_users)} users with {learning_connection_count} connections | Projections: {len(projection_active_users)} users with {projection_connection_count} connections"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting connection status: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get connection status"
        }
