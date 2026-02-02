"""
LESSON 12: Database Configuration - PostgreSQL & MySQL
======================================================

Configure FastAPI with production databases.

Key Concepts:
- PostgreSQL with asyncpg
- MySQL/MariaDB with aiomysql
- Connection pooling
- Environment-based config
- Async database sessions

To run:
    uv run uvicorn lessons.02_intermediate.06_database_config:app --reload
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base, Session


# =============================================================================
# Configuration
# =============================================================================

class DatabaseSettings(BaseSettings):
    """Database configuration from environment."""

    # Database type: sqlite, postgresql, mysql
    db_type: str = "sqlite"

    # SQLite (default for development)
    sqlite_url: str = "sqlite:///./demo.db"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    postgres_db: str = "fastapi_db"

    # MySQL
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "password"
    mysql_db: str = "fastapi_db"

    # Connection pool
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30

    class Config:
        env_prefix = "DB_"
        env_file = ".env"

    @property
    def database_url(self) -> str:
        """Get database URL based on type."""
        if self.db_type == "postgresql":
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        elif self.db_type == "mysql":
            return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"
        return self.sqlite_url

    @property
    def async_database_url(self) -> str:
        """Get async database URL."""
        if self.db_type == "postgresql":
            return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        elif self.db_type == "mysql":
            return f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"
        return f"sqlite+aiosqlite:///{self.sqlite_url.replace('sqlite:///', '')}"


settings = DatabaseSettings()


# =============================================================================
# Synchronous Database Setup
# =============================================================================

Base = declarative_base()

# Sync engine with connection pooling
sync_engine = create_engine(
    settings.database_url,
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_timeout=settings.pool_timeout,
    pool_pre_ping=True,  # Verify connections
    echo=False,  # Set True for SQL logging
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)


def get_sync_db() -> Session:
    """Sync database session dependency."""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
# Asynchronous Database Setup (Recommended)
# =============================================================================

async_engine = create_async_engine(
    settings.async_database_url,
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_timeout=settings.pool_timeout,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Async database session dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# =============================================================================
# Sample Model
# =============================================================================

class Item(Base):
    """Sample item model."""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))


class ItemCreate(BaseModel):
    name: str
    description: str | None = None


class ItemResponse(BaseModel):
    id: int
    name: str
    description: str | None

    class Config:
        from_attributes = True


# =============================================================================
# Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup."""
    # For sync engine
    Base.metadata.create_all(bind=sync_engine)
    yield


app = FastAPI(
    title="Database Configuration Demo",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Show current database configuration."""
    return {
        "db_type": settings.db_type,
        "sync_url": settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url,
        "pool_size": settings.pool_size,
    }


@app.get("/health")
async def health(db: AsyncSession = Depends(get_async_db)):
    """Check database connection."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_async_db)):
    """Create item (async)."""
    db_item = Item(**item.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@app.get("/items", response_model=list[ItemResponse])
async def list_items(db: AsyncSession = Depends(get_async_db)):
    """List items (async)."""
    from sqlalchemy import select
    result = await db.execute(select(Item))
    return result.scalars().all()


# =============================================================================
# Key Concepts
# =============================================================================

"""
DATABASE URLS:
- SQLite: sqlite:///./app.db
- PostgreSQL: postgresql://user:pass@host:5432/db
- MySQL: mysql+pymysql://user:pass@host:3306/db

ASYNC DRIVERS:
- PostgreSQL: asyncpg (postgresql+asyncpg://)
- MySQL: aiomysql (mysql+aiomysql://)
- SQLite: aiosqlite (sqlite+aiosqlite://)

CONNECTION POOLING:
- pool_size: Number of persistent connections
- max_overflow: Extra connections when pool full
- pool_timeout: Wait time for connection
- pool_pre_ping: Verify connection before use

BEST PRACTICES:
- Use async for high-concurrency APIs
- Configure pool based on expected load
- Use environment variables for credentials
- Enable pool_pre_ping for reliability
"""
