"""
WebSocket Manager for Real-Time Updates

Provides WebSocket connection management for real-time updates to clients.
Supports broadcasting, targeted messaging, and connection lifecycle management.
"""

from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
from pydantic import BaseModel, Field
from enum import Enum
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of WebSocket messages"""
    SYSTEM_UPDATE = "system_update"
    USER_UPDATE = "user_update"
    PROJECTION_UPDATE = "projection_update"
    EVENT_NOTIFICATION = "event_notification"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class WebSocketMessage(BaseModel):
    """Standard WebSocket message format"""
    message_type: MessageType = Field(description="Type of message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    message_id: Optional[str] = Field(default=None, description="Unique message identifier")


class Connection(BaseModel):
    """WebSocket connection information"""
    websocket: WebSocket = Field(description="WebSocket connection")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    connected_at: datetime = Field(default_factory=datetime.utcnow, description="Connection timestamp")
    subscriptions: Set[str] = Field(default_factory=set, description="Topics subscribed to")
    
    class Config:
        arbitrary_types_allowed = True


class WebSocketManager:
    """
    Manager for WebSocket connections and real-time updates.
    
    Handles connection lifecycle, message broadcasting, and targeted messaging.
    """
    
    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: Dict[str, Connection] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        self.topic_subscribers: Dict[str, Set[str]] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: Optional user identifier
            session_id: Optional session identifier
            
        Returns:
            Connection ID
        """
        await websocket.accept()
        
        connection_id = f"conn_{datetime.utcnow().timestamp()}_{id(websocket)}"
        
        connection = Connection(
            websocket=websocket,
            user_id=user_id,
            session_id=session_id
        )
        
        self.active_connections[connection_id] = connection
        
        # Track user connections
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        logger.info(f"WebSocket connection {connection_id} established for user {user_id}")
        
        # Send welcome message
        await self.send_personal_message(
            WebSocketMessage(
                message_type=MessageType.SYSTEM_UPDATE,
                data={"status": "connected", "connection_id": connection_id}
            ),
            connection_id
        )
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """
        Disconnect a WebSocket connection.
        
        Args:
            connection_id: Connection identifier
        """
        connection = self.active_connections.get(connection_id)
        
        if connection:
            # Remove from user connections
            if connection.user_id:
                if connection.user_id in self.user_connections:
                    self.user_connections[connection.user_id].discard(connection_id)
            
            # Remove from topic subscriptions
            for topic in connection.subscriptions:
                if topic in self.topic_subscribers:
                    self.topic_subscribers[topic].discard(connection_id)
            
            # Remove connection
            del self.active_connections[connection_id]
            
            logger.info(f"WebSocket connection {connection_id} disconnected")
    
    async def send_personal_message(
        self,
        message: WebSocketMessage,
        connection_id: str
    ):
        """
        Send a message to a specific connection.
        
        Args:
            message: Message to send
            connection_id: Connection identifier
        """
        connection = self.active_connections.get(connection_id)
        
        if connection:
            try:
                await connection.websocket.send_json(message.dict())
            except Exception as e:
                logger.error(f"Error sending message to connection {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast(
        self,
        message: WebSocketMessage,
        exclude: Optional[Set[str]] = None
    ):
        """
        Broadcast a message to all active connections.
        
        Args:
            message: Message to broadcast
            exclude: Optional set of connection IDs to exclude
        """
        exclude = exclude or set()
        
        for connection_id, connection in list(self.active_connections.items()):
            if connection_id not in exclude:
                await self.send_personal_message(message, connection_id)
    
    async def send_to_user(
        self,
        message: WebSocketMessage,
        user_id: str
    ):
        """
        Send a message to all connections for a specific user.
        
        Args:
            message: Message to send
            user_id: User identifier
        """
        connection_ids = self.user_connections.get(user_id, set())
        
        for connection_id in connection_ids:
            await self.send_personal_message(message, connection_id)
    
    async def send_to_topic(
        self,
        message: WebSocketMessage,
        topic: str
    ):
        """
        Send a message to all subscribers of a topic.
        
        Args:
            message: Message to send
            topic: Topic to send to
        """
        connection_ids = self.topic_subscribers.get(topic, set())
        
        for connection_id in connection_ids:
            await self.send_personal_message(message, connection_id)
    
    def subscribe(
        self,
        connection_id: str,
        topic: str
    ):
        """
        Subscribe a connection to a topic.
        
        Args:
            connection_id: Connection identifier
            topic: Topic to subscribe to
        """
        connection = self.active_connections.get(connection_id)
        
        if connection:
            connection.subscriptions.add(topic)
            
            if topic not in self.topic_subscribers:
                self.topic_subscribers[topic] = set()
            self.topic_subscribers[topic].add(connection_id)
            
            logger.info(f"Connection {connection_id} subscribed to topic {topic}")
    
    def unsubscribe(
        self,
        connection_id: str,
        topic: str
    ):
        """
        Unsubscribe a connection from a topic.
        
        Args:
            connection_id: Connection identifier
            topic: Topic to unsubscribe from
        """
        connection = self.active_connections.get(connection_id)
        
        if connection:
            connection.subscriptions.discard(topic)
            
            if topic in self.topic_subscribers:
                self.topic_subscribers[topic].discard(connection_id)
            
            logger.info(f"Connection {connection_id} unsubscribed from topic {topic}")
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a specific user."""
        return len(self.user_connections.get(user_id, set()))
    
    def get_topic_subscriber_count(self, topic: str) -> int:
        """Get number of subscribers for a topic."""
        return len(self.topic_subscribers.get(topic, set()))
    
    async def start_heartbeat(self, interval_seconds: int = 30):
        """
        Start heartbeat task to keep connections alive.
        
        Args:
            interval_seconds: Heartbeat interval in seconds
        """
        while True:
            try:
                heartbeat_message = WebSocketMessage(
                    message_type=MessageType.HEARTBEAT,
                    data={"timestamp": datetime.utcnow().isoformat()}
                )
                
                await self.broadcast(heartbeat_message)
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat task: {e}")
                await asyncio.sleep(interval_seconds)


# Global WebSocket manager instance
_global_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """
    Get the global WebSocket manager instance.
    
    Returns:
        WebSocketManager instance
    """
    global _global_websocket_manager
    if _global_websocket_manager is None:
        _global_websocket_manager = WebSocketManager()
    return _global_websocket_manager
