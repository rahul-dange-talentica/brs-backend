"""Rate limiting middleware for API endpoints."""

import time
import json
import asyncio
from collections import defaultdict, deque
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.schemas.common import create_error_response
from app.core.exceptions import RateLimitExceededError


logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.
    
    In production, this should be replaced with Redis or another distributed cache
    for scalability across multiple application instances.
    """
    
    def __init__(self):
        # Store request timestamps for each identifier
        # Format: {identifier: deque([timestamp1, timestamp2, ...])}
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
        # Store rate limit info for each identifier
        # Format: {identifier: (limit, window_seconds, reset_time)}
        self.limits: Dict[str, Tuple[int, int, float]] = {}
        self._lock = asyncio.Lock()
    
    async def is_allowed(
        self, 
        identifier: str, 
        limit: int, 
        window_seconds: int
    ) -> Tuple[bool, int, float]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            identifier: Unique identifier (user_id, IP, etc.)
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, remaining_requests, reset_time)
        """
        async with self._lock:
            current_time = time.time()
            window_start = current_time - window_seconds
            
            # Get or create request history for identifier
            request_times = self.requests[identifier]
            
            # Remove expired requests (outside current window)
            while request_times and request_times[0] < window_start:
                request_times.popleft()
            
            # Count current requests in window
            current_requests = len(request_times)
            
            # Calculate reset time (when oldest request in window expires)
            reset_time = request_times[0] + window_seconds if request_times else current_time + window_seconds
            
            # Check if limit exceeded
            if current_requests >= limit:
                # Store limit info for headers
                self.limits[identifier] = (limit, window_seconds, reset_time)
                return False, 0, reset_time
            
            # Allow request and record timestamp
            request_times.append(current_time)
            remaining = limit - (current_requests + 1)
            
            # Store limit info for headers
            self.limits[identifier] = (limit, window_seconds, reset_time)
            
            return True, remaining, reset_time
    
    async def get_limit_info(self, identifier: str) -> Optional[Tuple[int, int, float]]:
        """Get current limit information for identifier."""
        return self.limits.get(identifier)
    
    async def cleanup_expired(self, max_age_seconds: int = 3600):
        """Clean up expired entries to prevent memory leaks."""
        async with self._lock:
            current_time = time.time()
            expired_identifiers = []
            
            for identifier, request_times in self.requests.items():
                # Remove old requests
                while request_times and request_times[0] < current_time - max_age_seconds:
                    request_times.popleft()
                
                # Mark identifier for cleanup if no recent requests
                if not request_times:
                    expired_identifiers.append(identifier)
            
            # Clean up empty entries
            for identifier in expired_identifiers:
                del self.requests[identifier]
                self.limits.pop(identifier, None)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with different limits for authenticated/anonymous users.
    """
    
    def __init__(
        self,
        app,
        authenticated_limit: int = 100,
        anonymous_limit: int = 20,
        window_seconds: int = 60,
        cleanup_interval: int = 300  # 5 minutes
    ):
        super().__init__(app)
        self.authenticated_limit = authenticated_limit
        self.anonymous_limit = anonymous_limit
        self.window_seconds = window_seconds
        self.rate_limiter = InMemoryRateLimiter()
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
        
        # Paths to exclude from rate limiting
        self.excluded_paths = {
            "/health",
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/openapi.json",
            "/api/v1/monitoring/health/liveness",
            "/api/v1/monitoring/health/readiness"
        }
    
    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client.
        
        Priority:
        1. Authenticated user ID (from token)
        2. X-Forwarded-For header (for proxied requests)
        3. Client IP address
        """
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Get IP address (considering proxy headers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = getattr(request.client, 'host', 'unknown')
        
        return f"ip:{client_ip}"
    
    def _is_authenticated_request(self, request: Request) -> bool:
        """Check if request is from authenticated user."""
        return hasattr(request.state, 'user_id') and request.state.user_id is not None
    
    def _should_apply_rate_limit(self, request: Request) -> bool:
        """Determine if rate limiting should be applied to this request."""
        path = request.url.path
        
        # Skip rate limiting for excluded paths
        if path in self.excluded_paths:
            return False
        
        # Skip rate limiting for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return False
        
        return True
    
    async def _cleanup_if_needed(self):
        """Perform cleanup if enough time has passed."""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            await self.rate_limiter.cleanup_expired()
            self.last_cleanup = current_time
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        
        # Skip rate limiting for certain paths
        if not self._should_apply_rate_limit(request):
            return await call_next(request)
        
        # Periodic cleanup
        await self._cleanup_if_needed()
        
        # Get client identifier and determine rate limit
        identifier = self._get_client_identifier(request)
        is_authenticated = self._is_authenticated_request(request)
        limit = self.authenticated_limit if is_authenticated else self.anonymous_limit
        
        # Check rate limit
        try:
            is_allowed, remaining, reset_time = await self.rate_limiter.is_allowed(
                identifier, limit, self.window_seconds
            )
            
            if not is_allowed:
                # Rate limit exceeded
                logger.warning(
                    f"Rate limit exceeded for {identifier} on {request.method} {request.url.path}",
                    extra={
                        "identifier": identifier,
                        "path": request.url.path,
                        "method": request.method,
                        "limit": limit,
                        "window_seconds": self.window_seconds
                    }
                )
                
                # Calculate retry-after header
                retry_after = max(0, int(reset_time - time.time()))
                
                # Create rate limit error response
                error_response = create_error_response(
                    message=f"Rate limit exceeded: {limit} requests per {self.window_seconds} seconds",
                    errors={
                        "code": "RATE_LIMIT_EXCEEDED",
                        "limit": limit,
                        "window_seconds": self.window_seconds,
                        "retry_after_seconds": retry_after,
                        "reset_time": datetime.fromtimestamp(reset_time).isoformat()
                    }
                )
                
                response = JSONResponse(
                    status_code=429,
                    content=error_response,
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(reset_time)),
                        "Retry-After": str(retry_after)
                    }
                )
                return response
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to successful responses
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(reset_time))
            response.headers["X-RateLimit-Window"] = str(self.window_seconds)
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiter error: {str(e)}", exc_info=True)
            # If rate limiter fails, allow the request but log the error
            return await call_next(request)


