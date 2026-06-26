"""
Auth API Package

Enhanced authentication system with JWT verification, user management, and role-based access.
"""

from .auth import auth_router

__all__ = [
    'auth_router'
]
