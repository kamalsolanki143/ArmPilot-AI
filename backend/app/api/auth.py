"""
ArmPilot-AI — Auth API
Registration, login, token refresh, OAuth, and profile endpoints.
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

from app.auth.authentication import get_current_user, get_current_active_user
from app.auth.oauth import OAuthRouter, exchange_github_code
from app.models.user import User
from app.schemas.auth import (
    MessageResponse,
    OAuthCallback,
    PasswordChange,
    TokenPair,
    TokenRefresh,
    UserInfo,
    UserLogin,
    UserRegister,
    UserWithToken,
)
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth")


# ── Registration ──────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserWithToken, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister):
    """Register a new user account."""
    try:
        user, tokens = auth_service.register(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return UserWithToken(
        user=auth_service.to_user_info(user),
        tokens=tokens,
    )


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=UserWithToken)
async def login(data: UserLogin):
    """Authenticate with email and password."""
    try:
        user, tokens = auth_service.login(data.email, data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    return UserWithToken(
        user=auth_service.to_user_info(user),
        tokens=tokens,
    )


# ── Token Refresh ─────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenPair)
async def refresh_token(data: TokenRefresh):
    """Get a new token pair from a refresh token."""
    try:
        tokens = auth_service.refresh_tokens(data.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    return tokens


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: TokenRefresh,
    _user: User = Depends(get_current_active_user),
):
    """Revoke a refresh token (effectively log out)."""
    auth_service.logout(data.refresh_token)
    return MessageResponse(message="Logged out successfully")


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserInfo)
async def get_profile(user: User = Depends(get_current_active_user)):
    """Get the current user's profile."""
    return auth_service.to_user_info(user)


# ── Password Change ───────────────────────────────────────────────────────────

@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: PasswordChange,
    user: User = Depends(get_current_active_user),
):
    """Change the current user's password."""
    try:
        auth_service.change_password(user, data.current_password, data.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return MessageResponse(message="Password changed successfully")


# ── OAuth: GitHub ─────────────────────────────────────────────────────────────

@router.get("/oauth/github")
async def github_login():
    """Redirect to GitHub's OAuth2 authorize page."""
    state = secrets.token_urlsafe(32)
    return OAuthRouter.redirect_to_github(state)


@router.get("/oauth/github/callback", response_model=UserWithToken)
async def github_callback(code: str = Query(...), state: str = Query(default="")):
    """Handle the GitHub OAuth2 callback."""
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code",
        )

    gh_user = await exchange_github_code(code)
    if gh_user is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to authenticate with GitHub",
        )
    if not gh_user.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account has no verified email",
        )

    user, tokens = auth_service.oauth_login_or_register(
        provider="github",
        provider_user_id=gh_user["github_id"],
        email=gh_user["email"],
        username=gh_user["username"],
        full_name=gh_user["full_name"],
    )
    return UserWithToken(
        user=auth_service.to_user_info(user),
        tokens=tokens,
    )
