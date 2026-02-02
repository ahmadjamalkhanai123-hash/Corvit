"""
OAuth Provider Configuration
============================

Configuration and utilities for OAuth2 providers (Google, GitHub, Microsoft).
"""

from dataclasses import dataclass
import httpx
from ..core.config import settings


@dataclass
class OAuthProvider:
    """OAuth2 provider configuration."""
    name: str
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: list[str]
    redirect_uri: str


# Provider configurations
PROVIDERS = {
    "google": OAuthProvider(
        name="google",
        client_id=getattr(settings, 'google_client_id', ''),
        client_secret=getattr(settings, 'google_client_secret', ''),
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
        scopes=["openid", "email", "profile"],
        redirect_uri=getattr(settings, 'google_redirect_uri', 'http://localhost:8000/auth/google/callback')
    ),
    "github": OAuthProvider(
        name="github",
        client_id=getattr(settings, 'github_client_id', ''),
        client_secret=getattr(settings, 'github_client_secret', ''),
        authorize_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        userinfo_url="https://api.github.com/user",
        scopes=["user:email", "read:user"],
        redirect_uri=getattr(settings, 'github_redirect_uri', 'http://localhost:8000/auth/github/callback')
    ),
    "microsoft": OAuthProvider(
        name="microsoft",
        client_id=getattr(settings, 'microsoft_client_id', ''),
        client_secret=getattr(settings, 'microsoft_client_secret', ''),
        authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        userinfo_url="https://graph.microsoft.com/v1.0/me",
        scopes=["openid", "email", "profile", "User.Read"],
        redirect_uri=getattr(settings, 'microsoft_redirect_uri', 'http://localhost:8000/auth/microsoft/callback')
    ),
}


def get_provider(name: str) -> OAuthProvider | None:
    """Get OAuth provider by name."""
    return PROVIDERS.get(name)


def get_authorization_url(provider: OAuthProvider, state: str) -> str:
    """Generate authorization URL."""
    params = {
        "client_id": provider.client_id,
        "redirect_uri": provider.redirect_uri,
        "response_type": "code",
        "scope": " ".join(provider.scopes),
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{provider.authorize_url}?{query}"


async def exchange_code(provider: OAuthProvider, code: str) -> dict:
    """Exchange authorization code for tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            provider.token_url,
            data={
                "client_id": provider.client_id,
                "client_secret": provider.client_secret,
                "code": code,
                "redirect_uri": provider.redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"}
        )
        return response.json()


async def get_user_info(provider: OAuthProvider, access_token: str) -> dict:
    """Fetch user info from provider."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            provider.userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return response.json()


def normalize_user_info(provider_name: str, data: dict) -> dict:
    """Normalize user info to common format."""
    if provider_name == "google":
        return {
            "provider": "google",
            "provider_user_id": data["id"],
            "email": data.get("email"),
            "name": data.get("name"),
            "picture": data.get("picture"),
        }
    elif provider_name == "github":
        return {
            "provider": "github",
            "provider_user_id": str(data["id"]),
            "email": data.get("email"),
            "name": data.get("name") or data.get("login"),
            "picture": data.get("avatar_url"),
        }
    elif provider_name == "microsoft":
        return {
            "provider": "microsoft",
            "provider_user_id": data["id"],
            "email": data.get("mail") or data.get("userPrincipalName"),
            "name": data.get("displayName"),
            "picture": None,
        }
    return data
