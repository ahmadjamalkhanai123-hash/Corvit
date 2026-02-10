import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import app
from src.config.settings import Settings


@pytest.fixture
def test_settings():
    return Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://corvit:corvit123@localhost:5432/corvit_db",
        debug=False,
    )


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
