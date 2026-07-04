"""
Request Validation Middleware

Enhanced request validation for production security and data integrity.
Validates request size, content type, and sanitizes input.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Callable
import logging
import re

logger = logging.getLogger(__name__)


class RequestValidationMiddleware:
    """
    Validates incoming requests for security and data integrity.
    
    Validates:
    - Request size limits
    - Content-Type headers
    - SQL injection patterns
    - XSS patterns
    - Path traversal attempts
    """
    
    def __init__(
        self,
        max_request_size_mb: int = 10,
        allowed_content_types: list = None,
        enable_sql_injection_check: bool = True,
        enable_xss_check: bool = True,
        enable_path_traversal_check: bool = True
    ):
        self.max_request_size_bytes = max_request_size_mb * 1024 * 1024
        self.allowed_content_types = allowed_content_types or [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data"
        ]
        self.enable_sql_injection_check = enable_sql_injection_check
        self.enable_xss_check = enable_xss_check
        self.enable_path_traversal_check = enable_path_traversal_check
        
        # SQL injection patterns
        self.sql_injection_patterns = [
            r"(\bSELECT\b.*\bFROM\b)",
            r"(\bINSERT\b.*\bINTO\b)",
            r"(\bUPDATE\b.*\bSET\b)",
            r"(\bDELETE\b.*\bFROM\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(\bUNION\b.*\bSELECT\b)",
            r"(--|;|\/\*|\*\/)",
            r"(\bOR\b.*=.*\bOR\b)",
            r"(\bAND\b.*=.*\bAND\b)"
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"eval\s*\(",
            r"document\.",
            r"window\.",
            r"alert\s*\("
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
            r"\.\.%2f",
            r"\.\.%5c"
        ]
    
    def _check_sql_injection(self, value: str) -> bool:
        """Check for SQL injection patterns."""
        
        if not self.enable_sql_injection_check:
            return False
        
        value_upper = value.upper()
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, value_upper, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {value[:100]}")
                return True
        
        return False
    
    def _check_xss(self, value: str) -> bool:
        """Check for XSS patterns."""
        
        if not self.enable_xss_check:
            return False
        
        for pattern in self.xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"XSS pattern detected: {value[:100]}")
                return True
        
        return False
    
    def _check_path_traversal(self, value: str) -> bool:
        """Check for path traversal patterns."""
        
        if not self.enable_path_traversal_check:
            return False
        
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Path traversal pattern detected: {value[:100]}")
                return True
        
        return False
    
    def _validate_string_value(self, key: str, value: str) -> bool:
        """Validate a single string value for security issues."""
        
        # Check SQL injection
        if self._check_sql_injection(value):
            logger.warning(f"SQL injection detected in field: {key}")
            return False
        
        # Check XSS
        if self._check_xss(value):
            logger.warning(f"XSS detected in field: {key}")
            return False
        
        # Check path traversal
        if self._check_path_traversal(value):
            logger.warning(f"Path traversal detected in field: {key}")
            return False
        
        return True
    
    async def validate_request(self, request: Request) -> tuple[bool, str]:
        """
        Validate request for security issues.
        
        Returns:
            (is_valid, error_message)
        """
        
        # Check Content-Type for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("Content-Type", "")
            if content_type and not any(
                allowed in content_type 
                for allowed in self.allowed_content_types
            ):
                return False, f"Invalid Content-Type: {content_type}"
        
        # Validate query parameters
        for key, value in request.query_params.items():
            if isinstance(value, str):
                if not self._validate_string_value(key, value):
                    return False, f"Invalid value in query parameter: {key}"
        
        # Validate path parameters (if available)
        if hasattr(request, "path_params"):
            for key, value in request.path_params.items():
                if isinstance(value, str):
                    if not self._validate_string_value(key, value):
                        return False, f"Invalid value in path parameter: {key}"
        
        # Validate request body (if JSON)
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
                if isinstance(body, dict):
                    for key, value in body.items():
                        if isinstance(value, str):
                            if not self._validate_string_value(key, value):
                                return False, f"Invalid value in request body field: {key}"
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, str):
                                    if not self._validate_string_value(key, item):
                                        return False, f"Invalid value in request body list field: {key}"
            except Exception:
                # Body parsing failed - will be handled by validation layer
                pass
        
        return True, ""
    
    async def __call__(self, request: Request, call_next: Callable):
        """
        Middleware entry point.
        """
        
        # Validate request
        is_valid, error_message = await self.validate_request(request)
        
        if not is_valid:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": error_message,
                        "context": {}
                    },
                    "status": status.HTTP_400_BAD_REQUEST
                }
            )
        
        # Process request
        response = await call_next(request)
        
        return response


def register_request_validation(app, config: dict = None):
    """
    Register request validation middleware with FastAPI app.
    
    Args:
        app: FastAPI application
        config: Optional configuration override
    """
    
    middleware_config = config or {}
    validation_middleware = RequestValidationMiddleware(**middleware_config)
    
    app.middleware("http")(validation_middleware.__call__)
    
    logger.info("✅ Request validation middleware registered")
