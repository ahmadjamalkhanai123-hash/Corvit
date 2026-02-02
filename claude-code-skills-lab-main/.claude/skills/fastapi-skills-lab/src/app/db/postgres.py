"""
PostgreSQL Database Configuration
=================================

Async PostgreSQL setup with asyncpg.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from ..core.config import settings


def get_postgres_url() -> str:
    """Build PostgreSQL async URL."""
    return (
        f"postgresql+asyncpg://"
        f"{getattr(settings, 'postgres_user', 'postgres')}:"
        f"{getattr(settings, 'postgres_password', 'password')}@"
        f"{getattr(settings, 'postgres_host', 'localhost')}:"
        f"{getattr(settings, 'postgres_port', 5432)}/"
        f"{getattr(settings, 'postgres_db', 'fastapi_db')}"
    )


def create_postgres_engine(url: str = None):
    """Create async PostgreSQL engine."""
    return create_async_engine(
        url or get_postgres_url(),
        pool_size=getattr(settings, 'pool_size', 5),
        max_overflow=getattr(settings, 'max_overflow', 10),
        pool_timeout=getattr(settings, 'pool_timeout', 30),
        pool_pre_ping=True,
        echo=getattr(settings, 'debug', False),
    )


def create_postgres_session_factory(engine=None):
    """Create async session factory."""
    if engine is None:
        engine = create_postgres_engine()

    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )


# Default instances
postgres_engine = None
PostgresSessionLocal = None


def init_postgres():
    """Initialize PostgreSQL connection."""
    global postgres_engine, PostgresSessionLocal
    postgres_engine = create_postgres_engine()
    PostgresSessionLocal = create_postgres_session_factory(postgres_engine)


async def get_postgres_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for PostgreSQL session."""
    if PostgresSessionLocal is None:
        init_postgres()

    async with PostgresSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_postgres():
    """Close PostgreSQL connection."""
    if postgres_engine:
        await postgres_engine.dispose()
