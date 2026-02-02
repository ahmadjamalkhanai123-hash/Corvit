"""
LESSON 17: OAuth2 Provider Integration
======================================

Integrate with Google, GitHub, and Microsoft OAuth2.

Key Concepts:
- OAuth2 authorization code flow
- Google OAuth2 integration
- GitHub OAuth2 integration
- Microsoft/Azure AD integration
- State management and CSRF protection
- Token storage and refresh

To run this lesson:
    cd fastapi-skills-lab
    uv run uvicorn lessons.03_advanced.05_oauth2_providers:app --reload

Then visit: http://127.0.0.1:8000/docs

Note: You'll need to configure OAuth credentials for each provider.
"""

from datetime import datetime, timezone
from typing import Annotated
import secrets
import httpx

from fastapi import FastAPI, Depends, HTTPException, status, Request, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings


# =============================================================================
# SECTION 1: Configuration
# =============================================================================

class OAuthSettings(BaseSettings):
    """OAuth provider configuration."""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/auth/github/callback"

    # Microsoft OAuth
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""
    microsoft_redirect_uri: str = "http://localhost:8000/auth/microsoft/callback"
    microsoft_tenant: str = "common"  # or specific tenant ID

    class Config:
        env_file = ".env"


settings = OAuthSettings()


# =============================================================================
# SECTION 2: OAuth2 Provider Base Class
# =============================================================================

class OAuth2Provider:
    """Base class for OAuth2 providers."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        authorize_url: str,
        token_url: str,
        userinfo_url: str,
        scopes: list[str]
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.userinfo_url = userinfo_url
        self.scopes = scopes

    def get_authorization_url(self, state: str) -> str:
        """Generate authorization URL with state parameter."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.authorize_url}?{query}"

    async def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Token exchange failed: {response.text}"
                )

            return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        """Fetch user information using access token."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch user info"
                )

            return response.json()


# =============================================================================
# SECTION 3: Provider Implementations
# =============================================================================

class GoogleOAuth(OAuth2Provider):
    """Google OAuth2 provider."""

    def __init__(self):
        super().__init__(
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            redirect_uri=settings.google_redirect_uri,
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
            scopes=["openid", "email", "profile"]
        )

    def get_authorization_url(self, state: str) -> str:
        """Google-specific authorization URL with additional params."""
        base_url = super().get_authorization_url(state)
        # Add Google-specific parameters
        return f"{base_url}&access_type=offline&prompt=consent"

    def normalize_user(self, user_data: dict) -> dict:
        """Normalize Google user data to common format."""
        return {
            "provider": "google",
            "provider_id": user_data["id"],
            "email": user_data["email"],
            "name": user_data.get("name"),
            "picture": user_data.get("picture"),
            "email_verified": user_data.get("verified_email", False)
        }


class GitHubOAuth(OAuth2Provider):
    """GitHub OAuth2 provider."""

    def __init__(self):
        super().__init__(
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            redirect_uri=settings.github_redirect_uri,
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            userinfo_url="https://api.github.com/user",
            scopes=["user:email", "read:user"]
        )

    async def get_user_email(self, access_token: str) -> str | None:
        """GitHub may not return email in user info, fetch separately."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                emails = response.json()
                for email in emails:
                    if email.get("primary"):
                        return email["email"]
        return None

    def normalize_user(self, user_data: dict, email: str | None = None) -> dict:
        """Normalize GitHub user data to common format."""
        return {
            "provider": "github",
            "provider_id": str(user_data["id"]),
            "email": email or user_data.get("email"),
            "name": user_data.get("name") or user_data.get("login"),
            "picture": user_data.get("avatar_url"),
            "username": user_data.get("login")
        }


class MicrosoftOAuth(OAuth2Provider):
    """Microsoft/Azure AD OAuth2 provider."""

    def __init__(self):
        tenant = settings.microsoft_tenant
        super().__init__(
            client_id=settings.microsoft_client_id,
            client_secret=settings.microsoft_client_secret,
            redirect_uri=settings.microsoft_redirect_uri,
            authorize_url=f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
            token_url=f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            userinfo_url="https://graph.microsoft.com/v1.0/me",
            scopes=["openid", "email", "profile", "User.Read"]
        )

    def normalize_user(self, user_data: dict) -> dict:
        """Normalize Microsoft user data to common format."""
        return {
            "provider": "microsoft",
            "provider_id": user_data["id"],
            "email": user_data.get("mail") or user_data.get("userPrincipalName"),
            "name": user_data.get("displayName"),
            "picture": None,  # Requires separate Graph API call
            "job_title": user_data.get("jobTitle")
        }


