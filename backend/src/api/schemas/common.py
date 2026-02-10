from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
    timestamp: datetime | None = None


class HealthCheckService(BaseModel):
    status: str
    latency_ms: float | None = None
    error: str | None = None
    model: str | None = None
    collections: int | None = None
    documents: int | None = None


class HealthResponse(BaseModel):
    status: str
    checks: dict[str, HealthCheckService]
    timestamp: datetime


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[Any]
    total: int
    page: int
    limit: int
    pages: int
