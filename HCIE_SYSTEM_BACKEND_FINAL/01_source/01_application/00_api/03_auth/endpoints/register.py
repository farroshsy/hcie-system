"""
Auth Register Endpoint - User registration
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    role: str = "student"

class RegisterResponse(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str
    role: str

@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest) -> Dict[str, Any]:
    """Register new user"""
    try:
        from app.services.auth.dependencies import get_auth_service, get_jwt_service
        
        auth_service = get_auth_service()
        jwt_service = get_jwt_service()
        
        # Register user
        user = auth_service.register_user(
            email=request.email,
            password=request.password,
            name=request.name,
            role=request.role
        )
        
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
        
        logger.info(f"🎉 User registered: {request.email}")
        
        return {
            "user_id": user["id"],
            "access_token": access_token,
            "refresh_token": refresh_token,
            "role": user["role"]
        }
        
    except ValueError as e:
        logger.warning(f"⚠️ Registration failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")
