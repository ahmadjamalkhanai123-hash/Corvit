"""
LESSON 9: Middleware
====================

Middleware runs code before/after every request.
Perfect for logging, CORS, timing, etc.

Key Concepts:
- Custom middleware
- Built-in middleware (CORS, GZip, etc.)
- Request/response modification
- Error handling in middleware

To run:
    uv run uvicorn lessons.02_intermediate.03_middleware:app --reload
"""

import time
import uuid
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(title="Middleware Lesson")


# Custom middleware using @app.middleware decorator
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware that measures and reports request processing time.

    This runs for EVERY request:
    1. Records start time
    2. Processes the request (call_next)
    3. Adds X-Process-Time header to response
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Custom middleware class
class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to each request.

    Useful for:
    - Tracing requests through logs
    - Correlating frontend/backend logs
    - Debugging in production
    """
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add to request state (accessible in endpoints)
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response header
        response.headers["X-Request-ID"] = request_id

        return response


# Add custom middleware
app.add_middleware(RequestIDMiddleware)


# Logging middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all requests."""

    async def dispatch(self, request: Request, call_next):
        # Log request
        print(f"[REQUEST] {request.method} {request.url.path}")
        print(f"  Client: {request.client.host if request.client else 'unknown'}")

        # Process request
        response = await call_next(request)

        # Log response
        print(f"[RESPONSE] Status: {response.status_code}")

        return response


app.add_middleware(LoggingMiddleware)


# CORS Middleware (built-in)
# Allow requests from other origins (e.g., frontend on different port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "https://yourdomain.com"  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


# GZip Middleware (built-in)
# Compress responses larger than 1000 bytes
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Error handling middleware
class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that catches unhandled exceptions and returns
    a consistent error response.
    """
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log the error
            print(f"[ERROR] Unhandled exception: {exc}")

            # Return error response
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "request_id": getattr(request.state, 'request_id', 'unknown')
                }
            )


app.add_middleware(ErrorHandlingMiddleware)


# Test endpoints
@app.get("/")
def home(request: Request):
    """Home endpoint - check headers in response!"""
    return {
        "message": "Check the response headers!",
        "request_id": request.state.request_id
    }


@app.get("/slow")
async def slow_endpoint():
    """Slow endpoint to test timing middleware."""
    import asyncio
    await asyncio.sleep(1)  # Simulate slow operation
    return {"message": "This took about 1 second"}


@app.get("/large")
def large_response():
    """Large response to test GZip compression."""
    return {
        "data": "x" * 5000,  # Large string
        "message": "This response should be compressed"
    }


@app.get("/error")
def trigger_error():
    """Endpoint that raises an error (caught by middleware)."""
    raise ValueError("This is a test error")


@app.get("/headers")
def show_headers(request: Request):
    """Show all request headers."""
    return {
        "headers": dict(request.headers),
        "client": request.client.host if request.client else None
    }


"""
MIDDLEWARE ORDER:
----------------

Middleware is executed in reverse order of how it's added.
Last added = first executed for request, last for response.

Request flow:  Client -> LastAdded -> ... -> FirstAdded -> Endpoint
Response flow: Endpoint -> FirstAdded -> ... -> LastAdded -> Client


COMMON USE CASES:
----------------
1. Logging and monitoring
2. Authentication/Authorization
3. Request ID / Correlation ID
4. Rate limiting
5. CORS handling
6. Response compression
7. Error handling
8. Request/Response modification


BUILT-IN MIDDLEWARE:
-------------------
- CORSMiddleware: Handle Cross-Origin Resource Sharing
- GZipMiddleware: Compress responses
- HTTPSRedirectMiddleware: Redirect HTTP to HTTPS
- TrustedHostMiddleware: Validate Host header
- SessionMiddleware: Session management


EXERCISE 1:
-----------
Create a rate-limiting middleware that:
- Tracks requests per IP address
- Limits to 10 requests per minute
- Returns 429 Too Many Requests if exceeded

EXERCISE 2:
-----------
Create a middleware that adds security headers:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
"""
