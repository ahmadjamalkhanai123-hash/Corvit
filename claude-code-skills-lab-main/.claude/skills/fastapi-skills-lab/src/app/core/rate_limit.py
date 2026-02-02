"""
Rate Limiting Module
====================

Production-ready rate limiting for FastAPI applications.

Supports:
- In-memory rate limiting (single instance)
- Redis-based rate limiting (distributed)
- Per-user and per-IP limits
- Customizable windows and limits
"""

from collections import defaultdict
from datetime import datetime, timezone
import time
from typing import Callable

from fastapi import Request, HTTPException, status


class RateLimiter:
    """
    Sliding window rate limiter.

    For production with multiple instances, use Redis:
        from redis import Redis
        redis_client = Redis.from_url(settings.redis_url)
    """

    def __init__(
        self,
        requests_per_window: int = 60,
        window_seconds: int = 60
    ):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _clean_old_requests(self, key: str, now: float) -> None:
        """Remove requests outside the current window."""
        window_start = now - self.window_seconds
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]

    def is_allowed(self, key: str) -> tuple[bool, int, int]:
        """
        Check if request is allowed.

        Returns:
            tuple: (is_allowed, remaining_requests, reset_time_seconds)
        """
        now = time.time()
        self._clean_old_requests(key, now)

        current_count = len(self.requests[key])
        remaining = max(0, self.requests_per_window - current_count)

        # Calculate reset time
        if self.requests[key]:
            oldest = min(self.requests[key])
            reset_time = int(oldest + self.window_seconds - now)
        else:
            reset_time = self.window_seconds

        if current_count >= self.requests_per_window:
            return False, 0, reset_time

        self.requests[key].append(now)
        return True, remaining - 1, reset_time

    def get_key(self, request: Request, user_id: str | None = None) -> str:
        """Generate rate limit key from request."""
        if user_id:
            return f"user:{user_id}"
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"


class RedisRateLimiter:
    """
    Redis-based rate limiter for distributed systems.

    Usage:
        from redis import Redis
        redis_client = Redis.from_url("redis://localhost:6379")
        limiter = RedisRateLimiter(redis_client)
    """

    def __init__(
        self,
        redis_client,
        requests_per_window: int = 60,
        window_seconds: int = 60,
        key_prefix: str = "ratelimit"
    ):
        self.redis = redis_client
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

    def is_allowed(self, key: str) -> tuple[bool, int, int]:
        """Check if request is allowed using Redis."""
        redis_key = f"{self.key_prefix}:{key}"
        now = time.time()

        pipe = self.redis.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(redis_key, 0, now - self.window_seconds)

        # Count current entries
        pipe.zcard(redis_key)

        # Add new entry if allowed (done separately)
        results = pipe.execute()
        current_count = results[1]

        remaining = max(0, self.requests_per_window - current_count)

        if current_count >= self.requests_per_window:
            # Get TTL for reset time
            ttl = self.redis.ttl(redis_key)
            return False, 0, ttl if ttl > 0 else self.window_seconds

        # Add new request
        pipe = self.redis.pipeline()
        pipe.zadd(redis_key, {str(now): now})
        pipe.expire(redis_key, self.window_seconds)
        pipe.execute()

        return True, remaining - 1, self.window_seconds


def rate_limit(
    limiter: RateLimiter,
    key_func: Callable[[Request], str] | None = None
):
    """
    Dependency for rate limiting individual endpoints.

    Usage:
        @app.get("/api/data")
        async def get_data(
            _: None = Depends(rate_limit(limiter, key_func=lambda r: r.client.host))
        ):
            return {"data": "value"}
    """
    async def dependency(request: Request):
        if key_func:
            key = key_func(request)
        else:
            key = limiter.get_key(request)

        allowed, remaining, reset = limiter.is_allowed(key)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(limiter.requests_per_window),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                    "Retry-After": str(reset)
                }
            )

        # Store for response headers
        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_reset = reset

    return dependency


# Pre-configured limiters for common use cases
default_limiter = RateLimiter(requests_per_window=60, window_seconds=60)
strict_limiter = RateLimiter(requests_per_window=10, window_seconds=60)
auth_limiter = RateLimiter(requests_per_window=5, window_seconds=300)  # 5 per 5 min
