"""
Auth Service
============

Business logic for authentication operations.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from ..models.user import User
from ..models.oauth_account import OAuthAccount
from ..core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, create_token_pair,
    verify_token, TokenPair
)
from ..core.exceptions import (
    NotFoundException, UnauthorizedException, AlreadyExistsException
)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        self.db = db

    def authenticate(self, username: str, password: str) -> User:
        """Authenticate user with username/email and password."""
        # Try username first, then email
        user = self.db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user:
            raise UnauthorizedException("Invalid credentials")

        if not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid credentials")

        if not user.is_active:
            raise UnauthorizedException("Account is disabled")

        return user

    def login(self, username: str, password: str) -> TokenPair:
        """Login and return token pair."""
        user = self.authenticate(username, password)
        return create_token_pair(str(user.id))

    def refresh_tokens(self, refresh_token: str) -> TokenPair:
        """Refresh tokens using refresh token."""
        payload = verify_token(refresh_token, expected_type="refresh")
        return create_token_pair(payload.sub)

    def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str | None = None
    ) -> User:
        """Register a new user."""
        # Check existing
        if self.db.query(User).filter(User.email == email).first():
            raise AlreadyExistsException("Email already registered")
        if self.db.query(User).filter(User.username == username).first():
            raise AlreadyExistsException("Username already taken")

        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_or_create_oauth_user(
        self,
        provider: str,
        provider_user_id: str,
        email: str | None,
        name: str | None,
        picture: str | None
    ) -> User:
        """Get or create user from OAuth data."""
        # Check for existing OAuth account
        oauth = self.db.query(OAuthAccount).filter(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id
        ).first()

        if oauth:
            return oauth.user

        # Check if email exists
        user = None
        if email:
            user = self.db.query(User).filter(User.email == email).first()

        # Create new user if needed
        if not user:
            username = f"{provider}_{provider_user_id}"
            user = User(
                username=username,
                email=email,
                hashed_password="",  # OAuth users don't have password
                full_name=name
            )
            self.db.add(user)
            self.db.flush()

        # Create OAuth account link
        oauth = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            name=name,
            picture_url=picture
        )
        self.db.add(oauth)
        self.db.commit()
        self.db.refresh(user)
        return user

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> None:
        """Change user password."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("User not found")

        if not verify_password(current_password, user.hashed_password):
            raise UnauthorizedException("Current password is incorrect")

        user.hashed_password = get_password_hash(new_password)
        self.db.commit()


def get_auth_service(db: Session) -> AuthService:
    """Factory for dependency injection."""
    return AuthService(db)
