"""
Permission Scopes Module
========================

OAuth2-style permission scopes for API authorization.
"""

from enum import Enum
from typing import Set


class Scope(str, Enum):
    """All available API scopes."""

    # OpenID Connect scopes
    OPENID = "openid"
    PROFILE = "profile"
    EMAIL = "email"
    OFFLINE_ACCESS = "offline_access"

    # User scopes
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"

    # Profile scopes (own data only)
    PROFILE_READ = "profile:read"
    PROFILE_WRITE = "profile:write"

    # Item scopes
    ITEMS_READ = "items:read"
    ITEMS_WRITE = "items:write"
    ITEMS_DELETE = "items:delete"

    # Admin scopes
    ADMIN = "admin"
    ADMIN_USERS = "admin:users"
    ADMIN_SETTINGS = "admin:settings"


# Scope descriptions for OAuth2 consent screens and documentation
SCOPE_DESCRIPTIONS = {
    Scope.OPENID: "Authenticate with OpenID Connect",
    Scope.PROFILE: "Access your basic profile information",
    Scope.EMAIL: "Access your email address",
    Scope.OFFLINE_ACCESS: "Maintain access when you're not present",
    Scope.USERS_READ: "View user information",
    Scope.USERS_WRITE: "Create and update users",
    Scope.USERS_DELETE: "Delete users",
    Scope.PROFILE_READ: "View your own profile",
    Scope.PROFILE_WRITE: "Update your own profile",
    Scope.ITEMS_READ: "View items",
    Scope.ITEMS_WRITE: "Create and update items",
    Scope.ITEMS_DELETE: "Delete items",
    Scope.ADMIN: "Full administrative access",
    Scope.ADMIN_USERS: "Administer user accounts",
    Scope.ADMIN_SETTINGS: "Manage system settings",
}


# Scope hierarchy - higher scopes include lower ones
SCOPE_HIERARCHY: dict[Scope, list[Scope]] = {
    Scope.ADMIN: [
        Scope.ADMIN_USERS, Scope.ADMIN_SETTINGS,
        Scope.USERS_READ, Scope.USERS_WRITE, Scope.USERS_DELETE,
        Scope.ITEMS_READ, Scope.ITEMS_WRITE, Scope.ITEMS_DELETE,
        Scope.PROFILE_READ, Scope.PROFILE_WRITE,
    ],
    Scope.ADMIN_USERS: [Scope.USERS_READ, Scope.USERS_WRITE, Scope.USERS_DELETE],
    Scope.USERS_WRITE: [Scope.USERS_READ],
    Scope.USERS_DELETE: [Scope.USERS_READ],
    Scope.ITEMS_WRITE: [Scope.ITEMS_READ],
    Scope.ITEMS_DELETE: [Scope.ITEMS_READ],
    Scope.PROFILE_WRITE: [Scope.PROFILE_READ],
    Scope.PROFILE: [Scope.PROFILE_READ],
}


# Default scopes for different user types
DEFAULT_USER_SCOPES = [Scope.PROFILE_READ, Scope.PROFILE_WRITE, Scope.ITEMS_READ]
DEFAULT_ADMIN_SCOPES = [Scope.ADMIN]


def get_scope_description(scope: str | Scope) -> str:
    """Get human-readable description for a scope."""
    if isinstance(scope, str):
        try:
            scope = Scope(scope)
        except ValueError:
            return f"Unknown scope: {scope}"
    return SCOPE_DESCRIPTIONS.get(scope, "")


def expand_scopes(scopes: list[str] | set[str]) -> set[str]:
    """
    Expand scope list to include all inherited scopes.

    Example: ["admin"] -> {"admin", "users:read", "users:write", ...}
    """
    expanded: set[str] = set()

    for scope_str in scopes:
        expanded.add(scope_str)

        try:
            scope = Scope(scope_str)
            inherited = SCOPE_HIERARCHY.get(scope, [])
            for inherited_scope in inherited:
                expanded.add(inherited_scope.value)
                # Recursively expand inherited scopes
                expanded.update(expand_scopes([inherited_scope.value]))
        except ValueError:
            pass  # Unknown scope, don't expand

    return expanded


def scope_satisfies(granted: set[str], required: str) -> bool:
    """
    Check if granted scopes satisfy a required scope.

    Args:
        granted: Set of scope strings the user has
        required: The scope string that is required

    Returns:
        True if the required scope is satisfied
    """
    # Direct match
    if required in granted:
        return True

    # Expand granted scopes and check
    expanded = expand_scopes(granted)
    return required in expanded


def scopes_satisfy_all(granted: set[str], required: list[str]) -> bool:
    """Check if granted scopes satisfy all required scopes."""
    return all(scope_satisfies(granted, r) for r in required)


def scopes_satisfy_any(granted: set[str], required: list[str]) -> bool:
    """Check if granted scopes satisfy at least one required scope."""
    return any(scope_satisfies(granted, r) for r in required)


def filter_allowed_scopes(requested: list[str], allowed: set[str]) -> list[str]:
    """
    Filter requested scopes to only those the user is allowed to have.

    Args:
        requested: Scopes the client is requesting
        allowed: Maximum scopes the user can grant

    Returns:
        List of scopes that are both requested and allowed
    """
    allowed_expanded = expand_scopes(allowed)
    return [s for s in requested if s in allowed_expanded]


def get_all_scopes() -> dict[str, str]:
    """Get all scopes with descriptions for OAuth2 documentation."""
    return {s.value: SCOPE_DESCRIPTIONS.get(s, "") for s in Scope}


def parse_scope_string(scope_string: str) -> list[str]:
    """Parse space-separated scope string into list."""
    if not scope_string:
        return []
    return scope_string.split()


def format_scope_string(scopes: list[str]) -> str:
    """Format scope list as space-separated string."""
    return " ".join(scopes)
