"""
LESSON 18: OpenID Connect and Single Sign-On
============================================

Implement SSO patterns for enterprise applications.

Key Concepts:
- OpenID Connect basics
- ID Token validation
- Claims extraction
- SSO flow implementation
- Session management

To run:
    uv run uvicorn lessons.03_advanced.06_openid_sso:app --reload
"""

import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from jose import jwt, JWTError


# =============================================================================
# OpenID Connect Concepts
# =============================================================================

"""
OpenID Connect (OIDC) builds on OAuth2:
- OAuth2: Authorization (access to resources)
- OIDC: Authentication (who is the user)

Key additions:
- ID Token: JWT containing user identity
- UserInfo endpoint: Get user claims
- Standard scopes: openid, profile, email
- Standard claims: sub, name, email, picture
"""


# =============================================================================
# OIDC Configuration
# =============================================================================

class OIDCConfig(BaseModel):
    """OpenID Connect provider configuration."""
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    scopes_supported: list[str]
    response_types_supported: list[str]
    claims_supported: list[str]


# Example: Google's OIDC configuration
GOOGLE_OIDC = OIDCConfig(
    issuer="https://accounts.google.com",
    authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
    token_endpoint="https://oauth2.googleapis.com/token",
    userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
    scopes_supported=["openid", "email", "profile"],
    response_types_supported=["code", "token", "id_token"],
    claims_supported=["sub", "name", "email", "picture", "email_verified"]
)


# =============================================================================
# ID Token Handling
# =============================================================================

class IDToken(BaseModel):
    """Standard OIDC ID Token claims."""
    iss: str           # Issuer
    sub: str           # Subject (unique user ID)
    aud: str           # Audience (client ID)
    exp: int           # Expiration time
    iat: int           # Issued at
    nonce: str | None = None  # For replay protection
    # Standard claims
    name: str | None = None
    email: str | None = None
    email_verified: bool | None = None
    picture: str | None = None


def validate_id_token(
    token: str,
    client_id: str,
    issuer: str,
    secret: str = "demo-secret"  # In production: use JWKS
) -> IDToken:
    """
    Validate ID Token.

    In production:
    1. Fetch JWKS from provider
    2. Verify signature with provider's public key
    3. Validate all claims
    """
    try:
        # Decode (in production: verify with JWKS)
        payload = jwt.decode(
            token, secret,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Demo only
        )

        # Validate issuer
        if payload.get("iss") != issuer:
            raise ValueError("Invalid issuer")

        # Validate audience
        if payload.get("aud") != client_id:
            raise ValueError("Invalid audience")

        # Validate expiration
        if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
            raise ValueError("Token expired")

        return IDToken(**payload)

    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")


# =============================================================================
# SSO Session Management
# =============================================================================

class SSOSession(BaseModel):
    """SSO session data."""
    session_id: str
    user_id: str
    provider: str
    email: str | None
    name: str | None
    created_at: datetime
    expires_at: datetime
    claims: dict[str, Any]


# Session storage (use Redis in production)
sessions: dict[str, SSOSession] = {}
# State storage for CSRF
states: dict[str, dict] = {}


def create_session(
    user_id: str,
    provider: str,
    claims: dict
) -> SSOSession:
    """Create SSO session."""
    from datetime import timedelta

    session_id = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)

    session = SSOSession(
        session_id=session_id,
        user_id=user_id,
        provider=provider,
        email=claims.get("email"),
        name=claims.get("name"),
        created_at=now,
        expires_at=now + timedelta(hours=8),
        claims=claims
    )
    sessions[session_id] = session
    return session


def get_session(session_id: str) -> SSOSession | None:
    """Get and validate session."""
    session = sessions.get(session_id)
    if not session:
        return None
    if session.expires_at < datetime.now(timezone.utc):
        del sessions[session_id]
        return None
    return session


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="OpenID Connect & SSO Demo",
    version="1.0.0"
)

