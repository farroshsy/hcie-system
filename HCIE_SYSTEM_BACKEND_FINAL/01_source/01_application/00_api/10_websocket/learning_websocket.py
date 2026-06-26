"""
Real-time WebSocket API for live learning updates
"""

import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_data: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and track user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"🔌 WebSocket connected: user={user_id}, total_connections={len(self.active_connections[user_id])}")
        
        # Send initial data
        await self.send_initial_data(websocket, user_id)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"🔌 WebSocket disconnected: user={user_id}")
    
    async def send_initial_data(self, websocket: WebSocket, user_id: str):
        """Send initial learning data to newly connected client"""
        try:
            # 🔥 OWNERSHIP BOUNDARY: Frontend must read from learner_progress, NOT UnifiedBrain
            # UnifiedBrain is only reachable through event ingestion or replay topology
            from app.api.dependencies.learning import get_task_service
            task_service = get_task_service()
            db_store = task_service.db_store
            
            # Get mastery for common concepts from learner_progress table (canonical source)
            concepts = ["k2_algorithms", "k5_algorithms", "k8_algorithms"]
            initial_data = {
                "type": "initial_data",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": {}
            }
            
            for concept in concepts:
                try:
                    # Query from learner_progress table
                    progress = db_store.query_learner_progress(user_id, concept)
                    if progress:
                        initial_data["data"][concept] = {
                            "mastery": progress.get("mastery", 0.3),
                            "uncertainty": progress.get("uncertainty", 0.25),
                            "zpd_score": progress.get("zpd_score", 0.7),
                            "adaptive_rate": progress.get("adaptive_rate", 0.02)
                        }
                    else:
                        # No progress data yet, use default
                        initial_data["data"][concept] = {
                            "mastery": 0.3,
                            "uncertainty": 0.25,
                            "zpd_score": 0.7,
                            "adaptive_rate": 0.02
                        }
                except Exception as e:
                    logger.warning(f"Failed to get initial data for {concept} from learner_progress: {e}")
                    initial_data["data"][concept] = {
                        "mastery": 0.3,
                        "uncertainty": 0.25,
                        "zpd_score": 0.7,
                        "adaptive_rate": 0.02
                    }
            
            await websocket.send_text(json.dumps(initial_data))
            
        except Exception as e:
            logger.error(f"❌ Error sending initial data: {e}")
    
    async def broadcast_to_user(self, user_id: str, message: Dict):
        """Send message to all connections for a specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"❌ Failed to send to connection: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.disconnect(conn, user_id)
    
    async def broadcast_learning_update(self, user_id: str, concept: str, result):
        """Broadcast learning update to user's connections"""
        message = {
            "type": "learning_update",
            "user_id": user_id,
            "concept": concept,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "mastery": result.mastery,
                "uncertainty": result.uncertainty,
                "zpd_score": result.zpd_score,
                "adaptive_rate": getattr(result, 'adaptive_rate', 0.02),
                "lyapunov_mastery": result.lyapunov_mastery,
                "bayesian_alpha": result.bayesian_alpha,
                "bayesian_beta": result.bayesian_beta,
                "kalman_mastery": result.kalman_mastery
            }
        }
        
        await self.broadcast_to_user(user_id, message)
    
    async def broadcast_adaptive_rate_update(self, user_id: str, concept: str, adaptive_rate: float):
        """Broadcast adaptive rate change"""
        message = {
            "type": "adaptive_rate_update",
            "user_id": user_id,
            "concept": concept,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "adaptive_rate": adaptive_rate,
                "change_type": "increase" if adaptive_rate > 0.02 else "decrease" if adaptive_rate < 0.02 else "stable"
            }
        }
        
        await self.broadcast_to_user(user_id, message)

# Global connection manager
manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Main WebSocket endpoint for real-time learning updates"""
    await manager.connect(websocket, user_id)
    
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
                elif message.get("type") == "subscribe_concept":
                    # Handle concept subscription (future enhancement)
                    concept = message.get("concept")
                    logger.info(f"🔌 User {user_id} subscribed to {concept}")
                
            except json.JSONDecodeError:
                logger.warning(f"❌ Invalid JSON from WebSocket: {data}")
                continue
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket, user_id)

# Helper functions for broadcasting from other parts of the system
async def broadcast_learning_update(user_id: str, concept: str, result):
    """Broadcast learning update (call from learning system)"""
    await manager.broadcast_learning_update(user_id, concept, result)

async def broadcast_adaptive_rate_update(user_id: str, concept: str, adaptive_rate: float):
    """Broadcast adaptive rate update (call from learning system)"""
    await manager.broadcast_adaptive_rate_update(user_id, concept, adaptive_rate)
