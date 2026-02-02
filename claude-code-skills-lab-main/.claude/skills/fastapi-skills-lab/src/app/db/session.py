"""
Database Session Management
===========================

SQLAlchemy engine and session configuration.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends

from ..core.config import settings

# Create engine
engine = create_engine(
    settings.database_url,
    # SQLite specific
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    # Pool settings for production
    pool_pre_ping=True,  # Verify connections before using
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency that provides a database session.

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...

    The session is automatically closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Type alias for dependency injection
DBSession = Session
