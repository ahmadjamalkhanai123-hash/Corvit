"""
Rate Limit Middleware
=====================

Global rate limiting middleware for FastAPI applications.

Features:
- Per-IP rate limiting
- Per-user rate limiting (when authenticated)
- Customizable limits and windows
- Rate limit headers in responses
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.rate_limit import RateLimiter, default_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that applies rate limiting to all requests.

    Usage:
        from fastapi import FastAPI
        from src.app.middleware.rate_limit import RateLimitMiddleware

        app = FastAPI()
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_window=100,
            window_seconds=60
        )
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_window: int = 60,
        window_seconds: int = 60,
        limiter: RateLimiter | None = None,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.limiter = limiter or RateLimiter(
            requests_per_window=requests_per_window,
            window_seconds=window_seconds
        )
        self.exclude_paths = set(exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json"])

    def _get_client_key(self, request: Request) -> str:
        """Extract client identifier for rate limiting."""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to client IP
        client_ip = "unknown"
        if request.client:
            client_ip = request.client.host

        # Check for proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (original client)
            client_ip = forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            client_ip = real_ip

        return f"ip:{client_ip}"

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Get client key
        client_key = self._get_client_key(request)

        # Check rate limit
        allowed, remaining, reset = self.limiter.is_allowed(client_key)

        if not allowed:
            return Response(
                content='{"detail": "Rate limit exceeded. Please try again later."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(self.limiter.requests_per_window),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                    "Retry-After": str(reset),
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.limiter.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)

        return response


class TieredRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting with different tiers based on path patterns.

    Example:
        middleware = TieredRateLimitMiddleware(
            app,
            tiers={
                "/api/v1/auth/": {"requests": 10, "window": 300},  # Auth: 10/5min
                "/api/v1/upload": {"requests": 5, "window": 60},   # Upload: 5/min
                "/api/": {"requests": 100, "window": 60},          # API: 100/min
            },
            default_requests=60,
            default_window=60
        )
    """

    def __init__(
        self,
        app: ASGIApp,
        tiers: dict[str, dict] | None = None,
        default_requests: int = 60,
        default_window: int = 60,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.tiers = tiers or {}
        self.default_limiter = RateLimiter(default_requests, default_window)
        self.tier_limiters: dict[str, RateLimiter] = {}
        self.exclude_paths = set(exclude_paths or ["/health", "/docs"])

        # Create limiters for each tier
        for path_prefix, config in self.tiers.items():
            self.tier_limiters[path_prefix] = RateLimiter(
                requests_per_window=config.get("requests", default_requests),
                window_seconds=config.get("window", default_window)
            )

    def _get_limiter_for_path(self, path: str) -> RateLimiter:
        """Get the appropriate limiter for a path."""
        # Check tiers in order (longest prefix match wins)
        for path_prefix in sorted(self.tier_limiters.keys(), key=len, reverse=True):
            if path.startswith(path_prefix):
                return self.tier_limiters[path_prefix]
        return self.default_limiter

    def _get_client_key(self, request: Request) -> str:
        """Extract client identifier."""
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        limiter = self._get_limiter_for_path(request.url.path)
        client_key = self._get_client_key(request)

        allowed, remaining, reset = limiter.is_allowed(client_key)

        if not allowed:
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(limiter.requests_per_window),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                    "Retry-After": str(reset),
                }
            )

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(limiter.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)

        return response
