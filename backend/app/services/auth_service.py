"""
ArmPilot-AI — Auth Service
User registration, login, token management. JSON-file-backed for MVP.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logger import logger
from app.auth.password import hash_password, verify_password, needs_rehash
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.models.user import User, UserRole
from app.schemas.auth import (
    TokenPair,
    UserInfo,
    UserRegister,
)


class AuthService:
    """Manages user accounts and authentication tokens."""

    def __init__(self) -> None:
        self._users_dir = settings.resolve_path(settings.data_dir) / "users"
        self._users_dir.mkdir(parents=True, exist_ok=True)
        self._users: dict[str, User] = {}
        self._email_index: dict[str, str] = {}  # email -> user_id
        self._username_index: dict[str, str] = {}  # username -> user_id
        self._refresh_tokens: dict[str, str] = {}  # refresh_token -> user_id
        self._load_users()

    # ── Persistence ───────────────────────────────────────────────────────

    def _user_path(self, user_id: str) -> Path:
        return self._users_dir / f"{user_id}.json"

    def _load_users(self) -> None:
        for path in self._users_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                user = User.model_validate(data)
                self._users[user.id] = user
                self._email_index[user.email.lower()] = user.id
                self._username_index[user.username.lower()] = user.id
            except Exception:
                logger.warning("Failed to load user file: %s", path)
        logger.info("Loaded %d users", len(self._users))

    def _save_user(self, user: User) -> None:
        path = self._user_path(user.id)
        path.write_text(
            user.model_dump_json(indent=2),
            encoding="utf-8",
        )

    # ── User Queries ──────────────────────────────────────────────────────

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        uid = self._email_index.get(email.lower())
        return self._users.get(uid) if uid else None

    def get_user_by_username(self, username: str) -> Optional[User]:
        uid = self._username_index.get(username.lower())
        return self._users.get(uid) if uid else None

    # ── Registration ──────────────────────────────────────────────────────

    def register(self, data: UserRegister) -> tuple[User, TokenPair]:
        """Register a new user. Raises ValueError on duplicate email/username."""
        if self.get_user_by_email(data.email):
            raise ValueError("Email already registered")
        if self.get_user_by_username(data.username):
            raise ValueError("Username already taken")

        user = User(
            email=data.email.lower(),
            username=data.username.lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.USER,
        )
        self._users[user.id] = user
        self._email_index[user.email] = user.id
        self._username_index[user.username] = user.id
        self._save_user(user)

        tokens = self._create_tokens(user)
        logger.info("User registered: %s (%s)", user.username, user.email)
        return user, tokens

    # ── Login ─────────────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> tuple[User, TokenPair]:
        """Authenticate with email + password. Raises ValueError on failure."""
        user = self.get_user_by_email(email)
        if user is None:
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is deactivated")
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")

        if needs_rehash(user.hashed_password):
            user.hashed_password = hash_password(password)
            self._save_user(user)

        tokens = self._create_tokens(user)
        logger.info("User logged in: %s", user.username)
        return user, tokens

    # ── OAuth ─────────────────────────────────────────────────────────────

    def oauth_login_or_register(
        self,
        provider: str,
        provider_user_id: str,
        email: str,
        username: str,
        full_name: str = "",
    ) -> tuple[User, TokenPair]:
        """Login or auto-register via an OAuth provider."""
        # Check by provider + provider_user_id
        for user in self._users.values():
            if user.oauth_provider == provider and user.oauth_id == provider_user_id:
                tokens = self._create_tokens(user)
                return user, tokens

        # Check by email (link existing account)
        user = self.get_user_by_email(email)
        if user:
            user.oauth_provider = provider
            user.oauth_id = provider_user_id
            if not user.full_name and full_name:
                user.full_name = full_name
            self._save_user(user)
            tokens = self._create_tokens(user)
            return user, tokens

        # New user
        base_username = username or email.split("@")[0]
        unique_username = base_username
        counter = 1
        while self.get_user_by_username(unique_username):
            unique_username = f"{base_username}{counter}"
            counter += 1

        user = User(
            email=email.lower(),
            username=unique_username,
            hashed_password=hash_password(uuid.uuid4().hex),
            full_name=full_name,
            role=UserRole.USER,
            is_verified=True,
            oauth_provider=provider,
            oauth_id=provider_user_id,
        )
        self._users[user.id] = user
        self._email_index[user.email] = user.id
        self._username_index[user.username] = user.id
        self._save_user(user)

        tokens = self._create_tokens(user)
        logger.info("OAuth user registered: %s via %s", user.username, provider)
        return user, tokens

    # ── Token Management ──────────────────────────────────────────────────

    def _create_tokens(self, user: User) -> TokenPair:
        claims = {"role": user.role.value, "username": user.username}
        access_token = create_access_token(user.id, extra_claims=claims)
        refresh_token = create_refresh_token(user.id)
        self._refresh_tokens[refresh_token] = user.id
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    def refresh_tokens(self, refresh_token: str) -> TokenPair:
        """Issue a new token pair from a valid refresh token."""
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise ValueError("Invalid or expired refresh token")

        user_id = payload.get("sub")
        if not user_id or user_id not in self._users:
            raise ValueError("Invalid refresh token")

        user = self._users[user_id]
        if not user.is_active:
            raise ValueError("Account is deactivated")

        self._refresh_tokens.pop(refresh_token, None)
        return self._create_tokens(user)

    def logout(self, refresh_token: str) -> None:
        """Revoke a refresh token."""
        self._refresh_tokens.pop(refresh_token, None)

    # ── Password Management ───────────────────────────────────────────────

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        """Change a user's password."""
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        self._save_user(user)

    # ── Profile ───────────────────────────────────────────────────────────

    def to_user_info(self, user: User) -> UserInfo:
        return UserInfo(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )


# Singleton
auth_service = AuthService()
