"""
OAuth Account Model
===================

Links external OAuth provider accounts to local users.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.base import Base


class OAuthAccount(Base):
    """OAuth provider account linked to a user."""

    __tablename__ = "oauth_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False, index=True)  # google, github, microsoft
    provider_user_id = Column(String(255), nullable=False)
    email = Column(String(255))
    name = Column(String(255))
    picture_url = Column(String(500))
    access_token = Column(Text)  # Encrypted in production
    refresh_token = Column(Text)  # Encrypted in production
    token_expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="oauth_accounts")

    class Config:
        # Unique constraint: one account per provider per user
        __table_args__ = (
            {"unique": ["user_id", "provider"]},
        )
