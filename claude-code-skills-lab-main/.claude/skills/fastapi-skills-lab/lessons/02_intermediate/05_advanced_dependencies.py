"""
LESSON 11: Advanced Dependency Injection
========================================

Master advanced DI patterns for complex FastAPI applications.

Key Concepts:
- Scoped dependencies (request, session, application)
- Factory dependencies with configuration
- Contextual dependencies based on request attributes
- Parameterized dependencies
- Lazy dependencies
- Testing with dependency overrides

To run this lesson:
    cd fastapi-skills-lab
    uv run uvicorn lessons.02_intermediate.05_advanced_dependencies:app --reload

Then visit: http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager
from typing import Annotated, Any, Callable, TypeVar
from functools import lru_cache
from dataclasses import dataclass

from fastapi import FastAPI, Depends, Request, HTTPException, status, Query
from pydantic import BaseModel
from pydantic_settings import BaseSettings


# =============================================================================
# SECTION 1: Scoped Dependencies
# =============================================================================

"""
Dependencies can have different scopes:
- Request scope: New instance per request (default)
- Application scope: Single instance for entire app lifetime
- Session scope: Shared within a request chain

FastAPI's Depends() creates request-scoped dependencies by default.
"""

# Application-scoped: Created once, reused forever
class Settings(BaseSettings):
    """Application configuration - singleton pattern."""
    app_name: str = "DI Demo"
    debug: bool = True
    database_url: str = "sqlite:///./demo.db"

@lru_cache()
def get_settings() -> Settings:
    """
    Application-scoped dependency using lru_cache.
    Called once, cached forever (until app restart).
    """
    print("Creating Settings instance (should only see this once)")
    return Settings()


# Request-scoped: New instance per request
class RequestContext:
    """Context data for a single request."""

    def __init__(self, request: Request):
        self.request_id = request.headers.get("X-Request-ID", "no-id")
        self.user_agent = request.headers.get("User-Agent", "unknown")
        self.client_ip = request.client.host if request.client else "unknown"

async def get_request_context(request: Request) -> RequestContext:
    """
    Request-scoped dependency.
    New instance created for each request, shared within request.
    """
    print(f"Creating RequestContext for request {id(request)}")
    return RequestContext(request)


# Session-scoped (via request.state)
async def get_or_create_session_data(request: Request) -> dict:
    """
    Session-scoped data stored in request.state.
    Shared across all dependencies in the same request.
    """
    if not hasattr(request.state, "session_data"):
        request.state.session_data = {"counter": 0}
    request.state.session_data["counter"] += 1
    return request.state.session_data


# =============================================================================
# SECTION 2: Factory Dependencies with Configuration
# =============================================================================

"""
Factory dependencies create other dependencies based on configuration.
Useful for:
- Creating service instances with different configs
- Selecting implementations at runtime
- Dependency composition
"""

class DatabaseService:
    """Simulated database service."""

    def __init__(self, connection_string: str, pool_size: int = 5):
        self.connection_string = connection_string
        self.pool_size = pool_size
        print(f"DatabaseService created: pool_size={pool_size}")

    def query(self, sql: str) -> list:
        return [{"result": "mock data", "sql": sql}]


class CacheService:
    """Simulated cache service."""

    def __init__(self, backend: str = "memory", ttl: int = 300):
        self.backend = backend
        self.ttl = ttl
        self._cache: dict = {}

    def get(self, key: str) -> Any:
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value


def create_database_service(
    pool_size: int = 5,
    connection_string: str | None = None
):
    """
    Factory function that creates a dependency with configuration.

    Usage:
        # Default config
        db: DatabaseService = Depends(create_database_service())

        # Custom config
        db: DatabaseService = Depends(create_database_service(pool_size=10))
    """
    def dependency(settings: Settings = Depends(get_settings)) -> DatabaseService:
        conn_str = connection_string or settings.database_url
        return DatabaseService(conn_str, pool_size)
    return dependency


def create_cache_service(backend: str = "memory", ttl: int = 300):
    """Factory for cache service with configuration."""
    def dependency() -> CacheService:
        return CacheService(backend=backend, ttl=ttl)
    return dependency


# Pre-configured factories
get_database = create_database_service()
get_cache = create_cache_service(backend="memory", ttl=600)


# =============================================================================
# SECTION 3: Contextual Dependencies
# =============================================================================

"""
Contextual dependencies behave differently based on request attributes:
- User role/permissions
- Request headers (tenant, locale)
- Environment (dev/prod)
"""

@dataclass
class TenantContext:
    """Multi-tenant context."""
    tenant_id: str
    tenant_name: str
    features: list[str]

# Simulated tenant database
TENANTS = {
    "tenant-a": TenantContext("tenant-a", "Tenant A", ["feature1", "feature2"]),
    "tenant-b": TenantContext("tenant-b", "Tenant B", ["feature1"]),
}

async def get_tenant_context(request: Request) -> TenantContext:
    """
    Contextual dependency that varies by tenant header.

    Usage:
        @app.get("/data")
        def get_data(tenant: TenantContext = Depends(get_tenant_context)):
            if "feature2" in tenant.features:
                return {"data": "premium content"}
            return {"data": "basic content"}
    """
    tenant_id = request.headers.get("X-Tenant-ID")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header required"
        )

    tenant = TENANTS.get(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found"
        )

    return tenant


def require_feature(feature: str):
    """
    Dependency factory that checks for tenant feature.

    Usage:
        @app.get("/premium")
        def premium_endpoint(
            tenant: TenantContext = Depends(require_feature("feature2"))
        ):
            return {"premium": True}
    """
    async def dependency(tenant: TenantContext = Depends(get_tenant_context)):
        if feature not in tenant.features:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature}' not available for tenant"
            )
        return tenant
    return dependency


# =============================================================================
# SECTION 4: Parameterized Dependencies
# =============================================================================

"""
Parameterized dependencies accept runtime parameters.
Use class-based dependencies with __call__ for stateful dependencies.
"""

class Paginator:
    """
    Parameterized pagination dependency.

    Usage:
        @app.get("/items")
        def list_items(pagination: Paginator = Depends(Paginator(max_limit=50))):
            return {"page": pagination.page, "limit": pagination.limit}
    """

    def __init__(self, max_limit: int = 100, default_limit: int = 20):
        self.max_limit = max_limit
        self.default_limit = default_limit

    async def __call__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(None, ge=1, le=100, description="Items per page")
    ) -> "Paginator":
        # Create new instance with resolved parameters
        instance = Paginator(self.max_limit, self.default_limit)
        instance.page = page
        instance.limit = min(limit or self.default_limit, self.max_limit)
        instance.offset = (page - 1) * instance.limit
        return instance


class RateLimitChecker:
    """
    Parameterized rate limit checker.

    Usage:
        @app.get("/api/heavy")
        def heavy_operation(
            _: None = Depends(RateLimitChecker(requests_per_minute=10))
        ):
            ...
    """

    def __init__(self, requests_per_minute: int = 60):
        self.limit = requests_per_minute
        self._requests: dict[str, list] = {}

    async def __call__(self, request: Request) -> None:
        import time
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old requests
        if client_ip in self._requests:
            self._requests[client_ip] = [
                t for t in self._requests[client_ip]
                if now - t < 60
            ]
        else:
            self._requests[client_ip] = []

        # Check limit
        if len(self._requests[client_ip]) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

        self._requests[client_ip].append(now)


# =============================================================================
# SECTION 5: Lazy Dependencies
# =============================================================================

"""
Lazy dependencies defer initialization until first access.
Useful for expensive resources that might not be needed.
"""

T = TypeVar("T")

class LazyDependency:
    """
    Wrapper for lazy initialization of dependencies.

    Usage:
        expensive_service = LazyDependency(create_expensive_service)

        @app.get("/maybe-expensive")
        def endpoint(lazy: LazyDependency = Depends(lambda: expensive_service)):
            if need_expensive_operation:
                service = lazy.get()  # Initialized only when needed
                return service.do_work()
            return {"result": "cheap operation"}
    """

    def __init__(self, factory: Callable[[], T]):
        self._factory = factory
        self._instance: T | None = None
        self._initialized = False

    def get(self) -> T:
        if not self._initialized:
            print(f"Lazy initializing: {self._factory.__name__}")
            self._instance = self._factory()
            self._initialized = True
        return self._instance

    def reset(self) -> None:
        """Reset to uninitialized state."""
        self._instance = None
        self._initialized = False


def create_expensive_service():
    """Simulated expensive service initialization."""
    import time
    print("Expensive service: starting initialization...")
    time.sleep(0.1)  # Simulate slow init
    print("Expensive service: ready!")
    return {"service": "expensive", "status": "ready"}


# Global lazy instance
lazy_expensive = LazyDependency(create_expensive_service)


# =============================================================================
# SECTION 6: Testing with Dependency Overrides
# =============================================================================

"""
FastAPI allows overriding dependencies for testing.
This enables mocking, stubbing, and isolated testing.
"""

class EmailService:
    """Production email service."""

    def send(self, to: str, subject: str, body: str) -> bool:
        # In production: actually send email
        print(f"Sending email to {to}: {subject}")
        return True


class MockEmailService(EmailService):
    """Mock email service for testing."""

    def __init__(self):
        self.sent_emails: list[dict] = []

    def send(self, to: str, subject: str, body: str) -> bool:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
        return True


def get_email_service() -> EmailService:
    """Dependency that can be overridden in tests."""
    return EmailService()


# Example test setup (run with pytest)
"""
def test_send_notification():
    # Create mock
    mock_email = MockEmailService()

    # Override dependency
    app.dependency_overrides[get_email_service] = lambda: mock_email

    # Make test request
    client = TestClient(app)
    response = client.post("/notify", json={"email": "test@example.com"})

    # Assert
    assert response.status_code == 200
    assert len(mock_email.sent_emails) == 1
    assert mock_email.sent_emails[0]["to"] == "test@example.com"

    # Clean up
    app.dependency_overrides.clear()
