"""
Item Endpoints
==============

Item management endpoints.
"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from ....db.session import get_db
from ....schemas.item import ItemCreate, ItemUpdate, ItemResponse
from ....services.item_service import ItemService
from ....core.security import get_current_user_id

router = APIRouter()


@router.get("", response_model=list[ItemResponse])
def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    owner_id: int | None = None,
    db: Session = Depends(get_db)
):
    """
    Get all items.

    - **skip**: Number of items to skip (pagination)
    - **limit**: Maximum number of items to return
    - **owner_id**: Filter by owner ID (optional)
    """
    service = ItemService(db)
    items = service.get_all(skip=skip, limit=limit, owner_id=owner_id)
    return items


@router.get("/my-items", response_model=list[ItemResponse])
def list_my_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get all items owned by the current user."""
    service = ItemService(db)
    items = service.get_all(skip=skip, limit=limit, owner_id=int(current_user_id))
    return items


@router.get("/search", response_model=list[ItemResponse])
def search_items(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search items by title or description."""
    service = ItemService(db)
    items = service.search(query=q, skip=skip, limit=limit)
    return items


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get a specific item by ID."""
    service = ItemService(db)
    item = service.get_by_id(item_id)
    return item


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: ItemCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new item.

    - **title**: Item title (1-200 characters)
    - **description**: Item description (optional)
    - **price**: Item price (must be > 0)
    """
    service = ItemService(db)
    item = service.create(item_data, owner_id=int(current_user_id))
    return item


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item_data: ItemUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update an item (must be the owner)."""
    service = ItemService(db)
    item = service.update(item_id, item_data, current_user_id=int(current_user_id))
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete an item (must be the owner)."""
    service = ItemService(db)
    service.delete(item_id, current_user_id=int(current_user_id))
