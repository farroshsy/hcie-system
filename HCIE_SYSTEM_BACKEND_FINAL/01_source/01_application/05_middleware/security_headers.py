"""
Security Headers Middleware

Adds security headers to all HTTP responses to prevent common vulnerabilities.
Implements OWASP security best practices.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses.
    
    Security headers included:
    - X-Content-Type-Options: Prevents MIME-sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: XSS protection
    - Strict-Transport-Security: Enforces HTTPS
    - Content-Security-Policy: Controls resource loading
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    """
    
    def __init__(
        self,
        app,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True,
        csp_directives: dict = None
    ):
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        
        # Default CSP directives
        self.csp_directives = csp_directives or {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src": "'self' 'unsafe-inline'",
            "img-src": "'self' data: https:",
            "font-src": "'self' data:",
            "connect-src": "'self'",
            "frame-ancestors": "'none'",
            "form-action": "'self'",
            "base-uri": "'self'"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers to response.
        """
        
        response = await call_next(request)
        
        # X-Content-Type-Options: Prevents MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options: Prevents clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection: XSS protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy: Controls referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Strict-Transport-Security: Enforces HTTPS (only in production)
        # Skip for local development
        if request.url.is_secure:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # Content-Security-Policy: Controls resource loading
        csp_value = "; ".join([f"{key} {value}" for key, value in self.csp_directives.items()])
        response.headers["Content-Security-Policy"] = csp_value
        
        # Permissions-Policy: Controls browser features (formerly Feature-Policy)
        permissions_policy = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_policy)
        
        # Remove server information for security
        response.headers["Server"] = "HCIE-API"
        
        return response


def register_security_headers(app, config: dict = None):
    """
    Register security headers middleware with FastAPI app.
    
    Args:
        app: FastAPI application
        config: Optional configuration override
    """
    
    middleware_config = config or {}
    
    app.add_middleware(
        SecurityHeadersMiddleware,
        **middleware_config
    )
    
    logger.info("✅ Security headers middleware registered")
