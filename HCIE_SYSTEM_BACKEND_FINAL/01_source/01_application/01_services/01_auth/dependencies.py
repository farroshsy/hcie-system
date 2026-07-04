"""
Auth Dependencies - Singleton services and shared dependencies
"""

from .auth_service import AuthService
from .jwt_service import JWTService
from ...repositories.user_repository import UserRepository
from ...repositories.redis_token_store import RedisTokenStore

# Create singleton instances (shared across all requests)
_auth_service = None
_jwt_service = None

def get_auth_service() -> AuthService:
    """Get singleton AuthService instance with repositories"""
    global _auth_service
    if _auth_service is None:
        # Will be injected by ServiceFactory with proper repositories
        from ..service_factory import get_service_factory
        sf = get_service_factory()
        _auth_service = sf.get_auth_service()
    return _auth_service

def get_jwt_service() -> JWTService:
    """Get singleton JWTService instance"""
    global _jwt_service
    if _jwt_service is None:
        _jwt_service = JWTService()
    return _jwt_service

def create_auth_service(user_repo=None, token_store=None, event_producer=None) -> AuthService:
    """Create AuthService with proper repositories and event producer"""
    return AuthService(user_repo=user_repo, token_store=token_store, event_producer=event_producer)
