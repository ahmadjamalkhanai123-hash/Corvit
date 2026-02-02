"""
Item Model
==========

SQLAlchemy model for items table.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..db.base import Base


class Item(Base):
    """Item database model."""

    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True, nullable=False)
    description = Column(String(1000))
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="items")

    def __repr__(self):
        return f"<Item(id={self.id}, title='{self.title}')>"
