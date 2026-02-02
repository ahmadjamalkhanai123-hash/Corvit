"""
Auth Endpoints
==============

Authentication endpoints for login/register.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ....db.session import get_db
from ....schemas.user import Token, UserCreate, UserResponse
from ....services.user_service import UserService
from ....core.security import create_access_token

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    - **email**: User's email address
    - **username**: Unique username (3-50 characters)
    - **password**: Password (min 8 characters)
    - **full_name**: Optional full name
    """
    service = UserService(db)
    user = service.create(user_data)
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login.

    Use username (or email) and password to get an access token.
    """
    service = UserService(db)
    user = service.authenticate(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}