# Provider instances
google_oauth = GoogleOAuth()
github_oauth = GitHubOAuth()
microsoft_oauth = MicrosoftOAuth()


# =============================================================================
# SECTION 4: State Management (CSRF Protection)
# =============================================================================

"""
OAuth state parameter prevents CSRF attacks.
Store state server-side and verify on callback.
"""

# In production, use Redis or database
oauth_states: dict[str, dict] = {}


def generate_state(provider: str, redirect_after: str = "/") -> str:
    """Generate and store OAuth state."""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "provider": provider,
        "redirect_after": redirect_after,
        "created_at": datetime.now(timezone.utc)
    }
    return state


def verify_state(state: str, provider: str) -> dict:
    """Verify OAuth state and return stored data."""
    state_data = oauth_states.pop(state, None)

    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state"
        )

    if state_data["provider"] != provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State provider mismatch"
        )

    return state_data


# =============================================================================
# SECTION 5: User Storage (Simulated)
# =============================================================================

class OAuthUser(BaseModel):
    """OAuth user model."""
    id: str
    provider: str
    provider_id: str
    email: str | None
    name: str | None
    picture: str | None
    created_at: datetime
    last_login: datetime


# Simulated user database
users_db: dict[str, OAuthUser] = {}


def get_or_create_user(normalized_data: dict) -> OAuthUser:
    """Get existing user or create new one from OAuth data."""
    # Look up by provider + provider_id
    lookup_key = f"{normalized_data['provider']}:{normalized_data['provider_id']}"

    if lookup_key in users_db:
        # Update last login
        user = users_db[lookup_key]
        user.last_login = datetime.now(timezone.utc)
        return user

    # Create new user
    user = OAuthUser(
        id=secrets.token_hex(16),
        provider=normalized_data["provider"],
        provider_id=normalized_data["provider_id"],
        email=normalized_data.get("email"),
        name=normalized_data.get("name"),
        picture=normalized_data.get("picture"),
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    users_db[lookup_key] = user
    return user


# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="OAuth2 Provider Integration",
    description="Learn to integrate Google, GitHub, and Microsoft OAuth2",
    version="1.0.0"
)


# =============================================================================
# ENDPOINTS: Google OAuth
# =============================================================================

@app.get("/auth/google/login")
async def google_login(redirect_after: str = "/"):
    """Initiate Google OAuth login."""
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured"
        )

    state = generate_state("google", redirect_after)
    auth_url = google_oauth.get_authorization_url(state)
    return RedirectResponse(url=auth_url)


@app.get("/auth/google/callback")
async def google_callback(code: str, state: str):
    """Handle Google OAuth callback."""
    state_data = verify_state(state, "google")

    # Exchange code for tokens
    tokens = await google_oauth.exchange_code(code)

    # Get user info
    user_data = await google_oauth.get_user_info(tokens["access_token"])
    normalized = google_oauth.normalize_user(user_data)

    # Get or create user
    user = get_or_create_user(normalized)

    return {
        "message": "Login successful",
        "user": user,
        "tokens": {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens.get("expires_in")
        }
    }


# =============================================================================
# ENDPOINTS: GitHub OAuth
# =============================================================================

@app.get("/auth/github/login")
async def github_login(redirect_after: str = "/"):
    """Initiate GitHub OAuth login."""
    if not settings.github_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GitHub OAuth not configured"
        )

    state = generate_state("github", redirect_after)
    auth_url = github_oauth.get_authorization_url(state)
    return RedirectResponse(url=auth_url)


