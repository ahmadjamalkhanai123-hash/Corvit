"""
LESSON 21: Fine-Grained Permission Scopes
=========================================

Implement OAuth2-style permission scopes for APIs.

Key Concepts:
- Scope definition and hierarchy
- Token-based scope assignment
- Scope validation dependencies
- API documentation with scopes
- Client credential scopes
- Scope inheritance patterns

To run this lesson:
    cd fastapi-skills-lab
    uv run uvicorn lessons.03_advanced.09_permission_scopes:app --reload

Then visit: http://127.0.0.1:8000/docs
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated
import secrets

from fastapi import FastAPI, Depends, HTTPException, status, Security, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from pydantic import BaseModel
from jose import jwt, JWTError


# =============================================================================
# SECTION 1: Scope Definitions
# =============================================================================

"""
Scopes define what actions a token can perform.
Format: resource.action or resource:action

Common patterns:
- read, write, delete (basic CRUD)
- admin (full access)
- resource:read, resource:write (resource-specific)
"""

class Scope(str, Enum):
    """All available API scopes."""

    # User scopes
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"

    # Profile scopes (for user's own data)
    PROFILE_READ = "profile:read"
    PROFILE_WRITE = "profile:write"

    # Items scopes
    ITEMS_READ = "items:read"
    ITEMS_WRITE = "items:write"
    ITEMS_DELETE = "items:delete"

    # Admin scopes
    ADMIN = "admin"

    # Meta scopes
    OPENID = "openid"
    EMAIL = "email"
    OFFLINE_ACCESS = "offline_access"


# Scope descriptions for API documentation
SCOPE_DESCRIPTIONS = {
    Scope.USERS_READ: "Read user information",
    Scope.USERS_WRITE: "Create and update users",
    Scope.USERS_DELETE: "Delete users",
    Scope.PROFILE_READ: "Read your own profile",
    Scope.PROFILE_WRITE: "Update your own profile",
    Scope.ITEMS_READ: "Read items",
    Scope.ITEMS_WRITE: "Create and update items",
    Scope.ITEMS_DELETE: "Delete items",
    Scope.ADMIN: "Full administrative access",
    Scope.OPENID: "OpenID Connect authentication",
    Scope.EMAIL: "Access to email address",
    Scope.OFFLINE_ACCESS: "Refresh token access",
}


# Scope hierarchy (higher scopes include lower ones)
SCOPE_HIERARCHY = {
    Scope.ADMIN: [
        Scope.USERS_READ, Scope.USERS_WRITE, Scope.USERS_DELETE,
        Scope.ITEMS_READ, Scope.ITEMS_WRITE, Scope.ITEMS_DELETE,
        Scope.PROFILE_READ, Scope.PROFILE_WRITE,
    ],
    Scope.USERS_WRITE: [Scope.USERS_READ],
    Scope.USERS_DELETE: [Scope.USERS_READ],
    Scope.ITEMS_WRITE: [Scope.ITEMS_READ],
    Scope.ITEMS_DELETE: [Scope.ITEMS_READ],
    Scope.PROFILE_WRITE: [Scope.PROFILE_READ],
}


def expand_scopes(scopes: list[str]) -> set[str]:
    """Expand scopes to include inherited scopes."""
    expanded = set(scopes)

    for scope in scopes:
        try:
            scope_enum = Scope(scope)
            inherited = SCOPE_HIERARCHY.get(scope_enum, [])
            expanded.update(s.value for s in inherited)
        except ValueError:
            pass  # Unknown scope, skip hierarchy

    return expanded


def scope_satisfies(granted: set[str], required: str) -> bool:
    """Check if granted scopes satisfy required scope."""
    # Direct match
    if required in granted:
        return True

    # Admin has all scopes
    if Scope.ADMIN.value in granted:
        return True

    # Check expanded scopes
    expanded = expand_scopes(list(granted))
    return required in expanded


# =============================================================================
# SECTION 2: Token Management with Scopes
# =============================================================================

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={s.value: SCOPE_DESCRIPTIONS.get(s, "") for s in Scope}
)


class Token(BaseModel):
    """OAuth2 token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str
    refresh_token: str | None = None


class TokenData(BaseModel):
    """Decoded token data."""
    sub: str
    scopes: list[str]
    exp: datetime


