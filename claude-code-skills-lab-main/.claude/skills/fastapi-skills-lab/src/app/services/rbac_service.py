"""
RBAC Service
============

Business logic for Role-Based Access Control.
"""

from sqlalchemy.orm import Session
from ..core.exceptions import NotFoundException, ForbiddenException, AlreadyExistsException


class RBACService:
    """Service for RBAC operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_permissions(self, user_id: int) -> set[str]:
        """Get all permissions for a user (including inherited from roles)."""
        from ..models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(f"User {user_id} not found")

        permissions = set()
        for role in getattr(user, 'roles', []):
            permissions.update(role.get_all_permissions())
        return permissions

    def user_has_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has a specific permission."""
        permissions = self.get_user_permissions(user_id)

        if permission in permissions or "*" in permissions:
            return True

        # Check resource wildcard (e.g., "users:*" matches "users:read")
        if ":" in permission:
            resource = permission.split(":")[0]
            if f"{resource}:*" in permissions:
                return True
        return False

    def assign_role(self, user_id: int, role_name: str) -> None:
        """Assign a role to a user."""
        from ..models.user import User
        from ..models.role import Role

        user = self.db.query(User).filter(User.id == user_id).first()
        role = self.db.query(Role).filter(Role.name == role_name).first()

        if not user:
            raise NotFoundException(f"User {user_id} not found")
        if not role:
            raise NotFoundException(f"Role {role_name} not found")

        if role not in user.roles:
            user.roles.append(role)
            self.db.commit()

    def remove_role(self, user_id: int, role_name: str) -> None:
        """Remove a role from a user."""
        from ..models.user import User
        from ..models.role import Role

        user = self.db.query(User).filter(User.id == user_id).first()
        role = self.db.query(Role).filter(Role.name == role_name).first()

        if user and role and role in user.roles:
            user.roles.remove(role)
            self.db.commit()


def get_rbac_service(db: Session) -> RBACService:
    """Factory for dependency injection."""
    return RBACService(db)
