"""
Request Logging Middleware

Comprehensive request/response logging for observability and debugging.
Logs request details, response details, timing metrics, and error information.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging
import time
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request/response logging middleware.
    
    Logs:
    - Request method, path, query parameters
    - Request headers (sanitized)
    - Response status code
    - Response time
    - Request body (if configured)
    - Response body (if configured)
    """
    
    def __init__(
        self,
        app,
        log_level: str = "INFO",
        log_request_body: bool = False,
        log_response_body: bool = False,
        log_headers: bool = True,
        sanitize_headers: list = None,
        skip_paths: list = None
    ):
        super().__init__(app)
        self.log_level = getattr(logging, log_level.upper())
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.log_headers = log_headers
        self.sanitize_headers = sanitize_headers or [
            "authorization",
            "password",
            "token",
            "api-key",
            "secret"
        ]
        self.skip_paths = skip_paths or ["/health", "/metrics", "/favicon.ico"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response details.
        """
        # Skip logging for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Log request
        self._log_request(request)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Record response time
            process_time = time.time() - start_time
            
            # Log response
            self._log_response(request, response, process_time)
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        except Exception as e:
            # Record error time
            process_time = time.time() - start_time
            
            # Log error
            self._log_error(request, e, process_time)
            raise
    
    def _log_request(self, request: Request):
        """
        Log incoming request details.
        """
        log_data = {
            "type": "request",
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        # Add headers if configured
        if self.log_headers:
            log_data["headers"] = self._sanitize_headers(dict(request.headers))
        
        # Log request body if configured
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            # Note: Reading request body consumes it, so we need to handle this carefully
            # For now, we'll skip body logging to avoid request consumption issues
            pass
        
        logger.log(self.log_level, json.dumps(log_data))
    
    def _log_response(self, request: Request, response: Response, process_time: float):
        """
        Log outgoing response details.
        """
        log_data = {
            "type": "response",
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2)
        }
        
        # Add response size if available (skip streaming responses)
        if hasattr(response, "body") and response.body:
            log_data["response_size_bytes"] = len(response.body)
        else:
            log_data["response_type"] = "streaming"
        
        # Add headers if configured
        if self.log_headers:
            log_data["headers"] = self._sanitize_headers(dict(response.headers))
        
        # Log response body if configured (skip streaming responses)
        if self.log_response_body and hasattr(response, "body") and response.body:
            try:
                # Try to parse as JSON for cleaner logging
                if "application/json" in response.headers.get("content-type", ""):
                    log_data["body"] = json.loads(response.body.decode())
                else:
                    log_data["body_preview"] = response.body[:500].decode() if len(response.body) > 500 else response.body.decode()
            except Exception:
                log_data["body_preview"] = "Unable to parse response body"
        
        logger.log(self.log_level, json.dumps(log_data))
    
    def _log_error(self, request: Request, error: Exception, process_time: float):
        """
        Log error details.
        """
        log_data = {
            "type": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "process_time_ms": round(process_time * 1000, 2)
        }
        
        logger.error(json.dumps(log_data), exc_info=True)
    
    def _sanitize_headers(self, headers: dict) -> dict:
        """
        Sanitize sensitive headers.
        """
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sanitize_headers:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized


def register_request_logging(app, config: dict = None):
    """
    Register request logging middleware with FastAPI app.
    
    Args:
        app: FastAPI application
        config: Optional configuration override
    """
    
    middleware_config = config or {}
    
    app.add_middleware(
        RequestLoggingMiddleware,
        **middleware_config
    )
    
    logger.info("✅ Request logging middleware registered")
