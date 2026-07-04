"""Service-to-service authentication dependencies."""

from __future__ import annotations

import hmac
import os
from typing import Dict

from fastapi import Header, HTTPException


def require_service_token(
    x_hcie_service_token: str | None = Header(default=None, alias="X-HCIE-Service-Token"),
) -> Dict[str, str]:
    """Require the internal service token for `/v3/service/*` routes."""

    expected = os.getenv("HCIE_SERVICE_TOKEN", "dev-service-token")
    if not x_hcie_service_token or not hmac.compare_digest(x_hcie_service_token, expected):
        raise HTTPException(status_code=401, detail="Invalid service token")
    return {"service": "internal", "auth": "service_token"}
