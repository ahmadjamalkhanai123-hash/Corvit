"""
User Endpoints
==============

User management endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ....db.session import get_db
from ....schemas.user import UserResponse, UserUpdate
from ....services.user_service import UserService
from ....core.security import get_current_user_id

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_current_user(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current logged-in user."""
    service = UserService(db)
    user = service.get_by_id(int(current_user_id))
    return user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_data: UserUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update current user's information."""
    service = UserService(db)
    user = service.update(int(current_user_id), user_data)
    return user


@router.get("", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all users (admin only in production)."""
    service = UserService(db)
    users = service.get_all(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    service = UserService(db)
    user = service.get_by_id(user_id)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete a user (can only delete own account)."""
    # Only allow deleting own account
    if int(current_user_id) != user_id:
        from ....core.exceptions import ForbiddenException
        raise ForbiddenException("You can only delete your own account")

    service = UserService(db)
    service.delete(user_id)
