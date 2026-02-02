"""
API Key Management Module
=========================

Production-ready API key authentication for FastAPI.

Features:
- Secure key generation with prefixes
- SHA-256 hashing for storage
- Expiration and scope support
- Usage tracking
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated
import secrets
import hashlib

from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel


class APIKeyData(BaseModel):
    """API key metadata."""
    key_id: str
    owner: str
    name: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None
    is_active: bool = True


class APIKeyCreate(BaseModel):
    """Request model for creating API key."""
    name: str
    scopes: list[str] = ["read"]
    expires_in_days: int | None = 365


class APIKeyResponse(BaseModel):
    """Response after creating API key (only time full key is shown)."""
    key: str  # Full key - only shown once!
    key_id: str
    name: str
    scopes: list[str]
    expires_at: datetime | None


class APIKeyManager:
    """
    Manages API key lifecycle.

    In production, use a database instead of in-memory storage.
    """

    def __init__(self, prefix: str = "sk"):
        self.prefix = prefix
        # In production: use database
        self._keys: dict[str, APIKeyData] = {}

    def generate_key(
        self,
        owner: str,
        name: str,
        scopes: list[str] | None = None,
        expires_in_days: int | None = 365
    ) -> tuple[str, APIKeyData]:
        """
        Generate a new API key.

        Returns:
            tuple: (full_key, key_data)
            IMPORTANT: full_key is only returned once, store it securely!
        """
        # Generate random key
        random_part = secrets.token_hex(24)
        full_key = f"{self.prefix}_{random_part}"

        # Create key ID (first 8 chars of hash for identification)
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        key_id = f"{self.prefix}_{key_hash[:8]}"

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        # Create key data
        key_data = APIKeyData(
            key_id=key_id,
            owner=owner,
            name=name,
            scopes=scopes or ["read"],
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            last_used_at=None,
            is_active=True
        )

        # Store with hash as key
        self._keys[key_hash] = key_data

        return full_key, key_data

    def verify_key(self, api_key: str) -> APIKeyData | None:
        """
        Verify an API key and return its data.

        Returns None if key is invalid, expired, or inactive.
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_data = self._keys.get(key_hash)

        if not key_data:
            return None

        if not key_data.is_active:
            return None

        if key_data.expires_at and datetime.now(timezone.utc) > key_data.expires_at:
            return None

        # Update last used
        key_data.last_used_at = datetime.now(timezone.utc)

        return key_data

    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key by its ID."""
        for key_hash, data in self._keys.items():
            if data.key_id == key_id:
                data.is_active = False
                return True
        return False

    def list_keys(self, owner: str) -> list[APIKeyData]:
        """List all keys for an owner."""
        return [
            data for data in self._keys.values()
            if data.owner == owner and data.is_active
        ]

    def has_scope(self, key_data: APIKeyData, required_scope: str) -> bool:
        """Check if key has required scope."""
        # Handle scope hierarchy: admin > write > read
        scope_hierarchy = {"read": 0, "write": 1, "admin": 2}

        if required_scope not in scope_hierarchy:
            return required_scope in key_data.scopes

        required_level = scope_hierarchy[required_scope]

        for scope in key_data.scopes:
            if scope in scope_hierarchy:
                if scope_hierarchy[scope] >= required_level:
                    return True

        return False


# Global API key manager instance
api_key_manager = APIKeyManager()


# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def get_api_key(
    header_key: str | None = Security(api_key_header),
    query_key: str | None = Security(api_key_query)
) -> APIKeyData:
    """
    Dependency to validate API key from header or query parameter.

    Usage:
        @app.get("/api/data")
        async def get_data(key_data: APIKeyData = Depends(get_api_key)):
            return {"owner": key_data.owner}
    """
    api_key = header_key or query_key

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide via X-API-Key header or api_key query parameter."
        )

    key_data = api_key_manager.verify_key(api_key)

    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired API key"
        )

    return key_data


def require_scope(scope: str):
    """
    Dependency factory for scope-based authorization.

    Usage:
        @app.delete("/api/data/{id}")
        async def delete_data(
            id: int,
            key_data: APIKeyData = Depends(require_scope("admin"))
        ):
            ...
    """
    async def dependency(key_data: APIKeyData = Depends(get_api_key)) -> APIKeyData:
        if not api_key_manager.has_scope(key_data, scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires '{scope}' scope"
            )
        return key_data

    return dependency


# Convenience dependencies
require_read = require_scope("read")
require_write = require_scope("write")
require_admin = require_scope("admin")