class EnhancedRateLimitMiddleware(RateLimitMiddleware):
    """
    Enhanced rate limiter with endpoint-specific limits and burst protection.
    """
    
    def __init__(
        self,
        app,
        authenticated_limit: int = 100,
        anonymous_limit: int = 20,
        window_seconds: int = 60,
        endpoint_limits: Optional[Dict[str, Dict[str, int]]] = None,
        burst_limit: Optional[int] = None,
        burst_window: int = 10
    ):
        super().__init__(app, authenticated_limit, anonymous_limit, window_seconds)
        
        # Endpoint-specific limits
        # Format: {"/api/v1/auth/login": {"authenticated": 10, "anonymous": 5}}
        self.endpoint_limits = endpoint_limits or {
            "/api/v1/auth/login": {"authenticated": 10, "anonymous": 5},
            "/api/v1/auth/register": {"authenticated": 5, "anonymous": 3},
            "/api/v1/reviews": {"authenticated": 20, "anonymous": 5},
            "/api/v1/books": {"authenticated": 50, "anonymous": 10}
        }
        
        # Burst protection (very short window)
        self.burst_limit = burst_limit or 10
        self.burst_window = burst_window
    
    def _get_endpoint_limit(self, request: Request, is_authenticated: bool) -> int:
        """Get rate limit for specific endpoint."""
        path = request.url.path
        
        # Check for endpoint-specific limits
        if path in self.endpoint_limits:
            limit_type = "authenticated" if is_authenticated else "anonymous"
            return self.endpoint_limits[path].get(limit_type, 
                self.authenticated_limit if is_authenticated else self.anonymous_limit)
        
        # Use default limits
        return self.authenticated_limit if is_authenticated else self.anonymous_limit
    
    async def dispatch(self, request: Request, call_next):
        """Process request with enhanced rate limiting."""
        
        # Skip rate limiting for certain paths
        if not self._should_apply_rate_limit(request):
            return await call_next(request)
        
        # Periodic cleanup
        await self._cleanup_if_needed()
        
        # Get client identifier and determine rate limits
        identifier = self._get_client_identifier(request)
        is_authenticated = self._is_authenticated_request(request)
        
        # Check burst limit first (short window)
        burst_allowed, _, burst_reset = await self.rate_limiter.is_allowed(
            f"burst:{identifier}", self.burst_limit, self.burst_window
        )
        
        if not burst_allowed:
            logger.warning(f"Burst limit exceeded for {identifier}")
            retry_after = max(0, int(burst_reset - time.time()))
            
            error_response = create_error_response(
                message=f"Too many requests too quickly. Burst limit: {self.burst_limit} requests per {self.burst_window} seconds",
                errors={
                    "code": "BURST_LIMIT_EXCEEDED", 
                    "burst_limit": self.burst_limit,
                    "burst_window": self.burst_window,
                    "retry_after_seconds": retry_after
                }
            )
            
            return JSONResponse(
                status_code=429,
                content=error_response,
                headers={"Retry-After": str(retry_after)}
            )
        
        # Check regular rate limit
        regular_limit = self._get_endpoint_limit(request, is_authenticated)
        is_allowed, remaining, reset_time = await self.rate_limiter.is_allowed(
            identifier, regular_limit, self.window_seconds
        )
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {identifier} on {request.url.path}")
            retry_after = max(0, int(reset_time - time.time()))
            
            error_response = create_error_response(
                message=f"Rate limit exceeded: {regular_limit} requests per {self.window_seconds} seconds",
                errors={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "limit": regular_limit,
                    "window_seconds": self.window_seconds,
                    "retry_after_seconds": retry_after
                }
            )
            
            return JSONResponse(
                status_code=429,
                content=error_response,
                headers={
                    "X-RateLimit-Limit": str(regular_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time)),
                    "Retry-After": str(retry_after)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(regular_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        response.headers["X-RateLimit-Window"] = str(self.window_seconds)
        response.headers["X-BurstLimit-Limit"] = str(self.burst_limit)
        response.headers["X-BurstLimit-Window"] = str(self.burst_window)
        
        return response
