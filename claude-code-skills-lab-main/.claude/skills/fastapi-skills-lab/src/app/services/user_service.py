"""
User Service
============

Business logic for user operations.
"""

from sqlalchemy.orm import Session

from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..core.security import get_password_hash, verify_password
from ..core.exceptions import NotFoundException, AlreadyExistsException


class UserService:
    """
    Service class for user operations.

    Encapsulates all business logic related to users.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User:
        """Get user by ID."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("User", user_id)
        return user

    def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination."""
        return self.db.query(User).offset(skip).limit(limit).all()

    def create(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user

        Raises:
            AlreadyExistsException: If email or username already exists
        """
        # Check for existing email
        if self.get_by_email(user_data.email):
            raise AlreadyExistsException("User", "email")

        # Check for existing username
        if self.get_by_username(user_data.username):
            raise AlreadyExistsException("User", "username")

        # Create user with hashed password
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password)
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user_id: int, user_data: UserUpdate) -> User:
        """
        Update a user.

        Args:
            user_id: User ID to update
            user_data: Update data

        Returns:
            Updated user
        """
        user = self.get_by_id(user_id)

        # Update fields that were provided
        update_data = user_data.model_dump(exclude_unset=True)

        # Hash password if provided
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: int) -> None:
        """Delete a user."""
        user = self.get_by_id(user_id)
        self.db.delete(user)
        self.db.commit()

    def authenticate(self, username: str, password: str) -> User | None:
        """
        Authenticate a user.

        Args:
            username: Username or email
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise
        """
        # Try to find by username or email
        user = self.get_by_username(username)
        if not user:
            user = self.get_by_email(username)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user


def get_user_service(db: Session) -> UserService:
    """Factory function for dependency injection."""
    return UserService(db)
