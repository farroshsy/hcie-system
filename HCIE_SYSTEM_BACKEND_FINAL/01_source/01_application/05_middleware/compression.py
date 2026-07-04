"""
Response Compression Middleware

Compresses HTTP responses to reduce bandwidth and improve performance.
Supports gzip and brotli compression.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging
import gzip
import io

logger = logging.getLogger(__name__)


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Response compression middleware with configurable compression levels.
    
    Compresses responses for text-based content types:
    - application/json
    - text/html
    - text/plain
    - text/css
    - application/javascript
    """
    
    def __init__(
        self,
        app,
        minimum_size: int = 500,  # Only compress responses larger than 500 bytes
        compresslevel: int = 6,  # Compression level (0-9, 6 is default)
        compressible_types: list = None
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compresslevel = compresslevel
        self.compressible_types = compressible_types or [
            "application/json",
            "text/html",
            "text/plain",
            "text/css",
            "application/javascript",
            "text/xml",
            "application/xml"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Compress response if applicable.
        """
        response = await call_next(request)
        
        # Check if response should be compressed
        if not self._should_compress(request, response):
            return response
        
        # Compress response body
        compressed_body = self._compress_body(response.body)
        
        # Update response with compressed body and headers
        response.body = compressed_body
        response.headers["Content-Encoding"] = "gzip"
        response.headers["Content-Length"] = str(len(compressed_body))
        response.headers["X-Content-Encoded-By"] = "HCIE-Compression"
        
        return response
    
    def _should_compress(self, request: Request, response: Response) -> bool:
        """
        Determine if response should be compressed.
        """
        # Skip streaming responses
        if hasattr(response, "body_iterator") or not hasattr(response, "body"):
            return False
        
        # Check if client accepts gzip encoding
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return False
        
        # Check if response is large enough
        if len(response.body) < self.minimum_size:
            return False
        
        # Check if content type is compressible
        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type for ct in self.compressible_types):
            return False
        
        # Check if already compressed
        existing_encoding = response.headers.get("content-encoding", "")
        if existing_encoding:
            return False
        
        return True
    
    def _compress_body(self, body: bytes) -> bytes:
        """
        Compress response body using gzip.
        """
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=self.compresslevel) as gzip_file:
            gzip_file.write(body)
        return buffer.getvalue()


def register_compression(app, config: dict = None):
    """
    Register compression middleware with FastAPI app.
    
    Args:
        app: FastAPI application
        config: Optional configuration override
    """
    
    middleware_config = config or {}
    
    app.add_middleware(
        CompressionMiddleware,
        **middleware_config
    )
    
    logger.info("✅ Compression middleware registered")
