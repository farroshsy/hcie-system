"""
Auth Login Endpoint - User authentication
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str
    role: str
    policy_mode: str
    experiment_group: str

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> Dict[str, Any]:
    """Authenticate user and return tokens"""
    try:
        from app.services.auth.dependencies import get_auth_service, get_jwt_service
        
        auth_service = get_auth_service()
        jwt_service = get_jwt_service()
        
        # Authenticate user
        user = auth_service.authenticate_user(request.email, request.password)
        if not user:
            logger.warning(f"❌ Login failed for: {request.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create tokens
        user_data = {
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"],
            "policy_mode": user["policy_mode"],
            "experiment_group": user["experiment_group"]
        }
        
        access_token = jwt_service.create_access_token(user_data)
        refresh_token = jwt_service.create_refresh_token(user_data)
        
        # Store refresh token
        auth_service.store_refresh_token(user["id"], refresh_token)
        
        logger.info(f"🔐 User logged in: {request.email}")
        
        return {
            "user_id": user["id"],
            "access_token": access_token,
            "refresh_token": refresh_token,
            "role": user["role"],
            "policy_mode": user["policy_mode"],
            "experiment_group": user["experiment_group"] or "none"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")
