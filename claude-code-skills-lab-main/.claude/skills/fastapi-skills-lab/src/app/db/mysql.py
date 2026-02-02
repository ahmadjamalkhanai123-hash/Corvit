"""
MySQL Database Configuration
============================

Async MySQL setup with aiomysql.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from ..core.config import settings


def get_mysql_url() -> str:
    """Build MySQL async URL."""
    return (
        f"mysql+aiomysql://"
        f"{getattr(settings, 'mysql_user', 'root')}:"
        f"{getattr(settings, 'mysql_password', 'password')}@"
        f"{getattr(settings, 'mysql_host', 'localhost')}:"
        f"{getattr(settings, 'mysql_port', 3306)}/"
        f"{getattr(settings, 'mysql_db', 'fastapi_db')}"
    )


def create_mysql_engine(url: str = None):
    """Create async MySQL engine."""
    return create_async_engine(
        url or get_mysql_url(),
        pool_size=getattr(settings, 'pool_size', 5),
        max_overflow=getattr(settings, 'max_overflow', 10),
        pool_timeout=getattr(settings, 'pool_timeout', 30),
        pool_pre_ping=True,
        echo=getattr(settings, 'debug', False),
    )


def create_mysql_session_factory(engine=None):
    """Create async session factory."""
    if engine is None:
        engine = create_mysql_engine()

    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )


# Default instances
mysql_engine = None
MySQLSessionLocal = None


def init_mysql():
    """Initialize MySQL connection."""
    global mysql_engine, MySQLSessionLocal
    mysql_engine = create_mysql_engine()
    MySQLSessionLocal = create_mysql_session_factory(mysql_engine)


async def get_mysql_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for MySQL session."""
    if MySQLSessionLocal is None:
        init_mysql()

    async with MySQLSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_mysql():
    """Close MySQL connection."""
    if mysql_engine:
        await mysql_engine.dispose()
