"""
Advanced Dependencies Module
============================

Reusable advanced dependency patterns for FastAPI applications.

Includes:
- Scoped dependencies
- Factory dependencies
- Contextual dependencies
- Parameterized dependencies
- Common utility dependencies
"""

from typing import Any, Callable, TypeVar, Generic
from dataclasses import dataclass
from functools import lru_cache

from fastapi import Request, Query, Header, HTTPException, status, Depends
from pydantic import BaseModel


T = TypeVar("T")


# =============================================================================
# SCOPED DEPENDENCIES
# =============================================================================

class SingletonMeta(type):
    """Metaclass for creating singleton dependencies."""
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class LazyDependency(Generic[T]):
    """
    Lazy initialization wrapper for expensive dependencies.

    Usage:
        expensive = LazyDependency(create_expensive_resource)

        def get_expensive():
            return expensive.get()
    """

    def __init__(self, factory: Callable[[], T]):
        self._factory = factory
        self._instance: T | None = None

    def get(self) -> T:
        if self._instance is None:
            self._instance = self._factory()
        return self._instance

    def reset(self) -> None:
        self._instance = None

    @property
    def is_initialized(self) -> bool:
        return self._instance is not None


# =============================================================================
# REQUEST CONTEXT
# =============================================================================

@dataclass
class RequestContext:
    """Context information for the current request."""
    request_id: str
    correlation_id: str
    client_ip: str
    user_agent: str
    path: str
    method: str


async def get_request_context(request: Request) -> RequestContext:
    """
    Extract request context information.

    Usage:
        @app.get("/endpoint")
        def endpoint(ctx: RequestContext = Depends(get_request_context)):
            logger.info(f"Request {ctx.request_id} from {ctx.client_ip}")
    """
    return RequestContext(
        request_id=request.headers.get("X-Request-ID", ""),
        correlation_id=request.headers.get("X-Correlation-ID", ""),
        client_ip=_get_client_ip(request),
        user_agent=request.headers.get("User-Agent", ""),
        path=str(request.url.path),
        method=request.method
    )


def _get_client_ip(request: Request) -> str:
    """Extract client IP, considering proxy headers."""
    # Check proxy headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


# =============================================================================
# PAGINATION
# =============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = 1
    limit: int = 20
    offset: int = 0


class Paginator:
    """
    Parameterized pagination dependency.

    Usage:
        @app.get("/items")
        def list_items(
            pagination: PaginationParams = Depends(Paginator(max_limit=100))
        ):
            return db.query().offset(pagination.offset).limit(pagination.limit)
    """

    def __init__(
        self,
        default_limit: int = 20,
        max_limit: int = 100
    ):
        self.default_limit = default_limit
        self.max_limit = max_limit

    async def __call__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(None, ge=1, description="Items per page")
    ) -> PaginationParams:
        effective_limit = min(limit or self.default_limit, self.max_limit)
        return PaginationParams(
            page=page,
            limit=effective_limit,
            offset=(page - 1) * effective_limit
        )


# Default paginator
get_pagination = Paginator()


# =============================================================================
# SORTING
# =============================================================================

class SortParams(BaseModel):
    """Sorting parameters."""
    sort_by: str
    sort_order: str  # "asc" or "desc"


def create_sorter(
    allowed_fields: list[str],
    default_field: str = "id",
    default_order: str = "asc"
):
    """
    Factory for sorting dependency with allowed fields.

    Usage:
        get_user_sort = create_sorter(["id", "name", "email", "created_at"])

        @app.get("/users")
        def list_users(sort: SortParams = Depends(get_user_sort)):
            return db.query().order_by(sort.sort_by, sort.sort_order)
    """
    async def dependency(
        sort_by: str = Query(default_field, description="Field to sort by"),
        sort_order: str = Query(default_order, regex="^(asc|desc)$")
    ) -> SortParams:
        if sort_by not in allowed_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort field. Allowed: {allowed_fields}"
            )
        return SortParams(sort_by=sort_by, sort_order=sort_order)

    return dependency


# =============================================================================
# FILTERING
# =============================================================================

class FilterParams(BaseModel):
    """Generic filter parameters."""
    filters: dict[str, Any]


