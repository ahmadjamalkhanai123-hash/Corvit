"""
LESSON 2: Path Parameters
=========================

Path parameters allow you to capture values from the URL path.

Key Concepts:
- Path parameters with {parameter_name}
- Type hints for automatic validation
- Multiple path parameters
- Path parameter validation

To run:
    uv run uvicorn lessons.01_beginner.02_path_parameters:app --reload
"""

from fastapi import FastAPI, Path

app = FastAPI(title="Path Parameters Lesson")


# Basic path parameter
@app.get("/users/{user_id}")
def get_user(user_id: int):
    """
    Get a user by their ID.

    The `user_id` is captured from the URL.
    Type hint `int` means FastAPI will:
    1. Validate that user_id is a valid integer
    2. Convert it from string to int automatically

    Try: /users/123 (works)
    Try: /users/abc (returns validation error)
    """
    return {"user_id": user_id, "message": f"You requested user {user_id}"}


# String path parameter
@app.get("/items/{item_name}")
def get_item(item_name: str):
    """Get an item by name."""
    return {"item_name": item_name, "item_name_upper": item_name.upper()}


# Multiple path parameters
@app.get("/users/{user_id}/posts/{post_id}")
def get_user_post(user_id: int, post_id: int):
    """
    Get a specific post from a specific user.
    Demonstrates multiple path parameters.
    """
    return {
        "user_id": user_id,
        "post_id": post_id,
        "message": f"Post {post_id} by user {user_id}"
    }


# Path parameter with validation using Path()
@app.get("/products/{product_id}")
def get_product(
    product_id: int = Path(
        ...,  # ... means required
        title="Product ID",
        description="The unique identifier of the product",
        ge=1,  # greater than or equal to 1
        le=10000  # less than or equal to 10000
    )
):
    """
    Get a product with validated ID.

    The product_id must be between 1 and 10000.
    """
    return {"product_id": product_id, "name": f"Product #{product_id}"}


# Fixed path should come BEFORE path parameters
# Order matters in FastAPI!
@app.get("/users/me")  # This must come before /users/{user_id}
def get_current_user():
    """Get the current logged-in user."""
    return {"user": "current_user", "message": "This is you!"}


"""
EXERCISE 1:
-----------
Create an endpoint `/categories/{category_name}/items/{item_id}`
that returns both the category name and item ID.

EXERCISE 2:
-----------
Create an endpoint `/age/{age}` where age must be between 0 and 150.
Use Path() for validation.
"""
