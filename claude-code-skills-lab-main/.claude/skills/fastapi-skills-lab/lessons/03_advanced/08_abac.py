"""
LESSON 20: Attribute-Based Access Control (ABAC)
================================================

Fine-grained access control based on user, resource, and context attributes.

Key Concepts:
- Policy definition language
- Subject, resource, action, context attributes
- Policy evaluation engine
- Dynamic permission calculation
- ABAC vs RBAC comparison

To run:
    uv run uvicorn lessons.03_advanced.08_abac:app --reload
"""

from dataclasses import dataclass
from typing import Any
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from fastapi import FastAPI, Depends, HTTPException, status, Query
from pydantic import BaseModel


# =============================================================================
# ABAC Core
# =============================================================================

@dataclass
class AccessContext:
    """All attributes for access decision."""
    subject: dict[str, Any]      # User: id, role, department, clearance
    resource: dict[str, Any]     # Resource: owner_id, type, sensitivity
    action: str                   # Action: read, write, delete
    environment: dict[str, Any]  # Context: time, ip, device


class Policy(ABC):
    """Base policy class."""
    @abstractmethod
    def evaluate(self, ctx: AccessContext) -> bool:
        pass


class OwnerPolicy(Policy):
    """User owns the resource."""
    def evaluate(self, ctx: AccessContext) -> bool:
        return ctx.subject.get("id") == ctx.resource.get("owner_id")


class RolePolicy(Policy):
    """User has required role."""
    def __init__(self, role: str):
        self.role = role

    def evaluate(self, ctx: AccessContext) -> bool:
        return self.role in ctx.subject.get("roles", [])


class DepartmentPolicy(Policy):
    """Same department as resource."""
    def evaluate(self, ctx: AccessContext) -> bool:
        return ctx.subject.get("department") == ctx.resource.get("department")


class TimePolicy(Policy):
    """Within business hours (9-17 UTC)."""
    def evaluate(self, ctx: AccessContext) -> bool:
        hour = datetime.now(timezone.utc).hour
        return 9 <= hour < 17


class ClearancePolicy(Policy):
    """User clearance >= resource sensitivity."""
    def evaluate(self, ctx: AccessContext) -> bool:
        user_level = ctx.subject.get("clearance", 0)
        required = ctx.resource.get("sensitivity", 0)
        return user_level >= required


class PolicyEngine:
    """Evaluates policies."""
    def __init__(self):
        self.policies: list[Policy] = []

    def add(self, policy: Policy) -> "PolicyEngine":
        self.policies.append(policy)
        return self

    def any_allows(self, ctx: AccessContext) -> bool:
        """True if ANY policy allows."""
        return any(p.evaluate(ctx) for p in self.policies)

    def all_allow(self, ctx: AccessContext) -> bool:
        """True if ALL policies allow."""
        return all(p.evaluate(ctx) for p in self.policies)


# =============================================================================
# Sample Data
# =============================================================================

USERS = {
    "alice": {"id": "alice", "roles": ["admin"], "department": "IT", "clearance": 5},
    "bob": {"id": "bob", "roles": ["manager"], "department": "HR", "clearance": 3},
    "carol": {"id": "carol", "roles": ["employee"], "department": "HR", "clearance": 1},
}

DOCUMENTS = {
    "doc1": {"id": "doc1", "owner_id": "alice", "department": "IT", "sensitivity": 3},
    "doc2": {"id": "doc2", "owner_id": "bob", "department": "HR", "sensitivity": 2},
    "doc3": {"id": "doc3", "owner_id": "carol", "department": "HR", "sensitivity": 1},
}


# =============================================================================
# Policy Configurations
# =============================================================================

# Owner or Admin can access
owner_or_admin = PolicyEngine().add(OwnerPolicy()).add(RolePolicy("admin"))

# Same department + sufficient clearance (all must pass)
department_and_clearance = PolicyEngine().add(DepartmentPolicy()).add(ClearancePolicy())


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(title="ABAC Demo", version="1.0.0")


async def get_user(user_id: str = Query(...)) -> dict:
    """Get user for demo."""
    if user_id not in USERS:
        raise HTTPException(404, "User not found")
    return USERS[user_id]


@app.get("/")
async def root():
    return {
        "users": list(USERS.keys()),
        "documents": list(DOCUMENTS.keys()),
        "usage": "?user_id=alice or ?user_id=bob"
    }


@app.get("/documents/{doc_id}")
async def read_document(doc_id: str, user: dict = Depends(get_user)):
    """Read document - owner or admin allowed."""
    if doc_id not in DOCUMENTS:
        raise HTTPException(404, "Document not found")

    doc = DOCUMENTS[doc_id]
    ctx = AccessContext(
        subject=user,
        resource=doc,
        action="read",
        environment={}
    )

    if not owner_or_admin.any_allows(ctx):
        raise HTTPException(403, "Access denied")

    return {"document": doc, "accessed_by": user["id"]}


@app.get("/documents/{doc_id}/department-access")
async def department_access(doc_id: str, user: dict = Depends(get_user)):
    """Access by department + clearance (stricter)."""
    if doc_id not in DOCUMENTS:
        raise HTTPException(404, "Document not found")

    doc = DOCUMENTS[doc_id]
    ctx = AccessContext(subject=user, resource=doc, action="read", environment={})

    if not department_and_clearance.all_allow(ctx):
        raise HTTPException(403, f"Need same department AND clearance >= {doc['sensitivity']}")

    return {"document": doc, "accessed_by": user["id"]}


@app.get("/check-access")
async def check_access(
    doc_id: str,
    policy: str = Query("owner_or_admin"),
    user: dict = Depends(get_user)
):
    """Check access with different policies."""
    if doc_id not in DOCUMENTS:
        raise HTTPException(404, "Document not found")

    doc = DOCUMENTS[doc_id]
    ctx = AccessContext(subject=user, resource=doc, action="read", environment={})

    engines = {
        "owner_or_admin": owner_or_admin,
        "department_and_clearance": department_and_clearance,
    }

    engine = engines.get(policy)
    if not engine:
        raise HTTPException(400, f"Unknown policy: {policy}")

    allowed = engine.any_allows(ctx) if policy == "owner_or_admin" else engine.all_allow(ctx)

    return {
        "user": user["id"],
        "document": doc_id,
        "policy": policy,
        "allowed": allowed,
        "user_clearance": user.get("clearance"),
        "doc_sensitivity": doc.get("sensitivity"),
        "same_department": user.get("department") == doc.get("department")
    }


# =============================================================================
# Key Concepts
# =============================================================================

"""
ABAC vs RBAC:
- RBAC: "Is user an admin?" (role-based)
- ABAC: "Is user in same department AND has clearance >= 3 AND it's business hours?"

ABAC Components:
1. Subject attributes (user properties)
2. Resource attributes (data properties)
3. Action (what they want to do)
4. Environment (context: time, location)

Policy Types:
- ANY: At least one policy must pass (OR)
- ALL: Every policy must pass (AND)

Use Cases:
- Multi-tenant data isolation
- Time-based access restrictions
- Sensitivity/clearance levels
- Geographic restrictions
"""
