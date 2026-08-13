"""
ArmPilot-AI — User Model
In-memory / JSON-backed user storage for MVP.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class User(BaseModel):
    """User model stored as JSON."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    email: str
    username: str
    hashed_password: str
    full_name: str = ""
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