"""


# =============================================================================
# APPLICATION SETUP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with startup/shutdown."""
    # Startup
    print("Application starting...")
    settings = get_settings()
    print(f"Running: {settings.app_name}")
    yield
    # Shutdown
    print("Application shutting down...")


app = FastAPI(
    title="Advanced Dependency Injection",
    description="Learn advanced DI patterns for FastAPI",
    version="1.0.0",
    lifespan=lifespan
)


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/")
async def root(settings: Settings = Depends(get_settings)):
    """Demonstrates application-scoped dependency."""
    return {
        "app": settings.app_name,
        "debug": settings.debug,
        "note": "Settings is cached - same instance for all requests"
    }


@app.get("/context")
async def get_context(
    ctx: RequestContext = Depends(get_request_context),
    session: dict = Depends(get_or_create_session_data)
):
    """Demonstrates request-scoped and session-scoped dependencies."""
    return {
        "request_id": ctx.request_id,
        "user_agent": ctx.user_agent,
        "session_counter": session["counter"]
    }


@app.get("/database")
async def use_database(
    db: DatabaseService = Depends(get_database)
):
    """Demonstrates factory dependency."""
    result = db.query("SELECT * FROM users")
    return {"pool_size": db.pool_size, "result": result}


@app.get("/database-custom")
async def use_custom_database(
    db: DatabaseService = Depends(create_database_service(pool_size=20))
):
    """Demonstrates configured factory dependency."""
    return {"pool_size": db.pool_size}