def create_token(
    subject: str,
    scopes: list[str],
    expires_delta: timedelta = timedelta(hours=1)
) -> str:
    """Create JWT token with scopes."""
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": subject,
        "scopes": scopes,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> TokenData:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(
            sub=payload["sub"],
            scopes=payload.get("scopes", []),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# =============================================================================
# SECTION 3: User Database with Allowed Scopes
# =============================================================================

class User(BaseModel):
    """User model with allowed scopes."""
    username: str
    email: str
    hashed_password: str
    allowed_scopes: list[str]  # Maximum scopes user can request
    is_active: bool = True


# Simulated user database
users_db = {
    "admin": User(
        username="admin",
        email="admin@example.com",
        hashed_password="hashed_admin123",
        allowed_scopes=[Scope.ADMIN.value]
    ),
    "manager": User(
        username="manager",
        email="manager@example.com",
        hashed_password="hashed_manager123",
        allowed_scopes=[
            Scope.USERS_READ.value, Scope.USERS_WRITE.value,
            Scope.ITEMS_READ.value, Scope.ITEMS_WRITE.value,
            Scope.PROFILE_READ.value, Scope.PROFILE_WRITE.value,
        ]
    ),
    "user": User(
        username="user",
        email="user@example.com",
        hashed_password="hashed_user123",
        allowed_scopes=[
            Scope.PROFILE_READ.value, Scope.PROFILE_WRITE.value,
            Scope.ITEMS_READ.value,
        ]
    )
}


# =============================================================================
# SECTION 4: Scope Validation Dependencies
# =============================================================================

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
) -> tuple[User, TokenData]:
    """
    Get current user and validate scopes.

    Uses FastAPI's SecurityScopes for automatic scope checking.
    """
    # Decode token
    token_data = decode_token(token)

    # Get user
    user = users_db.get(token_data.sub)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Check required scopes
    token_scopes = set(token_data.scopes)

    for scope in security_scopes.scopes:
        if not scope_satisfies(token_scopes, scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{scope}' required",
                headers={
                    "WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'
                }
            )

    return user, token_data


def require_scope(*required_scopes: str):
    """
    Dependency factory for scope-based authorization.

    Usage:
        @app.get("/admin/users")
        def list_users(
            auth: tuple = Depends(require_scope("users:read"))
        ):
            user, token_data = auth
            ...
    """
    async def dependency(
        token: str = Depends(oauth2_scheme)
    ) -> tuple[User, TokenData]:
        token_data = decode_token(token)
        user = users_db.get(token_data.sub)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        token_scopes = set(token_data.scopes)

        for scope in required_scopes:
            if not scope_satisfies(token_scopes, scope):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Scope '{scope}' required"
                )

        return user, token_data

    return dependency


# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="Permission Scopes API",
    description="OAuth2-style scoped permissions",
    version="1.0.0"
)


# =============================================================================
# ENDPOINTS: Authentication
# =============================================================================

