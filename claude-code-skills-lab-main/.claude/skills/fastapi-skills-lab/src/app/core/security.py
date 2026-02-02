"""
Security Utilities
==================

JWT token handling (access + refresh), password hashing (bcrypt + argon2),
and authentication dependencies.
"""

from datetime import datetime, timedelta, timezone
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from .config import settings


# =============================================================================
# PASSWORD HASHING
# =============================================================================

# bcrypt context - traditional, widely used
bcrypt_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

# argon2 context - modern, recommended for new projects
argon2_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,
    argon2__parallelism=4
)

# Default context (use argon2 for new projects)
pwd_context = argon2_context


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    Automatically detects hash type (bcrypt or argon2).
    """
    # Try argon2 first (preferred)
    if hashed_password.startswith("$argon2"):
        return argon2_context.verify(plain_password, hashed_password)
    # Fall back to bcrypt for legacy hashes
    return bcrypt_context.verify(plain_password, hashed_password)


def get_password_hash(password: str, use_argon2: bool = True) -> str:
    """
    Hash a password using argon2 (default) or bcrypt.

    Args:
        password: Plain text password
        use_argon2: Use argon2 (True) or bcrypt (False)
    """
    if use_argon2:
        return argon2_context.hash(password)
    return bcrypt_context.hash(password)


# Legacy aliases for backward compatibility
def hash_password_bcrypt(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt_context.hash(password)


def hash_password_argon2(password: str) -> str:
    """Hash password using argon2 (recommended)."""
    return argon2_context.hash(password)


# =============================================================================
# JWT TOKENS
# =============================================================================

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str | None = None
    exp: datetime | None = None
    type: str = "access"  # "access" or "refresh"
    jti: str | None = None  # JWT ID for blacklisting


class TokenPair(BaseModel):
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    include_jti: bool = True
) -> str:
    """
    Create a JWT access token (short-lived).

    Args:
        subject: The subject claim (usually user ID or username)
        expires_delta: Optional custom expiration time
        include_jti: Include JWT ID for blacklisting support

    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }

    if include_jti:
        to_encode["jti"] = secrets.token_hex(16)

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None
) -> str:
    """
    Create a JWT refresh token (long-lived).

    Args:
        subject: The subject claim (usually user ID or username)
        expires_delta: Optional custom expiration time (default: 7 days)

    Returns:
        Encoded JWT refresh token string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": secrets.token_hex(16)
    }

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )


def create_token_pair(subject: str) -> TokenPair:
    """
    Create both access and refresh tokens.

    Args:
        subject: The subject claim (usually user ID or username)

    Returns:
        TokenPair with access_token and refresh_token
    """
    return TokenPair(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject)
    )


def verify_token(token: str, expected_type: str | None = None) -> TokenPayload:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token to verify
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        TokenPayload with decoded data

    Raises:
        HTTPException: If token is invalid, expired, or wrong type
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        # Validate token type if specified
        if expected_type and payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenPayload(**payload)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def decode_token_unsafe(token: str) -> dict | None:
    """
    Decode a token without verification.
    Useful for extracting JTI for blacklisting expired tokens.

    WARNING: Do not use for authentication!
    """
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"verify_exp": False}
        )
    except JWTError:
        return None


# =============================================================================
# AUTHENTICATION DEPENDENCIES
# =============================================================================

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependency to extract current user ID from access token.

    Use in endpoints:
        @app.get("/protected")
        def protected(user_id: str = Depends(get_current_user_id)):
            ...
    """
    payload = verify_token(token, expected_type="access")
    if payload.sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    return payload.sub


async def get_token_payload(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """
    Dependency to get full token payload.

    Useful when you need access to JTI for blacklist checking.
    """
    return verify_token(token, expected_type="access")


def require_fresh_token(max_age_minutes: int = 5):
    """
    Dependency factory for endpoints requiring recently issued tokens.

    Usage:
        @app.post("/change-password")
        def change_password(
            payload: TokenPayload = Depends(require_fresh_token(5))
        ):
            ...
    """
    async def dependency(token: str = Depends(oauth2_scheme)) -> TokenPayload:
        payload = verify_token(token, expected_type="access")

        if payload.exp:
            # Calculate when token was issued
            issued_at = payload.exp - timedelta(
                minutes=settings.access_token_expire_minutes
            )
            age = datetime.now(timezone.utc) - issued_at

            if age > timedelta(minutes=max_age_minutes):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token too old. Please re-authenticate."
                )

        return payload

    return dependency
