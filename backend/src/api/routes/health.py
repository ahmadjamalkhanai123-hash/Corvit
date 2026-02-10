import time
from datetime import UTC, datetime

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.common import HealthCheckService, HealthResponse
from src.config.settings import get_settings
from src.database.connection import async_session_factory

router = APIRouter(tags=["health"])


async def _check_postgres() -> HealthCheckService:
    try:
        start = time.monotonic()
        async with async_session_factory() as session:
            session: AsyncSession
            await session.execute(text("SELECT 1"))
        latency = (time.monotonic() - start) * 1000
        return HealthCheckService(status="up", latency_ms=round(latency, 1))
    except Exception as e:
        return HealthCheckService(status="down", error=str(e))


async def _check_redis() -> HealthCheckService:
    settings = get_settings()
    try:
        start = time.monotonic()
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        latency = (time.monotonic() - start) * 1000
        await client.aclose()
        return HealthCheckService(status="up", latency_ms=round(latency, 1))
    except Exception as e:
        return HealthCheckService(status="down", error=str(e))


async def _check_ollama() -> HealthCheckService:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                has_model = any(settings.ollama_model in m for m in models)
                return HealthCheckService(
                    status="up" if has_model else "degraded",
                    model=settings.ollama_model if has_model else None,
                )
            return HealthCheckService(status="down", error=f"HTTP {resp.status_code}")
    except Exception as e:
        return HealthCheckService(status="down", error=str(e))


async def _check_vectordb() -> HealthCheckService:
    settings = get_settings()
    try:
        import chromadb

        client = chromadb.PersistentClient(path=settings.chroma_db_path)
        collections = client.list_collections()
        total_docs = sum(col.count() for col in collections)
        return HealthCheckService(
            status="up",
            collections=len(collections),
            documents=total_docs,
        )
    except Exception as e:
        return HealthCheckService(status="down", error=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check(response: Response):
    checks = {
        "postgres": await _check_postgres(),
        "redis": await _check_redis(),
        "ollama": await _check_ollama(),
        "vectordb": await _check_vectordb(),
    }

    all_up = all(c.status == "up" for c in checks.values())
    status = "healthy" if all_up else "degraded"

    if any(c.status == "down" for c in checks.values()):
        response.status_code = 503

    return HealthResponse(
        status=status,
        checks=checks,
        timestamp=datetime.now(UTC),
    )
