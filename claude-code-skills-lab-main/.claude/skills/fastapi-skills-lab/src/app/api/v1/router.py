"""
API v1 Router
=============

Combines all v1 endpoints into a single router.
"""

from fastapi import APIRouter

from .endpoints import auth, users, items, pages

# Create main API router
api_router = APIRouter()

# Include endpoint routers with prefixes and tags
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    items.router,
    prefix="/items",
    tags=["Items"]
)

api_router.include_router(
    pages.router,
    prefix="/pages",
    tags=["Pages"]
)
