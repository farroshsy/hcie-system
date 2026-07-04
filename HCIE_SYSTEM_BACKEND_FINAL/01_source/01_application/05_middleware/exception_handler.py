"""
Global Exception Handler Middleware

Provides consistent error responses across all API endpoints.
Standardizes error format, prevents stack trace leakage in production.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Dict, Any
import logging
import traceback

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API exception with structured error response."""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Internal server error",
        error_code: str = "INTERNAL_ERROR",
        context: Dict[str, Any] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.context = context or {}
        super().__init__(detail)


class ValidationError(APIError):
    """Validation error with field-level details."""
    
    def __init__(self, detail: str = "Validation failed", errors: list = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
            context={"errors": errors or []}
        )


class AuthenticationError(APIError):
    """Authentication error."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(APIError):
    """Authorization error."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="AUTHORIZATION_ERROR"
        )


class NotFoundError(APIError):
    """Resource not found error."""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND"
        )


class RateLimitError(APIError):
    """Rate limit exceeded error."""
    
    def __init__(self, detail: str = "Rate limit exceeded", retry_after: int = None):
        context = {"retry_after": retry_after} if retry_after else {}
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT_EXCEEDED",
            context=context
        )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors with structured response."""
    
    logger.error(
        f"API Error: {exc.error_code} - {exc.detail} | "
        f"Path: {request.url.path} | Method: {request.method} | "
        f"Context: {exc.context}"
    )
    
    error_response = {
        "error": {
            "code": exc.error_code,
            "message": exc.detail,
            "context": exc.context
        },
        "status": exc.status_code
    }
    
    # Add retry_after header for rate limit errors
    headers = {}
    if exc.error_code == "RATE_LIMIT_EXCEEDED" and exc.context.get("retry_after"):
        headers["Retry-After"] = str(exc.context["retry_after"])
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=headers
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI validation errors."""
    
    logger.warning(
        f"Validation Error: {len(exc.errors())} errors | "
        f"Path: {request.url.path} | Method: {request.method}"
    )
    
    # Format validation errors
    formatted_errors = []
    for error in exc.errors():
        formatted_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    error_response = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "context": {
                "errors": formatted_errors
            }
        },
        "status": status.HTTP_422_UNPROCESSABLE_ENTITY
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail} | "
        f"Path: {request.url.path} | Method: {request.method}"
    )
    
    error_response = {
        "error": {
            "code": "HTTP_ERROR",
            "message": str(exc.detail),
            "context": {}
        },
        "status": exc.status_code
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    
    # Log full traceback in production for debugging
    logger.error(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)} | "
        f"Path: {request.url.path} | Method: {request.method}",
        exc_info=True
    )
    
    # Don't leak stack traces in production
    error_response = {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "context": {}  # Empty context in production
        },
        "status": status.HTTP_500_INTERNAL_SERVER_ERROR
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app."""
    
    # Custom API errors
    app.add_exception_handler(APIError, api_error_handler)
    
    # FastAPI validation errors
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    
    # Starlette HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("✅ Global exception handlers registered")
