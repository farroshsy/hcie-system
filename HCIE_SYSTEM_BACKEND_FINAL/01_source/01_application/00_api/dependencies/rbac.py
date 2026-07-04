"""
RBAC Dependencies - Role-Based Access Control
"""

from fastapi import Depends, HTTPException
from app.api.dependencies.auth import get_current_user
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Define system roles
ROLES = ["student", "researcher", "admin"]

def require_role(*allowed_roles: str):
    """Dependency to require specific roles"""
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            logger.warning(f"🚫 Access denied: {user['email']} lacks required role {allowed_roles}")
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Requires role: {allowed_roles}"
            )
        logger.info(f"✅ Role access granted: {user['email']} has role {user['role']}")
        return user
    return role_checker

def require_admin(user: Dict[str, Any] = Depends(get_current_user)):
    """Require admin role"""
    if user["role"] != "admin":
        logger.warning(f"🚫 Admin access denied: {user['email']}")
        raise HTTPException(
            status_code=403,
            detail="Access denied. Admin role required"
        )
    logger.info(f"✅ Admin access granted: {user['email']}")
    return user

def require_student(user: Dict[str, Any] = Depends(get_current_user)):
    """ITS production routes: student role plus elevated roles used in dev."""
    allowed = ("student", "admin", "researcher", "user")
    if user.get("role") not in allowed:
        logger.warning(
            f"🚫 ITS access denied: {user.get('email')} role={user.get('role')}"
        )
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Requires one of: {allowed}",
        )
    return user


def require_researcher_or_admin(user: Dict[str, Any] = Depends(get_current_user)):
    """Require researcher or admin role"""
    if user["role"] not in ["researcher", "admin"]:
        logger.warning(f"🚫 Research access denied: {user['email']}")
        raise HTTPException(
            status_code=403,
            detail="Access denied. Researcher or admin role required"
        )
    logger.info(f"✅ Research access granted: {user['email']}")
    return user

def check_tenant_access(user: Dict[str, Any], resource_tenant_id: str) -> bool:
    """Check if user can access tenant resource"""
    user_tenant_id = user.get("tenant_id")
    
    if not user_tenant_id or user_tenant_id != resource_tenant_id:
        logger.warning(f"🚫 Cross-tenant access denied: {user['email']} cannot access tenant {resource_tenant_id}")
        return False
    
    logger.info(f"✅ Tenant access granted: {user['email']} can access tenant {resource_tenant_id}")
    return True
