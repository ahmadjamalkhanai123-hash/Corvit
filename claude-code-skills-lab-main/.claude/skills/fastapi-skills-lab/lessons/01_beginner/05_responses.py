"""
LESSON 5: Responses & Error Handling
====================================

Learn how to control responses and handle errors properly.

Key Concepts:
- Response models
- Status codes
- HTTP exceptions
- Custom responses
- Response headers

To run:
    uv run uvicorn lessons.01_beginner.05_responses:app --reload
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Responses Lesson")


# Define response models
class ItemBase(BaseModel):
    name: str
    price: float


class ItemCreate(ItemBase):
    """Model for creating items - used in request body"""
    description: str | None = None


class ItemResponse(ItemBase):
    """Model for responses - includes id"""
    id: int
    description: str | None = None

    model_config = {"from_attributes": True}


# Fake database
fake_db = {
    1: {"id": 1, "name": "Laptop", "price": 999.99, "description": "Powerful laptop"},
    2: {"id": 2, "name": "Mouse", "price": 29.99, "description": "Wireless mouse"},
}
next_id = 3


# Response model - only return specified fields
@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    """
    Get an item by ID.

    response_model=ItemResponse ensures:
    1. Response is validated against the model
    2. Only specified fields are returned
    3. Documentation shows expected response shape
    """
    if item_id not in fake_db:
        # HTTPException for error responses
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    return fake_db[item_id]


# Return list of items
@app.get("/items", response_model=list[ItemResponse])
def list_items():
    """Get all items. Response is a list of ItemResponse."""
    return list(fake_db.values())


# Custom status code
@app.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED  # 201 for created resources
)
def create_item(item: ItemCreate):
    """
    Create a new item.

    Returns 201 Created status code on success.
    """
    global next_id
    new_item = {"id": next_id, **item.model_dump()}
    fake_db[next_id] = new_item
    next_id += 1
    return new_item


# Different status codes for different scenarios
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    """
    Delete an item.

    Returns 204 No Content on success (no response body).
    """
    if item_id not in fake_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    del fake_db[item_id]
    # No return needed for 204


# HTTPException with custom headers
@app.get("/protected")
def protected_resource():
    """
    A protected endpoint that always returns 401.
    Demonstrates HTTPException with custom headers.
    """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"}
    )


# Multiple possible responses (for documentation)
@app.get(
    "/items/{item_id}/details",
    response_model=ItemResponse,
    responses={
        404: {"description": "Item not found"},
        403: {"description": "Not authorized to view this item"}
    }
)
def get_item_details(item_id: int, auth_token: str | None = None):
    """
    Get item details with authentication.

    The `responses` parameter documents possible error responses.
    """
    if auth_token is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization token required"
        )
    if item_id not in fake_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )
    return fake_db[item_id]


# Custom JSON response with headers
@app.get("/custom-response")
def custom_response():
    """
    Return a custom JSONResponse with extra headers.
    """
    return JSONResponse(
        content={"message": "Custom response with headers"},
        headers={
            "X-Custom-Header": "Hello!",
            "X-API-Version": "1.0"
        }
    )


# Common HTTP Status Codes Reference
"""
COMMON STATUS CODES:
-------------------
200 OK              - Success (default for GET)
201 Created         - Resource created (POST)
204 No Content      - Success with no body (DELETE)
400 Bad Request     - Invalid request
401 Unauthorized    - Authentication required
403 Forbidden       - Authenticated but not authorized
404 Not Found       - Resource doesn't exist
422 Unprocessable   - Validation error (FastAPI default)
500 Server Error    - Internal server error
"""


"""
EXERCISE 1:
-----------
Create CRUD endpoints for a "User" resource:
- GET /users - list all users
- GET /users/{id} - get user by id
- POST /users - create user (201)
- PUT /users/{id} - update user
- DELETE /users/{id} - delete user (204)

Use proper response models and status codes.

EXERCISE 2:
-----------
Add custom error responses that include an error code
and timestamp in addition to the message.
"""
