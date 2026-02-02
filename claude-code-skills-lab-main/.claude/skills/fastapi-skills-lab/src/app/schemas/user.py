"""
User Schemas
============

Pydantic schemas for user data validation.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    full_name: str | None = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating a user - all fields optional."""
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=50)
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user responses - includes id and timestamps."""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """Schema for user in database - includes hashed password."""
    hashed_password: str


class Token(BaseModel):
    """OAuth2 token response."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str | None = None
