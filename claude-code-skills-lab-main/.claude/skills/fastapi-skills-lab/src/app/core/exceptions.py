"""
Custom Exceptions
=================

Define application-specific exceptions for cleaner error handling.
"""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base exception for application errors."""
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An error occurred"
    ):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(AppException):
    """Raised when a resource is not found."""
    def __init__(self, resource: str = "Resource", resource_id: str | int = ""):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id '{resource_id}' not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class AlreadyExistsException(AppException):
    """Raised when trying to create a resource that already exists."""
    def __init__(self, resource: str = "Resource", field: str = ""):
        detail = f"{resource} already exists"
        if field:
            detail = f"{resource} with this {field} already exists"
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class UnauthorizedException(AppException):
    """Raised when authentication fails."""
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class ForbiddenException(AppException):
    """Raised when user doesn't have permission."""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ValidationException(AppException):
    """Raised for business logic validation errors."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class BadRequestException(AppException):
    """Raised for invalid requests."""
    def __init__(self, detail: str = "Bad request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
