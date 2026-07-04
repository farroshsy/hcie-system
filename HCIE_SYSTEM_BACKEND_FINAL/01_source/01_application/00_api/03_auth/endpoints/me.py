"""
Auth Me Endpoint - Get current user info
"""

from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies.auth import get_current_user
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/me")
async def get_me(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current user information"""
    try:
        # Return user data without sensitive info
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
        logger.error(f"❌ Get me error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user info")
