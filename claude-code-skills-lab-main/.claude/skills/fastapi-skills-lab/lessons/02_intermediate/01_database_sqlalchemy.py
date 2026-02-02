"""
LESSON 7: Database with SQLAlchemy
==================================

Learn how to integrate SQLAlchemy with FastAPI for
database operations.

Key Concepts:
- SQLAlchemy models
- Database sessions
- CRUD operations
- Dependency injection for DB

To run:
    uv run uvicorn lessons.02_intermediate.01_database_sqlalchemy:app --reload
"""

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Database setup
DATABASE_URL = "sqlite:///./lessons.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# SQLAlchemy Model (Database Table)
class ProductDB(Base):
    """
    SQLAlchemy model - represents a database table.
    This defines the structure of our 'products' table.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Float, nullable=False)
    in_stock = Column(Boolean, default=True)


# Create tables
Base.metadata.create_all(bind=engine)


# Pydantic Schemas (API Data Validation)
class ProductBase(BaseModel):
    """Base schema with common fields"""
    name: str
    description: str | None = None
    price: float
    in_stock: bool = True


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating - all fields optional"""
    name: str | None = None
    description: str | None = None
    price: float | None = None
    in_stock: bool | None = None


class Product(ProductBase):
    """Schema for reading - includes id"""
    id: int

    model_config = ConfigDict(from_attributes=True)


# Dependency to get database session
def get_db():
    """
    Dependency that provides a database session.

    The session is automatically closed after the request,
    even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# FastAPI App
app = FastAPI(title="Database Lesson")


# CREATE
@app.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Create a new product.

    Depends(get_db) injects the database session.
    """
    db_product = ProductDB(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)  # Refresh to get the generated id
    return db_product


# READ ALL
@app.get("/products", response_model=list[Product])
def list_products(
    skip: int = 0,
    limit: int = 10,
    in_stock: bool | None = None,
    db: Session = Depends(get_db)
):
    """
    List products with optional filtering.
    """
    query = db.query(ProductDB)

    if in_stock is not None:
        query = query.filter(ProductDB.in_stock == in_stock)

    products = query.offset(skip).limit(limit).all()
    return products


# READ ONE
@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product by ID."""
    product = db.query(ProductDB).filter(ProductDB.id == product_id).first()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )

    return product


# UPDATE
@app.put("/products/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a product.

    Uses partial update - only updates provided fields.
    """
    db_product = db.query(ProductDB).filter(ProductDB.id == product_id).first()

    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )

    # Update only provided fields
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)

    db.commit()
    db.refresh(db_product)
    return db_product


# DELETE
@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product."""
    db_product = db.query(ProductDB).filter(ProductDB.id == product_id).first()

    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )

    db.delete(db_product)
    db.commit()


# Search endpoint
@app.get("/products/search/", response_model=list[Product])
def search_products(
    q: str,
    db: Session = Depends(get_db)
):
    """Search products by name."""
    products = db.query(ProductDB).filter(
        ProductDB.name.contains(q)
    ).all()
    return products


"""
KEY CONCEPTS:
------------

1. SQLAlchemy Model vs Pydantic Schema:
   - SQLAlchemy Model: Defines database table structure
   - Pydantic Schema: Defines API request/response validation

2. Session Management:
   - Use dependency injection for sessions
   - Always close sessions (yield + finally)

3. CRUD Pattern:
   - Create: db.add() + db.commit()
   - Read: db.query().filter().first() or .all()
   - Update: modify object + db.commit()
   - Delete: db.delete() + db.commit()

4. model_config = ConfigDict(from_attributes=True):
   - Allows Pydantic to read from SQLAlchemy models


EXERCISE 1:
-----------
Add a "Category" model with a one-to-many relationship
to Products (one category has many products).

EXERCISE 2:
-----------
Add pagination metadata to the list endpoint:
{
    "items": [...],
    "total": 100,
    "page": 1,
    "pages": 10
}
"""
