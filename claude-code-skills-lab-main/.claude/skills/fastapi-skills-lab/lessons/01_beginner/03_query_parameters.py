"""
LESSON 3: Query Parameters
==========================

Query parameters are the key-value pairs after ? in URLs.
Example: /items?skip=0&limit=10

Key Concepts:
- Query parameters (automatic detection)
- Optional vs required parameters
- Default values
- Query parameter validation

To run:
    uv run uvicorn lessons.01_beginner.03_query_parameters:app --reload
"""

from fastapi import FastAPI, Query

app = FastAPI(title="Query Parameters Lesson")


# Basic query parameters with defaults
@app.get("/items")
def list_items(skip: int = 0, limit: int = 10):
    """
    List items with pagination.

    Query parameters are automatically detected when they're
    not part of the path.

    Try: /items (uses defaults: skip=0, limit=10)
    Try: /items?skip=5&limit=20
    """
    # Simulating a database with fake items
    fake_items = [f"Item {i}" for i in range(100)]
    return {
        "skip": skip,
        "limit": limit,
        "items": fake_items[skip:skip + limit]
    }


# Required query parameter (no default value)
@app.get("/search")
def search(q: str):
    """
    Search endpoint - 'q' is required.

    Try: /search (returns error - q is required)
    Try: /search?q=python
    """
    return {"query": q, "results": [f"Result for '{q}' #{i}" for i in range(3)]}


# Optional query parameter using None as default
@app.get("/users")
def list_users(
    active: bool | None = None,
    role: str | None = None
):
    """
    List users with optional filters.

    Try: /users
    Try: /users?active=true
    Try: /users?role=admin
    Try: /users?active=true&role=admin
    """
    filters = {}
    if active is not None:
        filters["active"] = active
    if role is not None:
        filters["role"] = role

    return {
        "filters_applied": filters,
        "message": "Users filtered" if filters else "All users"
    }


# Query parameter validation with Query()
@app.get("/products")
def list_products(
    q: str | None = Query(
        default=None,
        min_length=2,
        max_length=50,
        description="Search query for products"
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=10, ge=1, le=100, description="Items per page")
):
    """
    List products with validated query parameters.

    - q: optional search, 2-50 characters if provided
    - page: must be >= 1
    - size: must be 1-100
    """
    return {
        "search_query": q,
        "page": page,
        "page_size": size,
        "message": f"Showing page {page} with {size} items"
    }


# Multiple values for same query parameter
@app.get("/items/filter")
def filter_items(
    tags: list[str] = Query(default=[], description="Filter by tags")
):
    """
    Filter items by multiple tags.

    Try: /items/filter?tags=python&tags=fastapi&tags=api
    """
    return {
        "tags": tags,
        "message": f"Filtering by {len(tags)} tags"
    }


"""
EXERCISE 1:
-----------
Create an endpoint `/books` with query parameters:
- author (optional string)
- year (optional integer, must be 1900-2024)
- available (optional boolean)

EXERCISE 2:
-----------
Create an endpoint `/articles` that accepts multiple category IDs
as a list query parameter.
"""
