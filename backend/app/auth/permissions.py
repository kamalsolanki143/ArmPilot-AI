"""
ArmPilot-AI — Permissions / RBAC
Role-based access control for API endpoints.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from fastapi import Depends, HTTPException, Request, status

from app.auth.authentication import get_current_user
from app.models.user import User, UserRole


class RequireRole:
    """FastAPI dependency that restricts access by role."""

    def __init__(self, *allowed_roles: UserRole) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(self, request: Request, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user


# ── Pre-built dependencies ────────────────────────────────────────────────────

require_admin = RequireRole(UserRole.ADMIN)
require_user = RequireRole(UserRole.ADMIN, UserRole.USER)
require_viewer = RequireRole(UserRole.ADMIN, UserRole.USER, UserRole.VIEWER)


def check_permission(user: User, required_role: UserRole) -> bool:
    """Check if a user has at least the given role level."""
    hierarchy = {UserRole.VIEWER: 0, UserRole.USER: 1, UserRole.ADMIN: 2}
    return hierarchy.get(user.role, 0) >= hierarchy.get(required_role, 0)
