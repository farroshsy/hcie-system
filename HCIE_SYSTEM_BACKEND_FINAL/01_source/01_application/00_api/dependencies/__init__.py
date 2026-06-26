"""
API Dependencies - Shared FastAPI dependencies
"""

from .auth import get_current_user

def get_current_user_websocket():
    """Get current user for WebSocket connections"""
    return "test_user"  # Simplified for demo

__all__ = ['get_current_user', 'get_current_user_websocket']
