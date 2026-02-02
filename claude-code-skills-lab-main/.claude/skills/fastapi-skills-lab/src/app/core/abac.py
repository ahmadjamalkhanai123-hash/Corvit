"""
Attribute-Based Access Control (ABAC)
=====================================

Policy engine for fine-grained access control based on attributes.
"""

from dataclasses import dataclass
from typing import Any, Callable
from abc import ABC, abstractmethod
from datetime import datetime, timezone


@dataclass
class AccessContext:
    """Context for access control decisions."""
    subject: dict[str, Any]      # User attributes (id, role, department, etc.)
    resource: dict[str, Any]     # Resource attributes (owner_id, type, status, etc.)
    action: str                   # Requested action (read, write, delete, etc.)
    environment: dict[str, Any]  # Context (time, ip, location, etc.)


class Policy(ABC):
    """Base class for access control policies."""

    @abstractmethod
    def evaluate(self, context: AccessContext) -> bool:
        """Evaluate policy against context. Returns True if allowed."""
        pass

    @property
    def name(self) -> str:
        return self.__class__.__name__


# =============================================================================
# Built-in Policies
# =============================================================================

class AllowAllPolicy(Policy):
    """Always allows access."""
    def evaluate(self, context: AccessContext) -> bool:
        return True


class DenyAllPolicy(Policy):
    """Always denies access."""
    def evaluate(self, context: AccessContext) -> bool:
        return False


class OwnerPolicy(Policy):
    """Allow if user owns the resource."""
    def evaluate(self, context: AccessContext) -> bool:
        return context.subject.get("id") == context.resource.get("owner_id")


class RolePolicy(Policy):
    """Allow if user has specific role."""
    def __init__(self, required_role: str):
        self.required_role = required_role

    def evaluate(self, context: AccessContext) -> bool:
        user_roles = context.subject.get("roles", [])
        return self.required_role in user_roles


class DepartmentPolicy(Policy):
    """Allow if user is in same department as resource."""
    def evaluate(self, context: AccessContext) -> bool:
        return context.subject.get("department") == context.resource.get("department")


class TimeWindowPolicy(Policy):
    """Allow only within specified hours (UTC)."""
    def __init__(self, start_hour: int = 9, end_hour: int = 17):
        self.start_hour = start_hour
        self.end_hour = end_hour

    def evaluate(self, context: AccessContext) -> bool:
        current_hour = datetime.now(timezone.utc).hour
        return self.start_hour <= current_hour < self.end_hour


class ActionPolicy(Policy):
    """Allow specific actions."""
    def __init__(self, allowed_actions: list[str]):
        self.allowed_actions = allowed_actions

    def evaluate(self, context: AccessContext) -> bool:
        return context.action in self.allowed_actions


# =============================================================================
# Policy Engine
# =============================================================================

class PolicyEngine:
    """Evaluates policies for access control decisions."""

    def __init__(self, default_deny: bool = True):
        self.policies: list[Policy] = []
        self.default_deny = default_deny

    def add_policy(self, policy: Policy) -> "PolicyEngine":
        """Add a policy to the engine."""
        self.policies.append(policy)
        return self

    def is_allowed(self, context: AccessContext) -> bool:
        """Check if access is allowed (any policy must pass)."""
        if not self.policies:
            return not self.default_deny

        return any(p.evaluate(context) for p in self.policies)

    def is_allowed_all(self, context: AccessContext) -> bool:
        """Check if all policies pass."""
        if not self.policies:
            return not self.default_deny

        return all(p.evaluate(context) for p in self.policies)

    def get_matching_policies(self, context: AccessContext) -> list[str]:
        """Get names of policies that allow access."""
        return [p.name for p in self.policies if p.evaluate(context)]


# =============================================================================
# Pre-configured Engines
# =============================================================================

# Owner or Admin can access
owner_or_admin_engine = PolicyEngine()
owner_or_admin_engine.add_policy(OwnerPolicy())
owner_or_admin_engine.add_policy(RolePolicy("admin"))

# Same department access
department_engine = PolicyEngine()
department_engine.add_policy(DepartmentPolicy())
department_engine.add_policy(RolePolicy("admin"))


def check_access(
    subject: dict,
    resource: dict,
    action: str,
    engine: PolicyEngine,
    environment: dict | None = None
) -> bool:
    """Helper function to check access."""
    context = AccessContext(
        subject=subject,
        resource=resource,
        action=action,
        environment=environment or {}
    )
    return engine.is_allowed(context)
