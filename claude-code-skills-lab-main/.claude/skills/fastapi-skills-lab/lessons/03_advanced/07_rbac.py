"""
LESSON 19: Role-Based Access Control (RBAC)
==========================================

Implement comprehensive role and permission systems.

Key Concepts:
- Role models and hierarchies
- Permission definitions
- Role-permission mapping
- User-role assignment
- Permission checking dependencies
- Admin panel for role management

To run this lesson:
    cd fastapi-skills-lab
    uv run uvicorn lessons.03_advanced.07_rbac:app --reload

Then visit: http://127.0.0.1:8000/docs
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field


# =============================================================================
# SECTION 1: Permission Definitions
# =============================================================================

"""
Permissions follow the pattern: resource:action
Examples:
- users:read - Can view users
- users:write - Can create/update users
- users:delete - Can delete users
- items:* - All permissions on items
"""

class Permission(str, Enum):
    """All available permissions in the system."""

    # User permissions
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"

    # Item permissions
    ITEMS_READ = "items:read"
    ITEMS_WRITE = "items:write"
    ITEMS_DELETE = "items:delete"

    # Admin permissions
    ADMIN_ACCESS = "admin:access"
    ROLES_MANAGE = "roles:manage"
    SETTINGS_MANAGE = "settings:manage"

    # Special permissions
    SUPERUSER = "*"  # All permissions


def permission_matches(required: str, granted: str) -> bool:
    """Check if granted permission satisfies required permission."""
    # Superuser has all permissions
    if granted == "*":
        return True

    # Exact match
    if granted == required:
        return True

    # Wildcard match (e.g., "users:*" matches "users:read")
    if granted.endswith(":*"):
        resource = granted[:-2]
        if required.startswith(f"{resource}:"):
            return True

    return False


# =============================================================================
# SECTION 2: Role Definitions
# =============================================================================

class RoleModel(BaseModel):
    """Role with associated permissions."""
    name: str
    description: str
    permissions: list[str]
    is_default: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Predefined roles
PREDEFINED_ROLES: dict[str, RoleModel] = {
    "admin": RoleModel(
        name="admin",
        description="Full system access",
        permissions=["*"]
    ),
    "moderator": RoleModel(
        name="moderator",
        description="Can manage users and content",
        permissions=[
            "users:read",
            "users:write",
            "items:read",
            "items:write",
            "items:delete"
        ]
    ),
    "editor": RoleModel(
        name="editor",
        description="Can manage content",
        permissions=[
            "items:read",
            "items:write"
        ]
    ),
    "viewer": RoleModel(
        name="viewer",
        description="Read-only access",
        permissions=[
            "users:read",
            "items:read"
        ],
        is_default=True
    )
}


# Custom roles storage (in production, use database)
custom_roles: dict[str, RoleModel] = {}


def get_role(role_name: str) -> RoleModel | None:
    """Get role by name from predefined or custom roles."""
    return PREDEFINED_ROLES.get(role_name) or custom_roles.get(role_name)


def get_all_roles() -> list[RoleModel]:
    """Get all available roles."""
    return list(PREDEFINED_ROLES.values()) + list(custom_roles.values())


# =============================================================================
# SECTION 3: User Model with Roles
# =============================================================================

class UserModel(BaseModel):
    """User with assigned roles."""
    id: str
    username: str
    email: str
    roles: list[str] = ["viewer"]  # Default role
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Simulated user database
users_db: dict[str, UserModel] = {
    "admin": UserModel(
        id="1",
        username="admin",
        email="admin@example.com",
        roles=["admin"]
    ),
    "moderator": UserModel(
        id="2",
        username="moderator",
        email="mod@example.com",
        roles=["moderator"]
    ),
    "editor": UserModel(
        id="3",
        username="editor",
        email="editor@example.com",
        roles=["editor"]
    ),
    "user": UserModel(
        id="4",
        username="user",
        email="user@example.com",
        roles=["viewer"]
    )
}


# =============================================================================
# SECTION 4: Permission Checking
# =============================================================================

def get_user_permissions(user: UserModel) -> set[str]:
    """Get all permissions for a user based on their roles."""
    permissions = set()

    for role_name in user.roles:
        role = get_role(role_name)
        if role:
            permissions.update(role.permissions)

    return permissions


def user_has_permission(user: UserModel, required_permission: str) -> bool:
    """Check if user has a specific permission."""
    user_permissions = get_user_permissions(user)

    for granted in user_permissions:
        if permission_matches(required_permission, granted):
            return True

    return False


def user_has_any_permission(user: UserModel, permissions: list[str]) -> bool:
    """Check if user has any of the specified permissions."""
    return any(user_has_permission(user, p) for p in permissions)


def user_has_all_permissions(user: UserModel, permissions: list[str]) -> bool:
    """Check if user has all specified permissions."""
    return all(user_has_permission(user, p) for p in permissions)


# =============================================================================
# SECTION 5: Authentication Simulation
# =============================================================================

# Simple token-to-user mapping (in production, use proper JWT)
active_sessions: dict[str, str] = {
    "admin-token": "admin",
    "mod-token": "moderator",
    "editor-token": "editor",
    "user-token": "user"
}


async def get_current_user(
    token: str = Query(..., alias="token", description="Auth token")
) -> UserModel:
    """Get current user from token."""
    username = active_sessions.get(token)

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user = users_db.get(username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return user


# =============================================================================
# SECTION 6: Permission Dependencies
# =============================================================================

def require_permission(permission: str):
    """
    Dependency factory for permission-based access control.

    Usage:
        @app.get("/admin/users")
        def list_all_users(
            user: UserModel = Depends(require_permission("users:read"))
        ):
            ...
    """
    async def dependency(user: UserModel = Depends(get_current_user)) -> UserModel:
        if not user_has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return user

    return dependency


def require_any_permission(*permissions: str):
    """Require at least one of the specified permissions."""
    async def dependency(user: UserModel = Depends(get_current_user)) -> UserModel:
        if not user_has_any_permission(user, list(permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these permissions required: {permissions}"
            )
        return user

    return dependency


def require_all_permissions(*permissions: str):
    """Require all specified permissions."""
    async def dependency(user: UserModel = Depends(get_current_user)) -> UserModel:
        if not user_has_all_permissions(user, list(permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"All these permissions required: {permissions}"
            )
        return user

    return dependency


def require_role(role_name: str):
    """Require user to have specific role."""
    async def dependency(user: UserModel = Depends(get_current_user)) -> UserModel:
        if role_name not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required"
            )
        return user

    return dependency


# =============================================================================
# SECTION 7: Role Hierarchy (Optional)
# =============================================================================

"""
Role hierarchy allows roles to inherit permissions from other roles.
Example: admin > moderator > editor > viewer
"""

ROLE_HIERARCHY: dict[str, list[str]] = {
    "admin": ["moderator", "editor", "viewer"],
    "moderator": ["editor", "viewer"],
    "editor": ["viewer"],
    "viewer": []
}


def get_effective_roles(role_name: str) -> list[str]:
    """Get role and all inherited roles."""
    roles = [role_name]
    inherited = ROLE_HIERARCHY.get(role_name, [])
    roles.extend(inherited)
    return roles


def get_user_permissions_with_hierarchy(user: UserModel) -> set[str]:
    """Get permissions including inherited roles."""
    permissions = set()

    for role_name in user.roles:
        effective_roles = get_effective_roles(role_name)
        for effective_role in effective_roles:
            role = get_role(effective_role)
            if role:
                permissions.update(role.permissions)

    return permissions


# =============================================================================
# APPLICATION SETUP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\nAvailable test tokens:")
    for token, username in active_sessions.items():
        user = users_db[username]
        print(f"  {token}: {username} (roles: {user.roles})")
    print()
    yield


app = FastAPI(
    title="Role-Based Access Control",
    description="Learn RBAC patterns for FastAPI",
    version="1.0.0",
    lifespan=lifespan
)


# =============================================================================
# SCHEMAS
# =============================================================================

class RoleCreate(BaseModel):
    name: str
    description: str
    permissions: list[str]


class UserRoleUpdate(BaseModel):
    roles: list[str]


class ItemCreate(BaseModel):
    title: str
    content: str


# =============================================================================
# ENDPOINTS: Public
# =============================================================================

@app.get("/")
async def root():
    """Public endpoint."""
    return {"message": "Welcome! Use ?token=xxx to authenticate"}


@app.get("/roles")
async def list_roles():
    """List all available roles (public)."""
    return {"roles": [r.model_dump() for r in get_all_roles()]}


@app.get("/permissions")
async def list_permissions():
    """List all available permissions (public)."""
    return {"permissions": [p.value for p in Permission]}


# =============================================================================
# ENDPOINTS: User Info
# =============================================================================

@app.get("/me")
async def get_me(user: UserModel = Depends(get_current_user)):
    """Get current user info."""
    return {
        "user": user,
        "permissions": list(get_user_permissions(user))
    }


@app.get("/me/check-permission")
async def check_permission(
    permission: str,
    user: UserModel = Depends(get_current_user)
):
    """Check if current user has a permission."""
    has_permission = user_has_permission(user, permission)
    return {
        "permission": permission,
        "has_permission": has_permission
    }


# =============================================================================
# ENDPOINTS: Users (requires users:read/write/delete)
# =============================================================================

@app.get("/users")
async def list_users(user: UserModel = Depends(require_permission("users:read"))):
    """List all users (requires users:read)."""
    return {"users": list(users_db.values())}


@app.get("/users/{username}")
async def get_user(
    username: str,
    user: UserModel = Depends(require_permission("users:read"))
):
    """Get user by username (requires users:read)."""
    target = users_db.get(username)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    return target


@app.put("/users/{username}/roles")
async def update_user_roles(
    username: str,
    role_update: UserRoleUpdate,
    user: UserModel = Depends(require_permission("users:write"))
):
    """Update user roles (requires users:write)."""
    target = users_db.get(username)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate roles exist
    for role_name in role_update.roles:
        if not get_role(role_name):
            raise HTTPException(
                status_code=400,
                detail=f"Role '{role_name}' does not exist"
            )

    target.roles = role_update.roles
    return target


@app.delete("/users/{username}")
async def delete_user(
    username: str,
    user: UserModel = Depends(require_permission("users:delete"))
):
    """Delete user (requires users:delete)."""
    if username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    del users_db[username]
    return {"message": f"User {username} deleted"}


# =============================================================================
# ENDPOINTS: Items (requires items:read/write/delete)
# =============================================================================

items_db: list[dict] = [
    {"id": 1, "title": "Item 1", "content": "Content 1"},
    {"id": 2, "title": "Item 2", "content": "Content 2"}
]


@app.get("/items")
async def list_items(user: UserModel = Depends(require_permission("items:read"))):
    """List all items (requires items:read)."""
    return {"items": items_db}


@app.post("/items")
async def create_item(
    item: ItemCreate,
    user: UserModel = Depends(require_permission("items:write"))
):
    """Create item (requires items:write)."""
    new_item = {
        "id": len(items_db) + 1,
        "title": item.title,
        "content": item.content,
        "created_by": user.username
    }
    items_db.append(new_item)
    return new_item


@app.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    user: UserModel = Depends(require_permission("items:delete"))
):
    """Delete item (requires items:delete)."""
    global items_db
    items_db = [i for i in items_db if i["id"] != item_id]
    return {"message": f"Item {item_id} deleted"}


# =============================================================================
# ENDPOINTS: Admin (requires admin:access)
# =============================================================================

@app.get("/admin/dashboard")
async def admin_dashboard(user: UserModel = Depends(require_permission("admin:access"))):
    """Admin dashboard (requires admin:access)."""
    return {
        "total_users": len(users_db),
        "total_items": len(items_db),
        "total_roles": len(get_all_roles())
    }


@app.post("/admin/roles")
async def create_role(
    role: RoleCreate,
    user: UserModel = Depends(require_permission("roles:manage"))
):
    """Create custom role (requires roles:manage)."""
    if role.name in PREDEFINED_ROLES or role.name in custom_roles:
        raise HTTPException(status_code=400, detail="Role already exists")

    new_role = RoleModel(
        name=role.name,
        description=role.description,
        permissions=role.permissions
    )
    custom_roles[role.name] = new_role
    return new_role


# =============================================================================
# KEY CONCEPTS SUMMARY
# =============================================================================

"""
KEY CONCEPTS:
=============

