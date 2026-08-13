"""
ArmPilot-AI — Auth Schemas
Pydantic models for authentication request/response payloads.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


# ── Request Schemas ───────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    """User registration payload."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=100)


class UserLogin(BaseModel):
    """User login payload."""
    email: EmailStr
    password: str


class TokenRefresh(BaseModel):
    """Refresh token payload."""
    refresh_token: str


class PasswordChange(BaseModel):
    """Password change payload."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordReset(BaseModel):
    """Password reset request payload."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation payload."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class OAuthCallback(BaseModel):
    """OAuth callback payload."""
    code: str
    state: Optional[str] = None


# ── Response Schemas ──────────────────────────────────────────────────────────

class TokenPair(BaseModel):
    """JWT token pair returned on login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    """Public user information."""
    id: str
    email: str
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserWithToken(BaseModel):
    """User info with tokens (for registration/login responses)."""
    user: UserInfo
    tokens: TokenPair


class MessageResponse(BaseModel):
    """Generic message response."""
    success: bool = True
    message: str
