from collections.abc import AsyncGenerator
from functools import lru_cache

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import Settings, get_settings
from src.database.connection import get_db as _get_db


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_db():
        yield session


@lru_cache
def get_settings_cached() -> Settings:
    return get_settings()


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    settings = get_settings()
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()
