"""
Auth Refresh Endpoint - Token refresh
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class RefreshRequest(BaseModel):
    refresh_token: str

class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: RefreshRequest) -> Dict[str, Any]:
    """Refresh access token using refresh token"""
    try:
        from app.services.auth.dependencies import get_auth_service, get_jwt_service
        
        auth_service = get_auth_service()
        jwt_service = get_jwt_service()
        
        # Verify refresh token type
        payload = jwt_service.verify_token(request.refresh_token, token_type="refresh")
        if not payload:
            logger.warning("⚠️ Invalid refresh token")
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user_id = payload["sub"]
        if not user_id:
            logger.warning("⚠️ Invalid refresh token payload")
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Get user data
        user = auth_service.get_user_by_id(user_id)
        if not user:
            logger.warning(f"⚠️ User not found: {user_id}")
            raise HTTPException(status_code=401, detail="User not found")
        
        # Create new tokens
        user_data = {
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"],
            "policy_mode": user["policy_mode"],
            "experiment_group": user["experiment_group"]
        }
        
        new_access_token = jwt_service.create_access_token(user_data)
        new_refresh_token = jwt_service.create_refresh_token(user_data)
        
        # Revoke old refresh token and store new one
        auth_service.revoke_refresh_token(request.refresh_token)
        auth_service.store_refresh_token(user_id, new_refresh_token)
        
        logger.info(f"🔄 Token refreshed for user: {user_id}")
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")