def create_filter(
    allowed_fields: list[str],
    field_types: dict[str, type] | None = None
):
    """
    Factory for filtering dependency.

    Usage:
        get_user_filter = create_filter(
            ["status", "role", "is_active"],
            {"is_active": bool}
        )
    """
    async def dependency(request: Request) -> FilterParams:
        filters = {}
        for field in allowed_fields:
            value = request.query_params.get(field)
            if value is not None:
                # Type conversion if specified
                if field_types and field in field_types:
                    try:
                        if field_types[field] == bool:
                            value = value.lower() in ("true", "1", "yes")
                        else:
                            value = field_types[field](value)
                    except (ValueError, TypeError):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid value for filter '{field}'"
                        )
                filters[field] = value
        return FilterParams(filters=filters)

    return dependency


# =============================================================================
# TENANT CONTEXT (Multi-tenancy)
# =============================================================================

@dataclass
class TenantContext:
    """Multi-tenant context."""
    tenant_id: str
    tenant_name: str | None = None
    settings: dict | None = None


async def get_tenant_context(
    tenant_id: str = Header(..., alias="X-Tenant-ID")
) -> TenantContext:
    """
    Extract tenant context from header.

    Usage:
        @app.get("/data")
        def get_data(tenant: TenantContext = Depends(get_tenant_context)):
            return db.query().filter(tenant_id=tenant.tenant_id)
    """
    # In production: load tenant settings from database
    return TenantContext(tenant_id=tenant_id)


def require_tenant_feature(feature: str):
    """
    Dependency factory for tenant feature gates.

    Usage:
        @app.get("/premium")
        def premium(tenant: TenantContext = Depends(require_tenant_feature("premium"))):
            ...
    """
    async def dependency(
        tenant: TenantContext = Depends(get_tenant_context)
    ) -> TenantContext:
        # In production: check tenant.settings for feature
        features = tenant.settings.get("features", []) if tenant.settings else []
        if feature not in features:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature}' not available"
            )
        return tenant

    return dependency


# =============================================================================
# HEADER DEPENDENCIES
# =============================================================================

def require_header(
    header_name: str,
    error_message: str | None = None
):
    """
    Factory for required header dependency.

    Usage:
        @app.get("/api/data")
        def get_data(api_version: str = Depends(require_header("X-API-Version"))):
            ...
    """
    async def dependency(request: Request) -> str:
        value = request.headers.get(header_name)
        if not value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message or f"Header '{header_name}' is required"
            )
        return value

    return dependency


def optional_header(header_name: str, default: str | None = None):
    """
    Factory for optional header dependency.

    Usage:
        @app.get("/api/data")
        def get_data(
            version: str | None = Depends(optional_header("X-API-Version", "v1"))
        ):
            ...
    """
    async def dependency(request: Request) -> str | None:
        return request.headers.get(header_name, default)

    return dependency


# =============================================================================
# CACHING DEPENDENCY
# =============================================================================

class CacheControl:
    """
    Cache control dependency for conditional requests.

    Usage:
        @app.get("/resource/{id}")
        def get_resource(
            id: int,
            cache: CacheControl = Depends(CacheControl())
        ):
            resource = db.get(id)
            if cache.if_none_match == resource.etag:
                raise HTTPException(status_code=304)
            return resource
    """

    def __init__(self):
        self.if_none_match: str | None = None
        self.if_modified_since: str | None = None

    async def __call__(self, request: Request) -> "CacheControl":
        self.if_none_match = request.headers.get("If-None-Match")
        self.if_modified_since = request.headers.get("If-Modified-Since")
        return self


# =============================================================================
# COMPOSABLE DEPENDENCIES
# =============================================================================

def compose(*dependencies: Callable):
    """
    Compose multiple dependencies into one.

    Usage:
        combined = compose(get_pagination, get_sorting, get_filters)

        @app.get("/items")
        def list_items(deps: tuple = Depends(combined)):
            pagination, sorting, filters = deps
            ...
    """
    async def composed(**kwargs) -> tuple:
        results = []
        for dep in dependencies:
            if callable(dep):
                result = await dep(**kwargs) if kwargs else await dep()
                results.append(result)
        return tuple(results)

    return composed


# =============================================================================
# SERVICE LOCATOR
# =============================================================================

class ServiceLocator:
    """
    Simple service locator for dependency management.

    Usage:
        locator = ServiceLocator()
        locator.register("email", EmailService())
        locator.register("cache", CacheService())

        def get_email_service():
            return locator.get("email")
    """

    def __init__(self):
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service

    def get(self, name: str) -> Any:
        if name not in self._services:
            raise KeyError(f"Service '{name}' not registered")
        return self._services[name]

    def has(self, name: str) -> bool:
        return name in self._services


# Global service locator
services = ServiceLocator()
