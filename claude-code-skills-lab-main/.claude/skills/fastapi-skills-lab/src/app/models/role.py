"""
Role and Permission Models
==========================

SQLAlchemy models for RBAC (Role-Based Access Control).
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Table, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.base import Base


# Association table for Role <-> Permission many-to-many relationship
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
)

# Association table for User <-> Role many-to-many relationship
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
)


class Permission(Base):
    """
    Permission model.

    Permissions follow the pattern: resource:action
    Examples: users:read, items:write, admin:access
    """

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(255))
    resource = Column(String(50), index=True)  # e.g., "users", "items"
    action = Column(String(50))  # e.g., "read", "write", "delete"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )

    def __repr__(self):
        return f"<Permission {self.name}>"

    @classmethod
    def from_string(cls, permission_string: str) -> "Permission":
        """Create Permission from string like 'users:read'."""
        parts = permission_string.split(":", 1)
        resource = parts[0] if parts else permission_string
        action = parts[1] if len(parts) > 1 else "*"

        return cls(
            name=permission_string,
            resource=resource,
            action=action
        )


class Role(Base):
    """
    Role model.

    Roles group permissions and can be assigned to users.
    Supports role hierarchy through parent_id.
    """

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255))
    is_system = Column(Boolean, default=False)  # System roles can't be deleted
    is_default = Column(Boolean, default=False)  # Assigned to new users
    parent_id = Column(Integer, ForeignKey("roles.id"), nullable=True)  # For hierarchy
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )

    # Self-referential relationship for hierarchy
    parent = relationship(
        "Role",
        remote_side=[id],
        backref="children"
    )

    # Users with this role
    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )

    def __repr__(self):
        return f"<Role {self.name}>"

    def get_all_permissions(self) -> set[str]:
        """Get all permission names including inherited from parent."""
        permissions = {p.name for p in self.permissions}

        if self.parent:
            permissions.update(self.parent.get_all_permissions())

        return permissions

    def has_permission(self, permission_name: str) -> bool:
        """Check if role has permission (including wildcard matching)."""
        all_permissions = self.get_all_permissions()

        # Direct match
        if permission_name in all_permissions:
            return True

        # Wildcard match (e.g., "*" or "users:*")
        if "*" in all_permissions:
            return True

        # Resource wildcard (e.g., "users:*" matches "users:read")
        resource = permission_name.split(":")[0] if ":" in permission_name else permission_name
        if f"{resource}:*" in all_permissions:
            return True

        return False


class RoleAssignment(Base):
    """
    Track role assignments with metadata.

    Useful for auditing when and why roles were assigned.
    """

    __tablename__ = "role_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Temporary roles
    reason = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])


# =============================================================================
# Default Roles and Permissions
# =============================================================================

DEFAULT_PERMISSIONS = [
    # User permissions
    {"name": "users:read", "resource": "users", "action": "read", "description": "View users"},
    {"name": "users:write", "resource": "users", "action": "write", "description": "Create/update users"},
    {"name": "users:delete", "resource": "users", "action": "delete", "description": "Delete users"},

    # Item permissions
    {"name": "items:read", "resource": "items", "action": "read", "description": "View items"},
    {"name": "items:write", "resource": "items", "action": "write", "description": "Create/update items"},
    {"name": "items:delete", "resource": "items", "action": "delete", "description": "Delete items"},

    # Admin permissions
    {"name": "admin:access", "resource": "admin", "action": "access", "description": "Access admin panel"},
    {"name": "roles:manage", "resource": "roles", "action": "manage", "description": "Manage roles"},
    {"name": "settings:manage", "resource": "settings", "action": "manage", "description": "Manage settings"},

    # Superuser
    {"name": "*", "resource": "*", "action": "*", "description": "All permissions"},
]

DEFAULT_ROLES = [
    {
        "name": "admin",
        "description": "Full system access",
        "is_system": True,
        "permissions": ["*"]
    },
    {
        "name": "moderator",
        "description": "Manage users and content",
        "is_system": True,
        "permissions": ["users:read", "users:write", "items:read", "items:write", "items:delete"]
    },
    {
        "name": "editor",
        "description": "Manage content",
        "is_system": True,
        "permissions": ["items:read", "items:write"]
    },
    {
        "name": "viewer",
        "description": "Read-only access",
        "is_system": True,
        "is_default": True,
        "permissions": ["users:read", "items:read"]
    },
]
