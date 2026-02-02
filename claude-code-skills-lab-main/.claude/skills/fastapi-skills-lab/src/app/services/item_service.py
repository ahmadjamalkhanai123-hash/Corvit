"""
Item Service
============

Business logic for item operations.
"""

from sqlalchemy.orm import Session

from ..models.item import Item
from ..schemas.item import ItemCreate, ItemUpdate
from ..core.exceptions import NotFoundException, ForbiddenException


class ItemService:
    """
    Service class for item operations.

    Encapsulates all business logic related to items.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, item_id: int) -> Item:
        """Get item by ID."""
        item = self.db.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise NotFoundException("Item", item_id)
        return item

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        owner_id: int | None = None
    ) -> list[Item]:
        """Get all items with optional filtering."""
        query = self.db.query(Item)

        if owner_id is not None:
            query = query.filter(Item.owner_id == owner_id)

        return query.offset(skip).limit(limit).all()

    def create(self, item_data: ItemCreate, owner_id: int) -> Item:
        """
        Create a new item.

        Args:
            item_data: Item creation data
            owner_id: ID of the user creating the item

        Returns:
            Created item
        """
        item = Item(
            **item_data.model_dump(),
            owner_id=owner_id
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(
        self,
        item_id: int,
        item_data: ItemUpdate,
        current_user_id: int
    ) -> Item:
        """
        Update an item.

        Args:
            item_id: Item ID to update
            item_data: Update data
            current_user_id: ID of the user making the update

        Returns:
            Updated item

        Raises:
            ForbiddenException: If user doesn't own the item
        """
        item = self.get_by_id(item_id)

        # Check ownership
        if item.owner_id != current_user_id:
            raise ForbiddenException("You can only update your own items")

        # Update fields
        update_data = item_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)

        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item_id: int, current_user_id: int) -> None:
        """
        Delete an item.

        Args:
            item_id: Item ID to delete
            current_user_id: ID of the user making the request

        Raises:
            ForbiddenException: If user doesn't own the item
        """
        item = self.get_by_id(item_id)

        # Check ownership
        if item.owner_id != current_user_id:
            raise ForbiddenException("You can only delete your own items")

        self.db.delete(item)
        self.db.commit()

    def search(self, query: str, skip: int = 0, limit: int = 100) -> list[Item]:
        """Search items by title or description."""
        return self.db.query(Item).filter(
            (Item.title.contains(query)) | (Item.description.contains(query))
        ).offset(skip).limit(limit).all()


def get_item_service(db: Session) -> ItemService:
    """Factory function for dependency injection."""
    return ItemService(db)
