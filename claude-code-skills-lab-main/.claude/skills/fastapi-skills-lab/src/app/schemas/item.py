"""
Item Schemas
============

Pydantic schemas for item data validation.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

if TYPE_CHECKING:
    from .user import UserResponse


class ItemBase(BaseModel):
    """Base item schema with common fields."""
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(gt=0)


class ItemCreate(ItemBase):
    """Schema for creating a new item."""
    pass


class ItemUpdate(BaseModel):
    """Schema for updating an item - all fields optional."""
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    price: float | None = Field(default=None, gt=0)
    is_active: bool | None = None


class ItemResponse(ItemBase):
    """Schema for item responses - includes id and metadata."""
    id: int
    is_active: bool
    owner_id: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ItemWithOwner(ItemResponse):
    """Item response with owner information."""
    owner: "UserResponse | None" = None
