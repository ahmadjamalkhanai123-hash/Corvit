"""
Auth Schemas
============

Pydantic schemas for authentication and authorization.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# Token Schemas
class Token(BaseModel):
    """OAuth2 token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None
    scope: str | None = None


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str
    exp: datetime
    type: str = "access"
    jti: str | None = None
    scopes: list[str] = []


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


# Login Schemas
class LoginRequest(BaseModel):
    """Login request."""
    username: str
    password: str
    scopes: list[str] = []


class LoginResponse(BaseModel):
    """Login response with tokens."""
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int


# OAuth Schemas
class OAuthCallback(BaseModel):
    """OAuth callback data."""
    code: str
    state: str


class OAuthUserInfo(BaseModel):
    """Normalized OAuth user info."""
    provider: str
    provider_user_id: str
    email: str | None = None
    name: str | None = None
    picture: str | None = None


# Role Schemas
class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., min_length=2, max_length=50)
    description: str | None = None


class RoleCreate(RoleBase):
    """Create role request."""
    permissions: list[str] = []


class RoleUpdate(BaseModel):
    """Update role request."""
    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None


class RoleResponse(RoleBase):
    """Role response."""
    id: int
    permissions: list[str]
    is_system: bool

    class Config:
        from_attributes = True


# Permission Schemas
class PermissionResponse(BaseModel):
    """Permission response."""
    id: int
    name: str
    description: str | None
    resource: str
    action: str

    class Config:
        from_attributes = True