@app.get("/tenant-data")
async def get_tenant_data(
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Demonstrates contextual dependency.
    Requires X-Tenant-ID header.
    """
    return {
        "tenant_id": tenant.tenant_id,
        "tenant_name": tenant.tenant_name,
        "features": tenant.features
    }


@app.get("/premium-feature")
async def premium_feature(
    tenant: TenantContext = Depends(require_feature("feature2"))
):
    """Demonstrates feature-gated contextual dependency."""
    return {"message": f"Premium content for {tenant.tenant_name}"}


@app.get("/items")
async def list_items(pagination: Paginator = Depends(Paginator(max_limit=50))):
    """Demonstrates parameterized dependency."""
    # Simulate fetching items
    items = [{"id": i, "name": f"Item {i}"} for i in range(100)]

    return {
        "page": pagination.page,
        "limit": pagination.limit,
        "offset": pagination.offset,
        "items": items[pagination.offset:pagination.offset + pagination.limit]
    }


@app.get("/rate-limited")
async def rate_limited_endpoint(
    _: None = Depends(RateLimitChecker(requests_per_minute=5))
):
    """Demonstrates rate limiting dependency (5 req/min)."""
    return {"message": "Request allowed"}


@app.get("/lazy")
async def lazy_endpoint(use_expensive: bool = False):
    """Demonstrates lazy dependency initialization."""
    if use_expensive:
        service = lazy_expensive.get()
        return {"used_expensive": True, "service": service}
    return {"used_expensive": False, "message": "Skipped expensive init"}


@app.post("/notify")
async def send_notification(
    email: str,
    email_service: EmailService = Depends(get_email_service)
):
    """Demonstrates testable dependency."""
    email_service.send(email, "Notification", "Hello!")
    return {"sent_to": email}


# =============================================================================
# KEY CONCEPTS SUMMARY
# =============================================================================

"""
KEY CONCEPTS:
=============

1. SCOPED DEPENDENCIES:
   - Application scope: @lru_cache() for singletons
   - Request scope: Default FastAPI behavior
   - Session scope: Use request.state for shared data

2. FACTORY DEPENDENCIES:
   - Functions that return dependency functions
   - Enable configuration at definition time
   - Pattern: def create_service(config) -> Callable

3. CONTEXTUAL DEPENDENCIES:
   - Vary behavior based on request attributes
   - Use headers, user info, environment
   - Great for multi-tenancy, feature flags

4. PARAMETERIZED DEPENDENCIES:
   - Class-based with __call__ method
   - Accept Query/Path/Header parameters
   - Can maintain state across calls

5. LAZY DEPENDENCIES:
   - Defer initialization until first use
   - Reduce startup time
   - Avoid unnecessary resource allocation

6. TESTING OVERRIDES:
   - app.dependency_overrides[dep] = mock_dep
   - Replace any dependency with mock
   - Essential for unit testing

BEST PRACTICES:
===============
- Keep dependencies focused and single-purpose
- Use type hints for better IDE support
- Document dependency requirements clearly
- Prefer composition over inheritance
- Use factories for configurable dependencies
- Always clean up overrides after tests
"""


# =============================================================================
# EXERCISES
# =============================================================================

"""
EXERCISE 1: Create a Logger Dependency
--------------------------------------
Create a contextual logger that:
1. Extracts correlation ID from X-Correlation-ID header
2. Includes request path in all log messages
3. Supports different log levels based on DEBUG setting

Requirements:
- Factory function to configure log level
- Request-scoped logger instance
- Methods: info(), warning(), error()


EXERCISE 2: Create a Feature Flag Dependency
--------------------------------------------
Implement a feature flag system:
1. Load flags from configuration
2. Support user-specific flag overrides
3. Provide require_flag(flag_name) dependency factory

Example usage:
    @app.get("/new-feature")
    def new_feature(
        _: None = Depends(require_flag("new_dashboard"))
    ):
        return {"feature": "enabled"}

Bonus: Add percentage-based rollout support
"""
