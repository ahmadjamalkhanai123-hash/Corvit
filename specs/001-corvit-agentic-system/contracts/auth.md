# API Contract: Authentication

## POST /api/auth/register

**Auth**: None
**Description**: Create new user account

**Request**:
```json
{
  "username": "admin",
  "email": "admin@corvit.edu.pk",
  "password": "securepass123",
  "role": "admin"
}
```

**Response 201**:
```json
{
  "id": "uuid",
  "username": "admin",
  "email": "admin@corvit.edu.pk",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-02-02T10:00:00Z"
}
```

**Response 409**: `{ "detail": "Username already exists", "error_code": "DUPLICATE_USERNAME" }`

---

## POST /api/auth/login

**Auth**: None
**Description**: Authenticate and receive JWT token

**Request**:
```json
{
  "username": "admin",
  "password": "securepass123"
}
```

**Response 200**:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 28800,
  "user": {
    "id": "uuid",
    "username": "admin",
    "role": "admin"
  }
}
```

**Response 401**: `{ "detail": "Invalid credentials", "error_code": "INVALID_CREDENTIALS" }`

---

## GET /api/auth/me

**Auth**: Bearer JWT (any role)
**Description**: Get current user info

**Response 200**:
```json
{
  "id": "uuid",
  "username": "admin",
  "email": "admin@corvit.edu.pk",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-02-02T10:00:00Z"
}
```

**Response 401**: `{ "detail": "Not authenticated", "error_code": "NOT_AUTHENTICATED" }`