@app.post("/auth/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 token endpoint with scope support.

    Request specific scopes in the 'scope' field.
    """
    # Validate user
    user = users_db.get(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Parse requested scopes
    requested_scopes = form_data.scopes if form_data.scopes else []

    # Validate requested scopes against user's allowed scopes
    granted_scopes = []
    user_allowed = set(user.allowed_scopes)

    # Admin can grant any scope
    if Scope.ADMIN.value in user_allowed:
        granted_scopes = requested_scopes if requested_scopes else [Scope.ADMIN.value]
    else:
        for scope in requested_scopes:
            if scope_satisfies(user_allowed, scope):
                granted_scopes.append(scope)

        # If no scopes requested, grant all allowed
        if not requested_scopes:
            granted_scopes = user.allowed_scopes

    # Create token
    expires_delta = timedelta(hours=1)
    access_token = create_token(user.username, granted_scopes, expires_delta)

    # Create refresh token if offline_access requested
    refresh_token = None
    if Scope.OFFLINE_ACCESS.value in granted_scopes:
        refresh_token = create_token(
            user.username,
            [Scope.OFFLINE_ACCESS.value],
            timedelta(days=7)
        )

    return Token(
        access_token=access_token,
        expires_in=int(expires_delta.total_seconds()),
        scope=" ".join(granted_scopes),
        refresh_token=refresh_token
    )


@app.get("/auth/scopes")
async def list_available_scopes():
    """List all available scopes with descriptions."""
    return {
        "scopes": {s.value: SCOPE_DESCRIPTIONS.get(s, "") for s in Scope}
    }


# =============================================================================
# ENDPOINTS: Profile (requires profile:* scopes)
# =============================================================================

@app.get("/profile")
async def get_profile(
    auth: tuple = Security(get_current_user, scopes=["profile:read"])
):
    """Get current user's profile (requires profile:read)."""
    user, token_data = auth
    return {
        "username": user.username,
        "email": user.email,
        "granted_scopes": token_data.scopes
    }


@app.put("/profile")
async def update_profile(
    data: dict,
    auth: tuple = Security(get_current_user, scopes=["profile:write"])
):
    """Update profile (requires profile:write)."""
    user, token_data = auth
    return {
        "message": "Profile updated",
        "username": user.username,
        "updated_fields": list(data.keys())
    }


# =============================================================================
# ENDPOINTS: Users (requires users:* scopes)
# =============================================================================

@app.get("/users")
async def list_users(
    auth: tuple = Security(get_current_user, scopes=["users:read"])
):
    """List all users (requires users:read)."""
    user, _ = auth
    return {
        "users": [
            {"username": u.username, "email": u.email}
            for u in users_db.values()
        ]
    }


@app.post("/users")
async def create_user(
    new_user: dict,
    auth: tuple = Security(get_current_user, scopes=["users:write"])
):
    """Create user (requires users:write)."""
    return {"message": "User created", "data": new_user}


@app.delete("/users/{username}")
async def delete_user(
    username: str,
    auth: tuple = Security(get_current_user, scopes=["users:delete"])
):
    """Delete user (requires users:delete)."""
    return {"message": f"User {username} deleted"}


# =============================================================================
# ENDPOINTS: Items (requires items:* scopes)
# =============================================================================

items_db = [
    {"id": 1, "title": "Item 1"},
    {"id": 2, "title": "Item 2"},
]


@app.get("/items")
async def list_items(
    auth: tuple = Security(get_current_user, scopes=["items:read"])
):
    """List items (requires items:read)."""
    return {"items": items_db}


@app.post("/items")
async def create_item(
    item: dict,
    auth: tuple = Security(get_current_user, scopes=["items:write"])
):
    """Create item (requires items:write)."""
    user, _ = auth
    new_item = {"id": len(items_db) + 1, **item, "created_by": user.username}
    items_db.append(new_item)
    return new_item


@app.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    auth: tuple = Security(get_current_user, scopes=["items:delete"])
):
    """Delete item (requires items:delete)."""
    return {"message": f"Item {item_id} deleted"}


# =============================================================================
# ENDPOINTS: Admin (requires admin scope)
# =============================================================================

@app.get("/admin/dashboard")
async def admin_dashboard(
    auth: tuple = Security(get_current_user, scopes=["admin"])
):
    """Admin dashboard (requires admin scope)."""
    return {
        "users_count": len(users_db),
        "items_count": len(items_db),
        "message": "Full admin access"
    }


# =============================================================================
# KEY CONCEPTS SUMMARY
# =============================================================================

"""
KEY CONCEPTS:
=============

1. SCOPE DEFINITIONS:
   - Use resource:action format
   - Define as enum for type safety
   - Include descriptions for documentation

2. SCOPE HIERARCHY:
   - Higher scopes include lower ones
   - admin includes all scopes
   - write includes read

3. TOKEN SCOPES:
   - Scopes stored in JWT payload
   - User requests scopes during login
   - Server limits to allowed scopes

4. SCOPE VALIDATION:
   - FastAPI's Security() with scopes parameter
   - SecurityScopes for automatic checking
   - WWW-Authenticate header for scope errors

5. SCOPE GRANTING:
   - User has max allowed scopes
   - Token has granted scopes (<= allowed)
   - Endpoints require specific scopes

BEST PRACTICES:
===============
- Define scopes granularly
- Use hierarchy to reduce complexity
- Document scope requirements in OpenAPI
- Return required scopes in error responses
- Support scope downgrading for tokens
"""


# =============================================================================
# EXERCISES
# =============================================================================

"""
EXERCISE 1: Implement Scope Downgrade
-------------------------------------
Add endpoint to create a new token with fewer scopes:
1. POST /auth/downgrade - Request subset of current scopes
2. Validate new scopes are subset of current
3. Return new token with reduced scopes
4. Use case: Creating limited tokens for third-party apps


EXERCISE 2: Implement Client Credentials Flow
---------------------------------------------
Add support for machine-to-machine authentication:
1. Create client_credentials grant type
2. Clients have fixed scopes (no user context)
3. POST /auth/client-token endpoint
4. Different scope validation (client scopes, not user)
"""
