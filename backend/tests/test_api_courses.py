"""Tests for courses API: CRUD, batch listing."""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def admin_token(client):
    """Create an admin user and return JWT."""
    unique = str(uuid.uuid4())[:8]
    await client.post("/api/auth/register", json={
        "username": f"courseadmin_{unique}",
        "email": f"courseadmin_{unique}@corvit.edu.pk",
        "password": "adminpass123",
        "role": "admin",
    })
    resp = await client.post("/api/auth/login", json={
        "username": f"courseadmin_{unique}",
        "password": "adminpass123",
    })
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_course(client, admin_token):
    """Admin can create a course."""
    unique = str(uuid.uuid4())[:8]
    resp = await client.post("/api/courses", json={
        "name": f"Test Course {unique}",
        "code": f"TC-{unique}",
        "duration_weeks": 12,
        "fee_amount": 25000.00,
        "description": "A test course",
        "category": "Testing",
    }, headers=auth_headers(admin_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == f"Test Course {unique}"
    assert data["fee_amount"] == 25000.00


@pytest.mark.asyncio
async def test_list_courses(client, admin_token):
    """List courses with pagination."""
    resp = await client.get("/api/courses?page=1&limit=10", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_update_course(client, admin_token):
    """Admin can update a course."""
    unique = str(uuid.uuid4())[:8]
    create_resp = await client.post("/api/courses", json={
        "name": f"Update Course {unique}",
        "code": f"UC-{unique}",
        "duration_weeks": 8,
        "fee_amount": 15000.00,
    }, headers=auth_headers(admin_token))
    course_id = create_resp.json()["id"]

    resp = await client.put(f"/api/courses/{course_id}", json={
        "fee_amount": 20000.00,
    }, headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert resp.json()["fee_amount"] == 20000.00


@pytest.mark.asyncio
async def test_delete_course(client, admin_token):
    """Admin can delete a course without active batches."""
    unique = str(uuid.uuid4())[:8]
    create_resp = await client.post("/api/courses", json={
        "name": f"Delete Course {unique}",
        "code": f"DC-{unique}",
        "duration_weeks": 4,
        "fee_amount": 5000.00,
    }, headers=auth_headers(admin_token))
    course_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/courses/{course_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_duplicate_course_code(client, admin_token):
    """Creating a course with duplicate code returns 409."""
    unique = str(uuid.uuid4())[:8]
    course_data = {
        "name": f"Dup Course {unique}",
        "code": f"DUP-{unique}",
        "duration_weeks": 8,
        "fee_amount": 10000.00,
    }

    resp1 = await client.post("/api/courses", json=course_data, headers=auth_headers(admin_token))
    assert resp1.status_code == 201

    resp2 = await client.post("/api/courses", json=course_data, headers=auth_headers(admin_token))
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_get_course_batches(client, admin_token):
    """Get batches for a course."""
    unique = str(uuid.uuid4())[:8]
    create_resp = await client.post("/api/courses", json={
        "name": f"Batch Course {unique}",
        "code": f"BC-{unique}",
        "duration_weeks": 12,
        "fee_amount": 25000.00,
    }, headers=auth_headers(admin_token))
    course_id = create_resp.json()["id"]

    resp = await client.get(f"/api/courses/{course_id}/batches", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["course_id"] == course_id
    assert "batches" in data
