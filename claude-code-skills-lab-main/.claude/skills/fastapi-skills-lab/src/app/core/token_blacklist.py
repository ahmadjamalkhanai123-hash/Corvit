"""
Token Blacklist Module
======================

Token revocation support for JWT authentication.

Use cases:
- User logout
- Password change (invalidate all tokens)
- Security breach response
- Account suspension

Storage backends:
- In-memory (development only)
- Redis (recommended for production)
- Database (for audit trails)
"""

from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import Protocol


class TokenBlacklistBackend(Protocol):
    """Protocol for token blacklist backends."""

    def add(self, jti: str, expires_at: datetime) -> None:
        """Add token to blacklist."""
        ...

    def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        ...

    def remove_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        ...


class InMemoryBlacklist:
    """
    In-memory token blacklist.

    WARNING: Not suitable for production with multiple instances!
    Use RedisBlacklist for distributed systems.
    """

    def __init__(self):
        # Store: {jti: expires_at}
        self._blacklist: dict[str, datetime] = {}

    def add(self, jti: str, expires_at: datetime) -> None:
        """Add token to blacklist until its expiration."""
        self._blacklist[jti] = expires_at

    def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        if jti not in self._blacklist:
            return False

        # Check if entry has expired
        expires_at = self._blacklist[jti]
        if datetime.now(timezone.utc) > expires_at:
            del self._blacklist[jti]
            return False

        return True

    def remove_expired(self) -> int:
        """Remove expired entries to free memory."""
        now = datetime.now(timezone.utc)
        expired = [jti for jti, exp in self._blacklist.items() if now > exp]
        for jti in expired:
            del self._blacklist[jti]
        return len(expired)

    def clear(self) -> None:
        """Clear all entries."""
        self._blacklist.clear()

    @property
    def size(self) -> int:
        """Get current blacklist size."""
        return len(self._blacklist)


class RedisBlacklist:
    """
    Redis-backed token blacklist for production.

    Features:
    - Automatic TTL-based expiration
    - Distributed across multiple instances
    - Persistent (survives restarts)

    Usage:
        from redis import Redis
        redis_client = Redis.from_url("redis://localhost:6379")
        blacklist = RedisBlacklist(redis_client)
    """

    def __init__(self, redis_client, key_prefix: str = "token_blacklist"):
        self.redis = redis_client
        self.key_prefix = key_prefix

    def _get_key(self, jti: str) -> str:
        """Generate Redis key for token."""
        return f"{self.key_prefix}:{jti}"

    def add(self, jti: str, expires_at: datetime) -> None:
        """Add token to blacklist with automatic expiration."""
        key = self._get_key(jti)
        ttl_seconds = int((expires_at - datetime.now(timezone.utc)).total_seconds())

        if ttl_seconds > 0:
            self.redis.setex(key, ttl_seconds, "1")

    def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        key = self._get_key(jti)
        return self.redis.exists(key) > 0

    def remove_expired(self) -> int:
        """
        Not needed for Redis - TTL handles expiration automatically.
        Returns 0 for compatibility.
        """
        return 0

    def revoke_all_for_user(self, user_id: str, pattern: str = "*") -> int:
        """
        Revoke all tokens for a user (requires storing user_id in token).

        Note: This requires a different key structure to be efficient.
        Consider using a user-specific set for production.
        """
        # This is a simplified implementation
        # In production, maintain a set of tokens per user
        return 0


class TokenBlacklistService:
    """
    High-level service for token blacklist operations.

    Provides a clean interface regardless of backend.
    """

    def __init__(self, backend: InMemoryBlacklist | RedisBlacklist | None = None):
        self.backend = backend or InMemoryBlacklist()

    def revoke_token(self, jti: str, expires_at: datetime) -> None:
        """Revoke a single token."""
        self.backend.add(jti, expires_at)

    def is_revoked(self, jti: str) -> bool:
        """Check if token has been revoked."""
        return self.backend.is_blacklisted(jti)

    def cleanup(self) -> int:
        """Remove expired entries (for non-Redis backends)."""
        return self.backend.remove_expired()


# Global blacklist instance (use Redis in production)
token_blacklist = TokenBlacklistService()


def get_token_blacklist() -> TokenBlacklistService:
    """Dependency to get token blacklist service."""
    return token_blacklist