CLIENT_ID = "demo-client-id"
ISSUER = "https://demo-idp.example.com"


@app.get("/")
async def root():
    """Home page."""
    return {
        "message": "OpenID Connect SSO Demo",
        "endpoints": {
            "/login": "Start SSO login",
            "/callback": "OIDC callback",
            "/me": "Get current user (requires session)",
            "/logout": "End session"
        }
    }


@app.get("/.well-known/openid-configuration")
async def openid_configuration():
    """OIDC Discovery endpoint (when acting as provider)."""
    return {
        "issuer": ISSUER,
        "authorization_endpoint": f"{ISSUER}/authorize",
        "token_endpoint": f"{ISSUER}/token",
        "userinfo_endpoint": f"{ISSUER}/userinfo",
        "jwks_uri": f"{ISSUER}/.well-known/jwks.json",
        "scopes_supported": ["openid", "email", "profile"],
        "response_types_supported": ["code", "id_token", "token"],
        "claims_supported": ["sub", "name", "email", "picture"]
    }


@app.get("/login")
async def login(provider: str = "demo"):
    """
    Initiate SSO login.

    In production: Redirect to actual IdP.
    """
    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(16)

    states[state] = {
        "provider": provider,
        "nonce": nonce,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Demo: Simulate immediate callback
    return {
        "message": "In production, redirect to IdP",
        "state": state,
        "nonce": nonce,
        "next_step": f"/callback?state={state}&code=demo-auth-code"
    }


@app.get("/callback")
async def callback(
    state: str,
    code: str = "demo-code"
):
    """
    Handle OIDC callback.

    In production:
    1. Validate state
    2. Exchange code for tokens
    3. Validate ID token
    4. Create session
    """
    # Validate state
    state_data = states.pop(state, None)
    if not state_data:
        raise HTTPException(400, "Invalid state")

    # Demo: Create mock ID token claims
    claims = {
        "iss": ISSUER,
        "sub": "user-123",
        "aud": CLIENT_ID,
        "exp": int((datetime.now(timezone.utc).timestamp()) + 3600),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "nonce": state_data["nonce"],
        "name": "Demo User",
        "email": "demo@example.com",
        "email_verified": True,
        "picture": "https://example.com/avatar.jpg"
    }

    # Create session
    session = create_session(
        user_id=claims["sub"],
        provider=state_data["provider"],
        claims=claims
    )

    return {
        "message": "Login successful",
        "session_id": session.session_id,
        "user": {
            "id": session.user_id,
            "name": session.name,
            "email": session.email
        },
        "expires_at": session.expires_at.isoformat()
    }


@app.get("/me")
async def get_current_user(session_id: str = Query(...)):
    """Get current user from session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(401, "Invalid or expired session")

    return {
        "user_id": session.user_id,
        "name": session.name,
        "email": session.email,
        "provider": session.provider,
        "claims": session.claims
    }


@app.post("/logout")
async def logout(session_id: str = Query(...)):
    """End SSO session."""
    if session_id in sessions:
        del sessions[session_id]

    return {"message": "Logged out successfully"}


# =============================================================================
# Key Concepts
# =============================================================================

"""
OIDC Flow:
1. User clicks "Login with Provider"
2. Redirect to IdP with client_id, scope, state, nonce
3. User authenticates at IdP
4. IdP redirects back with authorization code
5. Exchange code for tokens (access_token, id_token)
6. Validate id_token signature and claims
7. Create local session

Important Claims:
- sub: Unique user identifier (never changes)
- iss: Token issuer (must match expected)
- aud: Audience (must be your client_id)
- exp: Expiration (must be in future)
- nonce: Replay protection (must match sent value)

SSO Benefits:
- Single login for multiple apps
- Centralized user management
- Reduced password fatigue
- Audit trail at IdP

Security:
- Always validate state (CSRF protection)
- Verify nonce (replay protection)
- Use PKCE for public clients
- Validate ID token with JWKS
"""
