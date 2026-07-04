"""
User Profile Endpoint - User profile management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.api.dependencies.auth import get_current_user
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    learning_rate: Optional[float] = None
    forgetting_rate: Optional[float] = None

@router.get("/me")
async def get_user_profile(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current user profile"""
    try:
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "policy_mode": user["policy_mode"],
            "learning_rate": user["learning_rate"],
            "forgetting_rate": user["forgetting_rate"],
            "experiment_id": user["experiment_id"],
            "experiment_group": user["experiment_group"],
            "created_at": user["created_at"],
            "last_active": user["last_active"]
        }
    except Exception as e:
        logger.error(f"❌ Get profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile")

@router.patch("/me")
async def update_user_profile(
    request: UpdateProfileRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update current user profile"""
    try:
        from app.services.auth.dependencies import get_auth_service
        
        auth_service = get_auth_service()
        
        # Update user fields
        user_updated = False
        
        if request.name is not None:
            user["name"] = request.name
            user_updated = True
        
        if request.learning_rate is not None:
            user["learning_rate"] = request.learning_rate
            user_updated = True
            
        if request.forgetting_rate is not None:
            user["forgetting_rate"] = request.forgetting_rate
            user_updated = True
        
        if user_updated:
            user["last_active"] = datetime.utcnow().isoformat()  # Update timestamp
            logger.info(f"✏️ Updated profile for user: {user['id']}")
        
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "policy_mode": user["policy_mode"],
            "learning_rate": user["learning_rate"],
            "forgetting_rate": user["forgetting_rate"],
            "experiment_id": user["experiment_id"],
            "experiment_group": user["experiment_group"],
            "created_at": user["created_at"],
            "last_active": user["last_active"]
        }
        
    except Exception as e:
        logger.error(f"❌ Update profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")
