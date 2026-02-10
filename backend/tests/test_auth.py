"""Tests for authentication: register, login, JWT, role-based access."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import app
from src.auth.jwt_handler import create_access_token, verify_token


# ── JWT unit tests ──────────────────────────────────────────────────────


def test_create_and_verify_token():
    """Token round-trip: create → verify."""
    token = create_access_token({"sub": "550e8400-e29b-41d4-a716-446655440000", "role": "admin"})
    data = verify_token(token)
    assert str(data.user_id) == "550e8400-e29b-41d4-a716-446655440000"
    assert data.role == "admin"


def test_verify_token_missing_claims():
    """Token without required claims should raise."""
    from jose import jwt as jose_jwt, JWTError

    token = jose_jwt.encode({"sub": "test"}, "corvit-dev-secret-change-in-production", algorithm="HS256")
    with pytest.raises(JWTError):
        verify_token(token)


def test_verify_invalid_token():
    """Completely invalid token should raise."""
    from jose import JWTError

    with pytest.raises(JWTError):
        verify_token("not-a-valid-token")


# ── API integration tests ──────────────────────────────────────────────


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_register_and_login(client):
    """Register a user, then login and get a token."""
    import uuid

    unique = str(uuid.uuid4())[:8]

    # Register
    resp = await client.post("/api/auth/register", json={
        "username": f"testuser_{unique}",
        "email": f"test_{unique}@corvit.edu.pk",
        "password": "testpass123",
        "role": "admin",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == f"testuser_{unique}"
    assert data["role"] == "admin"

    # Login
    resp = await client.post("/api/auth/login", json={
        "username": f"testuser_{unique}",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    token_data = resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["user"]["username"] == f"testuser_{unique}"

    # Me
    resp = await client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {token_data['access_token']}"
    })
    assert resp.status_code == 200
    me_data = resp.json()
    assert me_data["username"] == f"testuser_{unique}"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Login with wrong password should return 401."""
    resp = await client.post("/api/auth/login", json={
        "username": "nonexistent_user",
        "password": "wrongpass",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token(client):
    """GET /me without token should return 401 or 403."""
    resp = await client.get("/api/auth/me")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    """Registering same username twice should return 409."""
    import uuid

    unique = str(uuid.uuid4())[:8]
    user_data = {
        "username": f"dup_{unique}",
        "email": f"dup_{unique}@corvit.edu.pk",
        "password": "pass123",
        "role": "student",
    }

    resp1 = await client.post("/api/auth/register", json=user_data)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/auth/register", json=user_data)
    assert resp2.status_code == 409