@app.get("/auth/github/callback")
async def github_callback(code: str, state: str):
    """Handle GitHub OAuth callback."""
    state_data = verify_state(state, "github")

    # Exchange code for tokens
    tokens = await github_oauth.exchange_code(code)
    access_token = tokens["access_token"]

    # Get user info
    user_data = await github_oauth.get_user_info(access_token)

    # Get email separately if not in user data
    email = user_data.get("email")
    if not email:
        email = await github_oauth.get_user_email(access_token)

    normalized = github_oauth.normalize_user(user_data, email)

    # Get or create user
    user = get_or_create_user(normalized)

    return {
        "message": "Login successful",
        "user": user,
        "tokens": {"access_token": access_token}
    }


# =============================================================================
# ENDPOINTS: Microsoft OAuth
# =============================================================================

@app.get("/auth/microsoft/login")
async def microsoft_login(redirect_after: str = "/"):
    """Initiate Microsoft OAuth login."""
    if not settings.microsoft_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Microsoft OAuth not configured"
        )

    state = generate_state("microsoft", redirect_after)
    auth_url = microsoft_oauth.get_authorization_url(state)
    return RedirectResponse(url=auth_url)


@app.get("/auth/microsoft/callback")
async def microsoft_callback(code: str, state: str):
    """Handle Microsoft OAuth callback."""
    state_data = verify_state(state, "microsoft")

    # Exchange code for tokens
    tokens = await microsoft_oauth.exchange_code(code)

    # Get user info
    user_data = await microsoft_oauth.get_user_info(tokens["access_token"])
    normalized = microsoft_oauth.normalize_user(user_data)

    # Get or create user
    user = get_or_create_user(normalized)

    return {
        "message": "Login successful",
        "user": user,
        "tokens": {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens.get("expires_in")
        }
    }


# =============================================================================
# ENDPOINTS: General
# =============================================================================

@app.get("/auth/providers")
async def list_providers():
    """List configured OAuth providers."""
    return {
        "providers": {
            "google": bool(settings.google_client_id),
            "github": bool(settings.github_client_id),
            "microsoft": bool(settings.microsoft_client_id)
        }
    }


@app.get("/users")
async def list_users():
    """List all OAuth users (demo endpoint)."""
    return {"users": list(users_db.values())}


# =============================================================================
# KEY CONCEPTS SUMMARY
# =============================================================================

"""
KEY CONCEPTS:
=============

1. OAUTH2 AUTHORIZATION CODE FLOW:
   1. User clicks "Login with Provider"
   2. Redirect to provider's authorization URL
   3. User grants permission
   4. Provider redirects back with authorization code
   5. Exchange code for access token
   6. Use token to fetch user info

2. STATE PARAMETER:
   - Random string to prevent CSRF attacks
   - Generated before redirect, verified on callback
   - Store server-side with expiration

3. PROVIDER-SPECIFIC DETAILS:
   - Google: Uses OpenID Connect, returns structured user info
   - GitHub: Email may need separate API call
   - Microsoft: Uses Graph API, tenant configuration

4. TOKEN MANAGEMENT:
   - Access tokens: Short-lived, used for API calls
   - Refresh tokens: Long-lived, used to get new access tokens
   - Store securely (encrypted in database)

5. USER LINKING:
   - Match users by provider + provider_id
   - Handle email conflicts (same email, different providers)
   - Support linking multiple providers to one account

SECURITY BEST PRACTICES:
========================
- Always verify state parameter
- Use HTTPS for all OAuth endpoints
- Store client secrets securely (env vars, secrets manager)
- Validate redirect URIs strictly
- Set appropriate token expiration
- Log authentication events for audit
"""


# =============================================================================
# EXERCISES
# =============================================================================

"""
EXERCISE 1: Implement Token Refresh
-----------------------------------
Add refresh token support for Google OAuth:
1. Store refresh tokens securely
2. POST /auth/google/refresh - Get new access token
3. Handle token expiration gracefully
4. Implement automatic token refresh in API calls


EXERCISE 2: Account Linking
---------------------------
Allow users to link multiple OAuth providers:
1. Add /auth/{provider}/link endpoint (requires existing auth)
2. Store multiple provider connections per user
3. Handle conflicts (e.g., email already used)
4. Add /auth/unlink/{provider} endpoint

Consider:
- What happens if user unlinks their only provider?
- How to handle email changes across providers?
"""
