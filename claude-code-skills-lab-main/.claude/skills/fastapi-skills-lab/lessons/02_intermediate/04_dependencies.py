"""
LESSON 10: Dependency Injection
===============================

Dependencies are a powerful FastAPI feature for code reuse,
separation of concerns, and testability.

Key Concepts:
- Function dependencies
- Class dependencies
- Nested dependencies
- Scoped dependencies
- Testing with dependency overrides

To run:
    uv run uvicorn lessons.02_intermediate.04_dependencies:app --reload
"""

from fastapi import FastAPI, Depends, HTTPException, Header, Query
from pydantic import BaseModel

app = FastAPI(title="Dependencies Lesson")


# Simple function dependency
def get_query_params(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    A simple dependency that provides common query parameters.

    Instead of repeating these in every endpoint, define once
    and use everywhere with Depends().
    """
    return {"skip": skip, "limit": limit}


@app.get("/items")
def list_items(params: dict = Depends(get_query_params)):
    """Uses the pagination dependency."""
    items = [f"Item {i}" for i in range(100)]
    return {
        "items": items[params["skip"]:params["skip"] + params["limit"]],
        "skip": params["skip"],
        "limit": params["limit"]
    }


@app.get("/products")
def list_products(params: dict = Depends(get_query_params)):
    """Same dependency, different endpoint."""
    products = [f"Product {i}" for i in range(50)]
    return {
        "products": products[params["skip"]:params["skip"] + params["limit"]],
        **params
    }


# Class-based dependency
class Pagination:
    """
    Class-based dependency for pagination.

    Benefits over function:
    - Can hold state
    - More complex initialization
    - Better IDE support
    """
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(10, ge=1, le=100, description="Items per page")
    ):
        self.page = page
        self.size = size
        self.skip = (page - 1) * size

    def paginate(self, items: list) -> dict:
        """Helper method to paginate a list."""
        total = len(items)
        pages = (total + self.size - 1) // self.size
        return {
            "items": items[self.skip:self.skip + self.size],
            "page": self.page,
            "size": self.size,
            "total": total,
            "pages": pages
        }


@app.get("/users")
def list_users(pagination: Pagination = Depends()):
    """Uses class-based pagination dependency."""
    fake_users = [{"id": i, "name": f"User {i}"} for i in range(100)]
    return pagination.paginate(fake_users)


# Dependency for authentication/authorization
def verify_token(authorization: str = Header(...)):
    """
    Dependency that verifies the Authorization header.

    In real apps, this would validate JWT tokens.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]  # Remove "Bearer " prefix
    if token != "valid-token":  # Simplified validation
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"user_id": 1, "username": "authenticated_user"}


@app.get("/protected")
def protected_route(user: dict = Depends(verify_token)):
    """Protected endpoint - requires valid token."""
    return {"message": f"Hello, {user['username']}!", "user": user}


# Nested dependencies
def get_db():
    """Simulated database connection."""
    print("Opening database connection...")
    db = {"connection": "active"}
    try:
        yield db
    finally:
        print("Closing database connection...")


def get_current_user(
    user_data: dict = Depends(verify_token),
    db: dict = Depends(get_db)
):
    """
    Nested dependency - depends on both token verification and database.

    Dependencies can depend on other dependencies!
    """
    # In real app: fetch full user from database
    return {
        **user_data,
        "email": f"{user_data['username']}@example.com",
        "from_db": True
    }


@app.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Uses nested dependency chain."""
    return current_user


# Dependency that modifies request
class RequestContext:
    """Dependency that provides request context."""
    def __init__(self):
        import uuid
        self.request_id = str(uuid.uuid4())
        self.timestamp = __import__('datetime').datetime.now().isoformat()


@app.get("/context")
def with_context(ctx: RequestContext = Depends()):
    """Shows request context from dependency."""
    return {
        "request_id": ctx.request_id,
        "timestamp": ctx.timestamp
    }


# Shared dependency across all routes
def common_parameters(
    q: str | None = None,
    skip: int = 0,
    limit: int = 100
):
    return {"q": q, "skip": skip, "limit": limit}


# Multiple endpoints with same dependency
@app.get("/api/items")
def api_items(commons: dict = Depends(common_parameters)):
    return {"endpoint": "items", **commons}


@app.get("/api/products")
def api_products(commons: dict = Depends(common_parameters)):
    return {"endpoint": "products", **commons}


@app.get("/api/orders")
def api_orders(commons: dict = Depends(common_parameters)):
    return {"endpoint": "orders", **commons}


# Sub-dependencies with caching (use_cache)
call_count = 0

def expensive_operation():
    """Simulates an expensive operation."""
    global call_count
    call_count += 1
    print(f"Expensive operation called (count: {call_count})")
    return {"computed_value": 42, "call_count": call_count}


def dep_a(data: dict = Depends(expensive_operation)):
    return {"dep_a": True, **data}


def dep_b(data: dict = Depends(expensive_operation)):
    return {"dep_b": True, **data}


@app.get("/cached-deps")
def cached_dependencies(
    a: dict = Depends(dep_a),
    b: dict = Depends(dep_b)
):
    """
    Both dep_a and dep_b depend on expensive_operation.

    By default, expensive_operation is only called ONCE per request!
    This is dependency caching.
    """
    return {"a": a, "b": b, "note": "expensive_operation only called once"}


"""
DEPENDENCY INJECTION BENEFITS:
-----------------------------

1. Code Reuse: Write once, use everywhere
2. Separation of Concerns: Keep auth, db, etc. separate
3. Testability: Easy to mock/override in tests
4. Type Safety: IDE autocomplete and type checking
5. Automatic Documentation: Shown in OpenAPI docs


DEPENDENCY PATTERNS:
-------------------

1. Function Dependency: Simple, stateless
2. Class Dependency: Stateful, complex logic
3. Generator Dependency: Setup/teardown (yield)
4. Nested Dependencies: Compose smaller deps
5. Cached Dependencies: Avoid repeated computation


TESTING TIP:
-----------
Override dependencies in tests:

    from fastapi.testclient import TestClient

    def override_verify_token():
        return {"user_id": 99, "username": "test_user"}

    app.dependency_overrides[verify_token] = override_verify_token

    client = TestClient(app)
    response = client.get("/protected")


EXERCISE 1:
-----------
Create a RateLimiter class dependency that:
- Tracks requests per user
- Raises 429 if limit exceeded
- Can be configured with max requests

EXERCISE 2:
-----------
Create a DatabaseSession dependency that:
- Uses context manager (yield)
- Handles transaction commit/rollback
- Logs session lifecycle
"""
