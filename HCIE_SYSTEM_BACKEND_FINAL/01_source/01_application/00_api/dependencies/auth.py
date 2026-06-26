"""
Auth Dependencies - Centralized authentication for FastAPI
"""

import logging
import os
from typing import Any, Dict

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Resolve the calling user from the JWT.

    Phase 14e behavior:
      - Verify the JWT via ``JWTService`` (must be ``access`` token).
      - Look the user up via the auth singleton. If the singleton is
        unavailable (e.g. V2 ``UnifiedLearningBrain`` failed to initialize
        and the user repo never got built — tracked as a 14i defect) the
        JWT payload itself is treated as the user identity. This avoids
        the FINAL ITS surface being held hostage by a stale V2 stack.
    """
    try:
        from app.services.auth.dependencies import get_jwt_service

        jwt_service = get_jwt_service()
        token = credentials.credentials

        payload = jwt_service.verify_token(token, token_type="access")
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            from app.services.auth.dependencies import get_auth_service

            auth_service = get_auth_service()
            user = auth_service.get_user_by_id(payload["sub"])
        except Exception as exc:
            logger.warning(
                "Auth singleton unavailable, trusting JWT payload: %s", exc
            )
            user = None

        if not user:
            # SECURITY: default OFF. Trusting role straight from the JWT payload without a DB
            # user lookup is a full RBAC-bypass surface; only enable deliberately in trusted dev.
            allow_jwt_only = os.environ.get("HCIE_AUTH_TRUST_JWT", "0") == "1"
            if not allow_jwt_only:
                raise HTTPException(status_code=401, detail="User not found")
            user = {
                "id": payload.get("sub"),
                "user_id": payload.get("sub"),
                "email": payload.get("email") or f"{payload.get('sub')}@hcie.local",
                "role": payload.get("role", "student"),
                "_auth_source": "jwt_payload",
            }

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Auth error: %s", e)
        raise HTTPException(status_code=401, detail="Authentication failed")
