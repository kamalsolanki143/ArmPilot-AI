"""
ArmPilot-AI — Authentication Tests
Tests for JWT tokens, password hashing, auth service, and auth dependencies.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_subject,
    get_token_type,
)
from app.auth.password import hash_password, verify_password, needs_rehash
from app.models.user import User, UserRole


# ── Password Hashing Tests ────────────────────────────────────────────────────

class TestPasswordHashing:
    """Tests for bcrypt password hashing."""

    def test_hash_password_returns_string(self):
        hashed = hash_password("mypassword")
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_different_each_time(self):
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2

    def test_verify_password_correct(self):
        password = "secure_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_verify_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False

    def test_needs_rehash_returns_bool(self):
        hashed = hash_password("test")
        result = needs_rehash(hashed)
        assert isinstance(result, bool)


# ── JWT Token Tests ───────────────────────────────────────────────────────────

class TestJWTTokens:
    """Tests for JWT token creation and decoding."""

    def test_create_access_token_returns_string(self):
        token = create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_returns_string(self):
        token = create_refresh_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_decodable(self):
        token = create_access_token("user-123")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_refresh_token_decodable(self):
        token = create_refresh_token("user-123")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_access_token_with_extra_claims(self):
        token = create_access_token("user-1", extra_claims={"role": "admin", "username": "admin"})
        payload = decode_token(token)
        assert payload["role"] == "admin"
        assert payload["username"] == "admin"

    def test_decode_invalid_token_returns_none(self):
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_decode_empty_token_returns_none(self):
        payload = decode_token("")
        assert payload is None

    def test_get_token_subject(self):
        token = create_access_token("user-42")
        subject = get_token_subject(token)
        assert subject == "user-42"

    def test_get_token_subject_invalid(self):
        subject = get_token_subject("invalid")
        assert subject is None

    def test_get_token_type_access(self):
        token = create_access_token("user-1")
        token_type = get_token_type(token)
        assert token_type == "access"

    def test_get_token_type_refresh(self):
        token = create_refresh_token("user-1")
        token_type = get_token_type(token)
        assert token_type == "refresh"

    def test_access_token_has_expiry(self):
        token = create_access_token("user-1")
        payload = decode_token(token)
        assert "exp" in payload
        assert "iat" in payload

    def test_refresh_token_has_longer_expiry(self):
        access = create_access_token("user-1")
        refresh = create_refresh_token("user-1")
        a_payload = decode_token(access)
        r_payload = decode_token(refresh)
        assert r_payload["exp"] > a_payload["exp"]


# ── User Model Tests ──────────────────────────────────────────────────────────

class TestUserModel:
    """Tests for the User model."""

    def test_user_defaults(self):
        user = User(
            email="test@test.com",
            username="test",
            hashed_password="hashed",
        )
        assert user.is_active is True
        assert user.is_verified is False
        assert user.role == UserRole.USER
        assert user.id is not None

    def test_user_roles(self):
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.USER.value == "user"
        assert UserRole.VIEWER.value == "viewer"

    def test_user_with_oauth(self):
        user = User(
            email="test@test.com",
            username="test",
            hashed_password="hashed",
            oauth_provider="github",
            oauth_id="12345",
        )
        assert user.oauth_provider == "github"
        assert user.oauth_id == "12345"

    def test_user_serialization(self):
        user = User(
            email="test@test.com",
            username="test",
            hashed_password="hashed",
        )
        data = user.model_dump()
        assert data["email"] == "test@test.com"
        assert "hashed_password" in data


# ── Auth Service Tests ────────────────────────────────────────────────────────

class TestAuthService:
    """Tests for the auth service (user registration, login, tokens)."""

    @patch("app.services.auth_service.auth_service._users_dir")
    def test_register_new_user(self, mock_dir: MagicMock):
        from app.services.auth_service import AuthService
        mock_dir.__truediv__ = MagicMock(return_value=MagicMock(
            mkdir=MagicMock(),
            glob=MagicMock(return_value=[]),
        ))
        svc = AuthService()
        svc._users = {}
        svc._email_index = {}
        svc._username_index = {}

        from app.schemas.auth import UserRegister
        data = UserRegister(
            email="new@test.com",
            username="newuser",
            password="password123",
        )
        user, tokens = svc.register(data)
        assert user.email == "new@test.com"
        assert user.username == "newuser"
        assert tokens.access_token is not None

    @patch("app.services.auth_service.auth_service._users_dir")
    def test_register_duplicate_email_raises(self, mock_dir: MagicMock):
        from app.services.auth_service import AuthService
        svc = AuthService()
        svc._users = {}
        svc._email_index = {"exists@test.com": "user-1"}
        svc._username_index = {}

        from app.schemas.auth import UserRegister
        data = UserRegister(
            email="exists@test.com",
            username="newuser",
            password="password123",
        )
        with pytest.raises(ValueError, match="Email already registered"):
            svc.register(data)

    @patch("app.services.auth_service.auth_service._users_dir")
    def test_register_duplicate_username_raises(self, mock_dir: MagicMock):
        from app.services.auth_service import AuthService
        svc = AuthService()
        svc._users = {}
        svc._email_index = {}
        svc._username_index = {"taken": "user-1"}

        from app.schemas.auth import UserRegister
        data = UserRegister(
            email="new@test.com",
            username="taken",
            password="password123",
        )
        with pytest.raises(ValueError, match="Username already taken"):
            svc.register(data)

    def test_to_user_info(self):
        from app.services.auth_service import AuthService
        svc = AuthService()
        user = User(
            id="u1",
            email="test@test.com",
            username="test",
            hashed_password="hashed",
            full_name="Test User",
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
        )
        info = svc.to_user_info(user)
        assert info.id == "u1"
        assert info.email == "test@test.com"
        assert info.username == "test"


# ── Auth Middleware Tests ─────────────────────────────────────────────────────

class TestAuthMiddleware:
    """Tests for authentication dependencies."""

    @pytest.mark.asyncio
    @patch("app.auth.authentication.auth_service")
    @patch("app.auth.authentication.decode_token")
    async def test_get_current_user_no_credentials(self, mock_decode: MagicMock, mock_auth: MagicMock):
        from app.auth.authentication import get_current_user
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch("app.auth.authentication.auth_service")
    @patch("app.auth.authentication.decode_token")
    async def test_get_current_user_invalid_token(self, mock_decode: MagicMock, mock_auth: MagicMock):
        from app.auth.authentication import get_current_user
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials
        mock_decode.return_value = None
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=creds)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch("app.auth.authentication.auth_service")
    @patch("app.auth.authentication.decode_token")
    async def test_get_current_user_success(self, mock_decode: MagicMock, mock_auth: MagicMock):
        from app.auth.authentication import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        mock_decode.return_value = {"sub": "user-1", "type": "access"}
        mock_user = User(
            id="user-1",
            email="test@test.com",
            username="test",
            hashed_password="hashed",
            is_active=True,
        )
        mock_auth.get_user_by_id.return_value = mock_user
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
        user = await get_current_user(credentials=creds)
        assert user.id == "user-1"

    @pytest.mark.asyncio
    @patch("app.auth.authentication.auth_service")
    @patch("app.auth.authentication.decode_token")
    async def test_get_current_user_inactive(self, mock_decode: MagicMock, mock_auth: MagicMock):
        from app.auth.authentication import get_current_user
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials
        mock_decode.return_value = {"sub": "user-1", "type": "access"}
        mock_user = User(
            id="user-1",
            email="test@test.com",
            username="test",
            hashed_password="hashed",
            is_active=False,
        )
        mock_auth.get_user_by_id.return_value = mock_user
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=creds)
        assert exc_info.value.status_code == 403
