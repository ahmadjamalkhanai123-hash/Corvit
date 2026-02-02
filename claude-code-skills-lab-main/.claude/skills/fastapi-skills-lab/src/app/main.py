"""
FastAPI Application Entry Point
===============================

Production-ready FastAPI application with multi-layer architecture.

Run with:
    uv run uvicorn src.app.main:app --reload

Or for production:
    uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .db.session import engine
from .db.base import Base
from .api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Runs code on startup and shutdown.
    """
    # Startup
    print("Starting up...")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

    yield

    # Shutdown
    print("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    FastAPI Skills Lab API - A production-ready multi-layer architecture.

    ## Features
    - User authentication with JWT
    - CRUD operations for users and items
    - Proper error handling
    - API versioning

    ## Architecture
    - **API Layer**: HTTP handling, validation
    - **Service Layer**: Business logic
    - **Data Layer**: Database operations
    """,
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"])
def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": settings.app_name,
        "version": settings.version,
        "docs": "/docs",
        "redoc": "/redoc",
        "api": "/api/v1"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "version": settings.version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
