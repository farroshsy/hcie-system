"""
Rate Limiting Middleware

Prevents API abuse with configurable rate limits per user/IP.
Supports per-user, per-IP, and endpoint-specific rate limits.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Dict, Callable
import time
import logging
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.
    
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(self):
        # Store request timestamps per key: key -> list of timestamps
        self.requests: Dict[str, list] = defaultdict(list)
        
        # Default limits (requests per minute)
        self.default_limits = {
            "global": 100,  # 100 requests per minute globally
            "per_user": 60,  # 60 requests per minute per user
            "per_ip": 40,    # 40 requests per minute per IP
        }
        
        # Endpoint-specific limits (higher for read operations)
        self.endpoint_limits = {
            "GET": 80,   # 80 requests per minute for GET
            "POST": 40,  # 40 requests per minute for POST
            "PUT": 30,   # 30 requests per minute for PUT
            "DELETE": 20 # 20 requests per minute for DELETE
        }
    
    @staticmethod
    def _client_ip(request: Request) -> str:
        """Real client IP — honour X-Forwarded-For (first hop) behind a proxy/gateway,
        so the limiter isn't keyed on a single shared proxy address."""
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            return xff.split(",")[0].strip()
        return getattr(request.client, "host", "unknown") if request.client else "unknown"

    def _get_key(self, request: Request, key_type: str = "ip") -> str:
        """Generate rate limit key based on type."""

        if key_type == "user":
            # Use user_id from auth header if available
            auth_header = request.headers.get("Authorization")
            if auth_header:
                # Hash the token to create a unique user key
                return f"user:{hashlib.md5(auth_header.encode(), usedforsecurity=False).hexdigest()}"
            # Fallback to IP
            return f"ip:{self._client_ip(request)}"

        elif key_type == "ip":
            return f"ip:{self._client_ip(request)}"
        
        elif key_type == "endpoint":
            return f"endpoint:{request.url.path}:{request.method}"
        
        return "global"
    
    def _clean_old_requests(self, key: str, window_seconds: int = 60):
        """Remove requests older than the time window."""
        
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        # Filter out old timestamps
        self.requests[key] = [
            timestamp for timestamp in self.requests[key]
            if timestamp > cutoff_time
        ]
    
    def check_rate_limit(
        self,
        request: Request,
        limit: int = 100,
        window_seconds: int = 60,
        key_type: str = "ip"
    ) -> tuple[bool, int]:
        """
        Check if request should be rate limited.
        
        Returns:
            (is_allowed, retry_after_seconds)
        """
        
        key = self._get_key(request, key_type)
        current_time = time.time()
        
        # Clean old requests
        self._clean_old_requests(key, window_seconds)
        
        # Check if limit exceeded
        request_count = len(self.requests[key])
        
        if request_count >= limit:
            # Calculate retry after
            oldest_request = min(self.requests[key])
            retry_after = int(oldest_request + window_seconds - current_time) + 1
            logger.warning(f"Rate limit exceeded for {key}: {request_count}/{limit} requests")
            return False, retry_after
        
        # Add current request
        self.requests[key].append(current_time)
        
        return True, 0


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(
    request: Request,
    call_next: Callable,
    limiter: RateLimiter = rate_limiter
):
    """
    Rate limiting middleware for FastAPI.
    
    Checks multiple rate limit tiers:
    1. Global rate limit
    2. Per-IP rate limit
    3. Per-user rate limit (if authenticated)
    4. Endpoint-specific rate limit
    """
    
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/", "/metrics", "/healthz"]:
        return await call_next(request)

    # Skip rate limiting for cohort/experiment orchestration. These endpoints
    # are researcher-only (RBAC enforced) and drive bursty server-internal
    # workloads (external-log replay, ITS prediction surface). Rate-limiting
    # them creates artificial throughput caps for offline research runs
    # without protecting any externally-exposed surface.
    if request.url.path.startswith("/v3/experiments/cohorts"):
        return await call_next(request)

    # Skip rate limiting for loopback traffic. The API issues internal
    # ``requests.post`` calls to itself (e.g. ``cohorts.external_attempt`` →
    # ``/v3/learner/attempt``); throttling those would deadlock the
    # orchestration path against its own outer limit.
    client_host = getattr(request.client, "host", None) if request.client else None
    if client_host in {"127.0.0.1", "::1"}:
        return await call_next(request)
    
    # Check global rate limit
    allowed, retry_after = limiter.check_rate_limit(
        request,
        limit=limiter.default_limits["global"],
        window_seconds=60,
        key_type="global"
    )
    
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Global rate limit exceeded",
                    "context": {"retry_after": retry_after}
                },
                "status": status.HTTP_429_TOO_MANY_REQUESTS
            },
            headers={"Retry-After": str(retry_after)}
        )
    
    # Check per-IP rate limit
    allowed, retry_after = limiter.check_rate_limit(
        request,
        limit=limiter.default_limits["per_ip"],
        window_seconds=60,
        key_type="ip"
    )
    
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "IP rate limit exceeded",
                    "context": {"retry_after": retry_after}
                },
                "status": status.HTTP_429_TOO_MANY_REQUESTS
            },
            headers={"Retry-After": str(retry_after)}
        )
    
    # Check per-user rate limit (if authenticated)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        allowed, retry_after = limiter.check_rate_limit(
            request,
            limit=limiter.default_limits["per_user"],
            window_seconds=60,
            key_type="user"
        )
        
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "User rate limit exceeded",
                        "context": {"retry_after": retry_after}
                    },
                    "status": status.HTTP_429_TOO_MANY_REQUESTS
                },
                headers={"Retry-After": str(retry_after)}
            )
    
    # Check endpoint-specific rate limit
    method_limit = limiter.endpoint_limits.get(request.method, 60)
    allowed, retry_after = limiter.check_rate_limit(
        request,
        limit=method_limit,
        window_seconds=60,
        key_type="endpoint"
    )
    
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Endpoint rate limit exceeded for {request.method}",
                    "context": {"retry_after": retry_after}
                },
                "status": status.HTTP_429_TOO_MANY_REQUESTS
            },
            headers={"Retry-After": str(retry_after)}
        )
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers to response
    response.headers["X-RateLimit-Limit"] = str(method_limit)
    response.headers["X-RateLimit-Remaining"] = str(max(0, method_limit - len(limiter.requests[limiter._get_key(request, "endpoint")])))
    response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
    
    return response


def register_rate_limiting(app, limiter: RateLimiter = rate_limiter):
    """Register rate limiting middleware with FastAPI app."""
    
    app.middleware("http")(rate_limit_middleware)
    
    logger.info("✅ Rate limiting middleware registered")
