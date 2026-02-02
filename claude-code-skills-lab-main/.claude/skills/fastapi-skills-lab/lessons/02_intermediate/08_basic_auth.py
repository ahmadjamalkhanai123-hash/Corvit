"""
LESSON 16: API Keys and HTTP Basic Authentication
=================================================

Implement simple authentication methods for APIs.

Key Concepts:
- API key authentication patterns
- HTTP Basic authentication
- Combining multiple auth methods
- Security considerations
- When to use each method

To run this lesson:
    cd fastapi-skills-lab
    uv run uvicorn lessons.02_intermediate.08_basic_auth:app --reload

Then visit: http://127.0.0.1:8000/docs
"""

import secrets
import hashlib
from typing import Annotated
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, status, Security, Header
from fastapi.security import APIKeyHeader, APIKeyQuery, HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel


# =============================================================================
# SECTION 1: API Key Authentication
# =============================================================================

"""
API Keys are simple tokens for authenticating API requests.

Use cases:
- Server-to-server communication
- Third-party integrations
- Public APIs with rate limiting
- Simpler alternative to OAuth for trusted clients

Best practices:
- Never log or expose API keys
- Hash keys before storing (like passwords)
- Use prefixes for identification (sk_live_, sk_test_)
- Set expiration dates
- Support key rotation
"""

# Security schemes for API key extraction
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)

# Simulated API key storage (use database in production)
# Format: {key_hash: {owner, scopes, created_at, expires_at}}
API_KEYS_DB: dict[str, dict] = {}


class APIKeyCreate(BaseModel):
    """Request to create new API key."""
    name: str
    scopes: list[str] = ["read"]


class APIKeyResponse(BaseModel):
    """Response with API key (only shown once!)."""
    key: str
    key_id: str
    name: str
    scopes: list[str]


def generate_api_key(prefix: str = "sk_live") -> str:
    """Generate a secure API key with prefix."""
    random_part = secrets.token_hex(24)
    return f"{prefix}_{random_part}"


def hash_api_key(key: str) -> str:
    """Hash API key for secure storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def create_api_key(owner: str, name: str, scopes: list[str]) -> tuple[str, str]:
    """
    Create and store a new API key.

    Returns (full_key, key_id) - full_key is only shown once!
    """
    full_key = generate_api_key()
    key_hash = hash_api_key(full_key)
    key_id = f"sk_{key_hash[:8]}"

    API_KEYS_DB[key_hash] = {
        "key_id": key_id,
        "owner": owner,
        "name": name,
        "scopes": scopes,
        "created_at": datetime.now(timezone.utc),
        "expires_at": None,
        "last_used": None
    }

    return full_key, key_id


def verify_api_key(key: str) -> dict | None:
    """Verify an API key and return its data."""
    key_hash = hash_api_key(key)
    key_data = API_KEYS_DB.get(key_hash)

    if not key_data:
        return None

    # Check expiration
    if key_data.get("expires_at"):
        if datetime.now(timezone.utc) > key_data["expires_at"]:
            return None

    # Update last used
    key_data["last_used"] = datetime.now(timezone.utc)

    return key_data


async def get_api_key(
    header_key: str | None = Security(api_key_header),
    query_key: str | None = Security(api_key_query)
) -> dict:
    """
    Dependency to validate API key from header or query.

    Checks X-API-Key header first, then api_key query parameter.
    """
    api_key = header_key or query_key

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    key_data = verify_api_key(api_key)

    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired API key"
        )

    return key_data


def require_scope(required_scope: str):
    """
    Dependency factory for scope-based authorization.

    Usage:
        @app.delete("/items/{id}")
        def delete_item(
            id: int,
            key_data: dict = Depends(require_scope("write"))
        ):
            ...
    """
    async def dependency(key_data: dict = Depends(get_api_key)) -> dict:
        if required_scope not in key_data.get("scopes", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{required_scope}' required"
            )
        return key_data

    return dependency


# =============================================================================
# SECTION 2: HTTP Basic Authentication
# =============================================================================

"""
HTTP Basic Auth sends username:password base64-encoded in Authorization header.

