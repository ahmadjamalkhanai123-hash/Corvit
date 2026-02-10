"""JWT token creation and verification using python-jose."""

import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from pydantic import BaseModel

from src.config.settings import get_settings


class TokenData(BaseModel):
    user_id: uuid.UUID
    role: str


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token, returning TokenData."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None or role is None:
            raise JWTError("Missing sub or role claim")
        return TokenData(user_id=uuid.UUID(user_id), role=role)
    except JWTError:
        raise
