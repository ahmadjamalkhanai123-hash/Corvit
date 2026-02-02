"""
Database Base
=============

Import all models here for Alembic migrations.
"""

from sqlalchemy.ext.declarative import declarative_base

# Base class for all models
Base = declarative_base()

# Import all models to register them with Base
# This is important for Alembic migrations
from ..models.user import User  # noqa
from ..models.item import Item  # noqa
