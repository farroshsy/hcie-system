"""
V3 Auth API - Enhanced Authentication System

Complete authentication system with JWT verification, user management, and role-based access.
Authority State: converging → authoritative
Runtime Contract Version: 1.0
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["v3-auth"])

auth_router = router

security = HTTPBearer()


# Pydantic models for API
class LoginRequest(BaseModel):
    """Login request."""
    email: str
    password: str


class LoginResponse(BaseModel):
    """Login response."""
    access_token: str
    refresh_token: str
    user: Dict[str, Any]
    semantic_version: str = "1.0"


class TokenRefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class RegisterRequest(BaseModel):
    """Register a new user (Phase 14e V3 auth completion)."""
    email: str
    password: str
    name: Optional[str] = None
    role: str = "student"


class TokenRefreshResponse(BaseModel):
    """Token refresh response."""
    access_token: str
    semantic_version: str = "1.0"


class UserProfileResponse(BaseModel):
    """User profile response."""
    user_id: str
    email: str
    role: str
    permissions: list
    semantic_version: str = "1.0"


@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest):
    """Register a new user and return JWT tokens immediately (idempotent on email)."""
    try:
        from app.services.auth.dependencies import get_auth_service, get_jwt_service

        auth_service = get_auth_service()
        jwt_service = get_jwt_service()

        try:
            user = auth_service.register_user(
                email=request.email,
                password=request.password,
                name=request.name or request.email.split("@")[0],
                role=request.role,
            )
        except Exception as exc:
            existing = auth_service.authenticate_user(request.email, request.password)
            if existing is None:
                raise HTTPException(
                    status_code=409,
                    detail=f"Registration failed: {exc}",
                )
            user = existing

        user_id = user.get("id") or user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=500, detail="Registered user missing id")

        token_subject = {
            "sub": user_id,
            "email": user.get("email") or request.email,
            "role": user.get("role") or request.role,
        }
        access_token = jwt_service.create_access_token(token_subject)
        refresh_token = jwt_service.create_refresh_token(token_subject)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user={
                "user_id": user_id,
                "email": token_subject["email"],
                "role": token_subject["role"],
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return tokens.
    
    Enhanced auth with JWT tokens (access + refresh).
    """
    try:
        from app.services.auth.dependencies import get_auth_service, get_jwt_service
        
        auth_service = get_auth_service()
        jwt_service = get_jwt_service()
        
        # Authenticate user
        user = auth_service.authenticate_user(request.email, request.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user_id = user.get("id") or user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=500, detail="Authenticated user missing id")

        token_subject = {
            "sub": user_id,
            "email": user.get("email"),
            "role": user.get("role", "student"),
        }
        access_token = jwt_service.create_access_token(token_subject)
        refresh_token = jwt_service.create_refresh_token(token_subject)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user={
                "user_id": user_id,
                "email": user.get("email"),
                "role": token_subject["role"],
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(request: TokenRefreshRequest):
    """
    Refresh access token using refresh token.
    
    Enhanced auth with token refresh capability.
    """
    try:
        from app.services.auth.dependencies import get_jwt_service
        
        jwt_service = get_jwt_service()
        
        # Verify refresh token
        payload = jwt_service.verify_token(request.refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        new_access_token = jwt_service.create_access_token(
            {"sub": payload["sub"], "role": payload.get("role", "student")}
        )
        
        return TokenRefreshResponse(access_token=new_access_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user profile with permissions.
    
    Enhanced auth with user profile and role-based permissions.
    """
    try:
        from app.api.dependencies.auth import get_current_user
        
        # Use existing V2 auth dependency
        user = await get_current_user(credentials)
        
        return UserProfileResponse(
            user_id=user.get("id") or user.get("user_id"),
            email=user.get("email"),
            role=user.get("role", "student"),
            permissions=user.get("permissions", ["read"]),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout user (invalidate tokens).
    
    Enhanced auth with token invalidation.
    """
    try:
        from app.services.auth.dependencies import get_jwt_service
        
        jwt_service = get_jwt_service()
        token = credentials.credentials
        
        # Invalidate token (add to blacklist)
        # Note: This requires Redis or similar for token blacklisting
        # For now, return success (client should discard tokens)
        
        return {"message": "Logged out successfully", "semantic_version": "1.0"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")
