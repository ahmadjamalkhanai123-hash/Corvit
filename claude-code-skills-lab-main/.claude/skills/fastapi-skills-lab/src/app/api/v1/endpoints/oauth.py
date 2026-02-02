"""
OAuth Endpoints
===============

OAuth2 provider authentication endpoints.
"""

import secrets
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ....db.session import get_db
from ....core.oauth import (
    get_provider, get_authorization_url, exchange_code,
    get_user_info, normalize_user_info
)
from ....core.security import create_token_pair
from ....services.auth_service import AuthService

router = APIRouter(prefix="/oauth", tags=["OAuth"])

# State storage (use Redis in production)
oauth_states: dict[str, dict] = {}


def generate_state(provider: str) -> str:
    """Generate OAuth state for CSRF protection."""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"provider": provider}
    return state


def verify_state(state: str, provider: str) -> bool:
    """Verify OAuth state."""
    data = oauth_states.pop(state, None)
    return data and data.get("provider") == provider


@router.get("/{provider}/login")
async def oauth_login(provider: str):
    """Initiate OAuth login flow."""
    oauth_provider = get_provider(provider)
    if not oauth_provider or not oauth_provider.client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider}' not configured"
        )

    state = generate_state(provider)
    auth_url = get_authorization_url(oauth_provider, state)
    return RedirectResponse(url=auth_url)


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback."""
    if not verify_state(state, provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state"
        )

    oauth_provider = get_provider(provider)
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Exchange code for tokens
    tokens = await exchange_code(oauth_provider, code)
    access_token = tokens.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="Token exchange failed")

    # Get user info
    user_data = await get_user_info(oauth_provider, access_token)
    normalized = normalize_user_info(provider, user_data)

    # Get or create user
    auth_service = AuthService(db)
    user = auth_service.get_or_create_oauth_user(
        provider=normalized["provider"],
        provider_user_id=normalized["provider_user_id"],
        email=normalized.get("email"),
        name=normalized.get("name"),
        picture=normalized.get("picture")
    )

    # Create JWT tokens
    token_pair = create_token_pair(str(user.id))

    return {
        "message": "Login successful",
        "user_id": user.id,
        "access_token": token_pair.access_token,
        "refresh_token": token_pair.refresh_token,
        "token_type": "bearer"
    }


@router.get("/providers")
async def list_providers():
    """List available OAuth providers."""
    from ....core.oauth import PROVIDERS
    return {
        "providers": [
            {"name": name, "configured": bool(p.client_id)}
            for name, p in PROVIDERS.items()
        ]
    }
