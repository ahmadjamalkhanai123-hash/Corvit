"""
LESSON 4: Request Body & Pydantic Models
=========================================

For POST, PUT, PATCH requests, you often need to send data
in the request body. FastAPI uses Pydantic for this.

Key Concepts:
- Pydantic models for data validation
- Request body parsing
- Nested models
- Field validation
- Response models

To run:
    uv run uvicorn lessons.01_beginner.04_request_body:app --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

app = FastAPI(title="Request Body Lesson")


# Basic Pydantic model
class Item(BaseModel):
    """
    Pydantic model for an Item.
    All fields are automatically validated.
    """
    name: str
    price: float
    description: str | None = None  # Optional field
    in_stock: bool = True  # Default value


# POST endpoint with request body
@app.post("/items")
def create_item(item: Item):
    """
    Create a new item.

    FastAPI will:
    1. Read the body as JSON
    2. Validate the data against Item model
    3. Convert types if needed
    4. Return validation errors if invalid

    Example request body:
    {
        "name": "Laptop",
        "price": 999.99,
        "description": "A powerful laptop",
        "in_stock": true
    }
    """
    return {
        "message": "Item created successfully",
        "item": item,
        "item_dict": item.model_dump()  # Convert to dictionary
    }


# Model with validation using Field()
class Product(BaseModel):
    name: str = Field(
        ...,  # Required
        min_length=2,
        max_length=100,
        description="Product name"
    )
    price: float = Field(
        ...,
        gt=0,  # Greater than 0
        description="Product price in USD"
    )
    quantity: int = Field(
        default=0,
        ge=0,  # Greater than or equal to 0
        description="Available quantity"
    )
    category: str = Field(
        default="general",
        description="Product category"
    )


@app.post("/products")
def create_product(product: Product):
    """Create a product with validated fields."""
    return {"product": product}


# Nested models
class Address(BaseModel):
    street: str
    city: str
    country: str
    zip_code: str


class User(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str  # Note: Use EmailStr for email validation
    full_name: str | None = None
    address: Address | None = None  # Nested model
    tags: list[str] = []  # List of strings


@app.post("/users")
def create_user(user: User):
    """
    Create a user with optional nested address.

    Example request body:
    {
        "username": "johndoe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "address": {
            "street": "123 Main St",
            "city": "New York",
            "country": "USA",
            "zip_code": "10001"
        },
        "tags": ["developer", "python"]
    }
    """
    return {"user": user}


# Path parameter + Request body
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    """
    Update an existing item.
    Combines path parameter with request body.
    """
    return {
        "item_id": item_id,
        "updated_item": item
    }


# Path parameter + Query parameter + Request body
@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    product: Product,
    notify: bool = False  # Query parameter
):
    """
    Update a product with optional notification.
    Demonstrates all three types of parameters together.
    """
    return {
        "product_id": product_id,
        "product": product,
        "notification_sent": notify
    }


# Model with example in schema
class Order(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
    shipping_address: Address

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "product_id": 1,
                    "quantity": 2,
                    "shipping_address": {
                        "street": "456 Oak Ave",
                        "city": "Los Angeles",
                        "country": "USA",
                        "zip_code": "90001"
                    }
                }
            ]
        }
    }


@app.post("/orders")
def create_order(order: Order):
    """Create an order. Check the docs to see the example!"""
    return {"order": order, "status": "pending"}


"""
EXERCISE 1:
-----------
Create a `BlogPost` model with:
- title (required, 5-200 characters)
- content (required)
- author (required)
- published (optional boolean, default False)
- tags (optional list of strings)

Create POST /blog/posts endpoint.

EXERCISE 2:
-----------
Create a `Comment` model and nest it inside BlogPost
as an optional list of comments.
"""