1. PERMISSION STRUCTURE:
   - Format: resource:action (e.g., users:read)
   - Wildcard support: users:* or * for all
   - Define as enum for type safety

2. ROLE MODEL:
   - Name, description, list of permissions
   - Support predefined and custom roles
   - Default role for new users

3. PERMISSION CHECKING:
   - Collect all permissions from user's roles
   - Support wildcard matching
   - Check single, any, or all permissions

4. DEPENDENCY INJECTION:
   - require_permission(permission) - Single permission
   - require_any_permission(*perms) - OR logic
   - require_all_permissions(*perms) - AND logic
   - require_role(role) - Specific role

5. ROLE HIERARCHY (OPTIONAL):
   - Admin inherits moderator permissions
   - Moderator inherits editor permissions
   - Reduces permission duplication

BEST PRACTICES:
===============
- Use descriptive permission names
- Keep roles focused (don't create mega-roles)
- Audit permission changes
- Support custom roles for flexibility
- Cache permission calculations for performance
"""


# =============================================================================
# EXERCISES
# =============================================================================

"""
EXERCISE 1: Implement Role Hierarchy in Permissions
---------------------------------------------------
Modify get_user_permissions to use ROLE_HIERARCHY:
1. When user has "admin" role, include all inherited roles' permissions
2. Test that admin can access editor-only endpoints
3. Add endpoint to show effective permissions (including inherited)


EXERCISE 2: Implement Permission Scoping
----------------------------------------
Add resource-level permissions:
1. items:read:own - Can only read own items
2. items:write:own - Can only modify own items
3. items:read:all - Can read all items (current behavior)

Implement checking logic:
- If user has :all scope, allow access to any resource
- If user has :own scope, check resource ownership
- Add owner_id to items and verify in endpoints
"""
