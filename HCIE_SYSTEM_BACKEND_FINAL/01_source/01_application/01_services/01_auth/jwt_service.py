"""
JWT Service - Token management for HCIE platform
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class JWTService:
    INSECURE_DEFAULT = "hcie-secret-key-change-in-production"

    def __init__(self, secret_key: str = None):
        import os
        key = secret_key or os.getenv("JWT_SECRET_KEY", "")
        env = os.getenv("ENVIRONMENT", "production").lower()
        if not key or key == self.INSECURE_DEFAULT:
            if env in ("development", "dev", "test", "testing"):
                key = self.INSECURE_DEFAULT  # local-only convenience
                logger.warning("JWT_SECRET_KEY unset — using insecure DEV default (development only)")
            else:
                raise RuntimeError(
                    "JWT_SECRET_KEY must be set to a strong secret outside development; "
                    "refusing to start with a missing/default token-signing key."
                )
        self.secret_key = key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 7
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = user_data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "type": "access"
        })
        
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.info(f"🔐 Created access token for user {user_data.get('sub')}")
        return token
    
    def create_refresh_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = user_data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({
            "exp": expire,
            "type": "refresh"
        })
        
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.info(f"🔄 Created refresh token for user {user_data.get('sub')}")
        return token
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Validate token type
            if payload.get("type") != token_type:
                logger.warning(f"⚠️ Invalid token type: expected {token_type}, got {payload.get('type')}")
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.PyJWTError as e:  # PyJWT base class (jwt.JWTError does not exist in PyJWT)
            logger.warning(f"Invalid token: {e}")
            return None
    
    def extract_user_id(self, token: str) -> Optional[str]:
        """Extract user ID from token"""
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None
