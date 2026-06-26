"""
Response Caching Middleware

Provides caching support for GET requests to reduce load and improve performance.
Supports Redis-backed caching with configurable TTL.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional, Dict
import json
import hashlib
import logging
import time

logger = logging.getLogger(__name__)


class CacheMiddleware(BaseHTTPMiddleware):
    """
    Response caching middleware for GET requests.
    
    Caches responses based on:
    - Request URL
    - Request query parameters
    - Request headers (if configured)
    
    Cache key format: cache:{method}:{url_hash}:{query_hash}
    """
    
    def __init__(
        self,
        app,
        cache_backend=None,
        default_ttl: int = 300,  # 5 minutes default TTL
        cacheable_methods: list = None,
        cacheable_status_codes: list = None,
        cache_key_headers: list = None,
        bypass_cache_header: str = "Cache-Control"
    ):
        super().__init__(app)
        self.cache_backend = cache_backend  # Redis client or None for in-memory
        self.default_ttl = default_ttl
        self.cacheable_methods = cacheable_methods or ["GET"]
        self.cacheable_status_codes = cacheable_status_codes or [200]
        self.cache_key_headers = cache_key_headers or []
        self.bypass_cache_header = bypass_cache_header
        
        # In-memory cache as fallback
        self.memory_cache: Dict[str, tuple] = {}  # key -> (response_data, expiry_time)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Handle request with caching logic.
        """
        # Only cache GET requests
        if request.method not in self.cacheable_methods:
            return await call_next(request)
        
        # Check if client requested no cache
        cache_control = request.headers.get("Cache-Control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get from cache
        cached_response = await self._get_from_cache(cache_key)
        if cached_response:
            logger.debug(f"Cache HIT: {cache_key}")
            return cached_response
        
        # Cache miss - process request
        logger.debug(f"Cache MISS: {cache_key}")
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code in self.cacheable_status_codes:
            await self._set_cache(cache_key, response, self.default_ttl)
        
        return response
    
    def _generate_cache_key(self, request: Request) -> str:
        """
        Generate cache key from request.
        """
        # Base key components
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        
        # Add headers if configured
        for header in self.cache_key_headers:
            header_value = request.headers.get(header, "")
            key_parts.append(f"{header}:{header_value}")
        
        # Hash the key
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()
        
        return f"cache:{request.method}:{request.url.path}:{key_hash}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Response]:
        """
        Get response from cache.
        """
        try:
            # Try Redis cache first
            if self.cache_backend:
                cached_data = self.cache_backend.get(cache_key)
                if cached_data:
                    return self._deserialize_response(cached_data)
            
            # Fallback to memory cache
            if cache_key in self.memory_cache:
                response_data, expiry_time = self.memory_cache[cache_key]
                if time.time() < expiry_time:
                    return self._deserialize_response(response_data)
                else:
                    del self.memory_cache[cache_key]
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        return None
    
    async def _set_cache(self, cache_key: str, response: Response, ttl: int):
        """
        Store response in cache.
        """
        try:
            # Serialize response
            response_data = self._serialize_response(response)
            
            # Skip if serialization failed (e.g., streaming response)
            if response_data is None:
                return
            
            # Try Redis cache first
            if self.cache_backend:
                self.cache_backend.setex(cache_key, ttl, response_data)
            
            # Fallback to memory cache
            expiry_time = time.time() + ttl
            self.memory_cache[cache_key] = (response_data, expiry_time)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
    
    def _serialize_response(self, response: Response) -> str:
        """
        Serialize response for storage.
        """
        # Skip streaming responses
        if hasattr(response, "body_iterator") or not hasattr(response, "body"):
            return None
        
        return json.dumps({
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.body.decode() if isinstance(response.body, bytes) else response.body
        })
    
    def _deserialize_response(self, data: str) -> Response:
        """
        Deserialize response from storage.
        """
        response_dict = json.loads(data)
        
        response = Response(
            content=response_dict["body"],
            status_code=response_dict["status_code"],
            headers=response_dict["headers"]
        )
        
        # Add cache header
        response.headers["X-Cache"] = "HIT"
        
        return response


def register_caching(app, cache_backend=None, config: dict = None):
    """
    Register caching middleware with FastAPI app.
    
    Args:
        app: FastAPI application
        cache_backend: Redis client or None for in-memory cache
        config: Optional configuration override
    """
    
    middleware_config = config or {}
    middleware_config["cache_backend"] = cache_backend
    
    app.add_middleware(
        CacheMiddleware,
        **middleware_config
    )
    
    logger.info("✅ Caching middleware registered")