Pros:
- Simple to implement
- Widely supported
- No cookies needed

Cons:
- Credentials sent with every request
- Must use HTTPS (credentials are only base64 encoded, not encrypted)
- No session management

Best for:
- Internal services
- Simple APIs
- Temporary/quick authentication needs
"""

basic_security = HTTPBasic()

# Simulated user database
USERS_DB = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "roles": ["admin", "user"]
    },
    "user": {
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "roles": ["user"]
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


async def get_current_user_basic(
    credentials: HTTPBasicCredentials = Depends(basic_security)
) -> dict:
    """
    Dependency for HTTP Basic authentication.

    Usage:
        @app.get("/protected")
        def protected(user: dict = Depends(get_current_user_basic)):
            return {"user": user["username"]}
    """
    user = USERS_DB.get(credentials.username)

    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"}
        )

    return {"username": credentials.username, "roles": user["roles"]}


def require_role(role: str):
    """
    Dependency factory for role-based access with Basic auth.

    Usage:
        @app.delete("/admin/users/{id}")
        def delete_user(
            id: int,
            user: dict = Depends(require_role("admin"))
        ):
            ...
    """
    async def dependency(user: dict = Depends(get_current_user_basic)) -> dict:
        if role not in user.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return user

    return dependency


# =============================================================================
# SECTION 3: Combining Authentication Methods
# =============================================================================

"""
Some APIs support multiple authentication methods.
This provides flexibility for different client types.
"""

async def get_current_user_flexible(
    api_key: str | None = Security(api_key_header),
    basic_credentials: HTTPBasicCredentials | None = Depends(
        HTTPBasic(auto_error=False)
    )
) -> dict:
    """
    Dependency that accepts either API key or Basic auth.

    Tries API key first, then Basic auth.
    """
    # Try API key first
    if api_key:
        key_data = verify_api_key(api_key)
        if key_data:
            return {
                "auth_type": "api_key",
                "identity": key_data["owner"],
                "scopes": key_data["scopes"]
            }

    # Try Basic auth
    if basic_credentials:
        user = USERS_DB.get(basic_credentials.username)
        if user and verify_password(basic_credentials.password, user["password_hash"]):
            return {
                "auth_type": "basic",
                "identity": basic_credentials.username,
                "roles": user["roles"]
            }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid API key or credentials required",
        headers={"WWW-Authenticate": "Basic, ApiKey"}
    )


# =============================================================================
# SECTION 4: Optional Authentication
# =============================================================================

"""
Some endpoints work differently for authenticated vs anonymous users.
"""

async def get_optional_user(
    api_key: str | None = Security(api_key_header)
) -> dict | None:
    """
    Dependency for optional authentication.

    Returns user data if authenticated, None otherwise.
    """
    if not api_key:
        return None

    return verify_api_key(api_key)


# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="API Keys and Basic Authentication",
    description="Learn simple authentication methods",
    version="1.0.0"
)

# Create a demo API key on startup
demo_key, demo_key_id = create_api_key("demo_user", "Demo Key", ["read", "write"])
print(f"\nDemo API Key: {demo_key}")
print(f"Demo Key ID: {demo_key_id}\n")


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.post("/api-keys", response_model=APIKeyResponse)
async def create_new_api_key(
    request: APIKeyCreate,
    user: dict = Depends(get_current_user_basic)
):
    """Create a new API key (requires Basic auth)."""
    if "admin" not in user["roles"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create API keys"
        )

    full_key, key_id = create_api_key(
        owner=user["username"],
        name=request.name,
        scopes=request.scopes
    )

    return APIKeyResponse(
        key=full_key,
        key_id=key_id,
        name=request.name,
        scopes=request.scopes
    )


@app.get("/api-key/info")
async def get_api_key_info(key_data: dict = Depends(get_api_key)):
    """Get information about the current API key."""
    return {
        "key_id": key_data["key_id"],
        "owner": key_data["owner"],
        "name": key_data["name"],
        "scopes": key_data["scopes"],
        "created_at": key_data["created_at"].isoformat()
    }


@app.get("/data/read")
async def read_data(key_data: dict = Depends(require_scope("read"))):
    """Endpoint requiring 'read' scope."""
    return {"data": "This is readable data", "accessed_by": key_data["owner"]}


@app.post("/data/write")
async def write_data(
    data: dict,
    key_data: dict = Depends(require_scope("write"))
):
    """Endpoint requiring 'write' scope."""
    return {"written": data, "written_by": key_data["owner"]}


@app.get("/basic/protected")
async def basic_protected(user: dict = Depends(get_current_user_basic)):
    """Endpoint protected by HTTP Basic auth."""
    return {"message": f"Hello, {user['username']}!", "roles": user["roles"]}


@app.get("/basic/admin")
async def admin_only(user: dict = Depends(require_role("admin"))):
    """Admin-only endpoint using Basic auth."""
    return {"message": "Welcome, admin!", "user": user["username"]}


@app.get("/flexible")
async def flexible_auth(user: dict = Depends(get_current_user_flexible)):
    """Endpoint accepting either API key or Basic auth."""
    return {
        "auth_type": user["auth_type"],
        "identity": user["identity"]
    }


@app.get("/public-or-private")
async def public_or_private(user: dict | None = Depends(get_optional_user)):
    """Endpoint with optional authentication."""
    if user:
        return {
            "message": "Authenticated access",
            "user": user["owner"],
            "premium_data": "Secret information"
        }
    return {
        "message": "Anonymous access",
        "basic_data": "Public information"
    }


@app.get("/health")
async def health():
    """Public health check endpoint."""
    return {"status": "healthy"}


# =============================================================================
# KEY CONCEPTS SUMMARY
# =============================================================================

"""
KEY CONCEPTS:
=============

