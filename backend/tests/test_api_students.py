"""Tests for students API: CRUD, pagination, search, attendance, fees."""

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
        "username": f"admin_{unique}",
        "email": f"admin_{unique}@corvit.edu.pk",
        "password": "adminpass123",
        "role": "admin",
    })
    resp = await client.post("/api/auth/login", json={
        "username": f"admin_{unique}",
        "password": "adminpass123",
    })
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def student_token(client):
    """Create a student user and return JWT."""
    unique = str(uuid.uuid4())[:8]
    await client.post("/api/auth/register", json={
        "username": f"student_{unique}",
        "email": f"student_{unique}@corvit.edu.pk",
        "password": "studentpass123",
        "role": "student",
    })
    resp = await client.post("/api/auth/login", json={
        "username": f"student_{unique}",
        "password": "studentpass123",
    })
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_student(client, admin_token):
    """Admin can create a student."""
    unique = str(uuid.uuid4())[:8]
    resp = await client.post("/api/students", json={
        "name": f"Test Student {unique}",
        "email": f"student_{unique}@example.com",
        "phone": "03001234567",
    }, headers=auth_headers(admin_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == f"Test Student {unique}"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_student_read_only_for_non_admin(client, student_token, admin_token):
    """Non-admin can read but not write students."""
    unique = str(uuid.uuid4())[:8]

    # Create as admin
    create_resp = await client.post("/api/students", json={
        "name": f"ReadOnly {unique}",
        "email": f"readonly_{unique}@example.com",
        "phone": "03001234567",
    }, headers=auth_headers(admin_token))
    assert create_resp.status_code == 201
    student_id = create_resp.json()["id"]

    # Student can read
    resp = await client.get(f"/api/students/{student_id}", headers=auth_headers(student_token))
    assert resp.status_code == 200

    # Student cannot create
    resp = await client.post("/api/students", json={
        "name": "Unauthorized",
        "email": "unauth@example.com",
        "phone": "03001234567",
    }, headers=auth_headers(student_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_students_pagination(client, admin_token):
    """List students with pagination."""
    resp = await client.get("/api/students?page=1&limit=5", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "pages" in data


@pytest.mark.asyncio
async def test_update_student(client, admin_token):
    """Admin can update a student."""
    unique = str(uuid.uuid4())[:8]
    create_resp = await client.post("/api/students", json={
        "name": f"Before {unique}",
        "email": f"before_{unique}@example.com",
        "phone": "03001234567",
    }, headers=auth_headers(admin_token))
    student_id = create_resp.json()["id"]

    resp = await client.put(f"/api/students/{student_id}", json={
        "name": f"After {unique}",
    }, headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert resp.json()["name"] == f"After {unique}"


@pytest.mark.asyncio
async def test_delete_student(client, admin_token):
    """Admin can delete a student without active enrollments."""
    unique = str(uuid.uuid4())[:8]
    create_resp = await client.post("/api/students", json={
        "name": f"Delete {unique}",
        "email": f"delete_{unique}@example.com",
        "phone": "03001234567",
    }, headers=auth_headers(admin_token))
    student_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/students/{student_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 204

    # Verify deleted
    resp = await client.get(f"/api/students/{student_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_student_not_found(client, admin_token):
    """Getting a non-existent student returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/students/{fake_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 404