1. API KEY AUTHENTICATION:
   - Simple token-based authentication
   - Support header (X-API-Key) and query parameter (api_key)
   - Hash keys before storage
   - Use meaningful prefixes (sk_live_, sk_test_)
   - Support scopes for authorization

2. HTTP BASIC AUTHENTICATION:
   - Username:password in Authorization header
   - Base64 encoded (NOT encrypted!)
   - MUST use HTTPS in production
   - Good for internal services

3. COMBINING METHODS:
   - Check multiple auth methods in order
   - Provide flexibility for different clients
   - Return consistent user/identity object

4. OPTIONAL AUTHENTICATION:
   - Some endpoints work for both auth/anon users
   - Return None if not authenticated
   - Provide different responses based on auth status

5. SECURITY CONSIDERATIONS:
   - Always use HTTPS
   - Hash API keys like passwords
   - Set appropriate expiration
   - Log authentication failures (not credentials!)
   - Rate limit authentication endpoints

WHEN TO USE WHAT:
=================
- API Keys: Server-to-server, third-party integrations
- Basic Auth: Internal tools, simple admin interfaces
- JWT/OAuth2: User-facing applications, mobile apps
"""


# =============================================================================
# EXERCISES
# =============================================================================

"""
EXERCISE 1: Implement Key Rotation
----------------------------------
Add ability to rotate API keys:
1. POST /api-keys/{key_id}/rotate - Generate new key, invalidate old
2. Support grace period where both old and new keys work
3. Track rotation history

Requirements:
- Only key owner can rotate
- Return new key (shown only once)
- Old key works for 24 hours after rotation


EXERCISE 2: Add Rate Limiting per API Key
-----------------------------------------
Implement rate limiting tied to API keys:
1. Different limits per scope (read: 100/min, write: 20/min)
2. Track usage in key_data
3. Return rate limit headers (X-RateLimit-*)

Bonus: Add daily/monthly quotas per key
"""
