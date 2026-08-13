"""
ArmPilot-AI — OAuth2 Support
GitHub OAuth2 integration for third-party login.
"""

from __future__ import annotations

from typing import Optional

import httpx
from fastapi import Request
from fastapi.responses import RedirectResponse

from app.core.config import settings

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_USER_EMAIL_URL = "https://api.github.com/user/emails"

_REDIRECT_URI = "/api/auth/oauth/github/callback"


def get_github_authorize_url(state: str) -> str:
    """Build the GitHub OAuth2 authorization URL."""
    return (
        f"{GITHUB_AUTHORIZE_URL}"
        f"?client_id={settings.oauth_github_client_id}"
        f"&redirect_uri={_redirect_uri}"
        f"&scope=read:user user:email"
        f"&state={state}"
    )


async def exchange_github_code(code: str) -> Optional[dict]:
    """Exchange an OAuth2 authorization code for an access token, then fetch user info."""
    if not settings.oauth_github_client_id or not settings.oauth_github_client_secret:
        return None

    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            json={
                "client_id": settings.oauth_github_client_id,
                "client_secret": settings.oauth_github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            return None

        access_token = token_resp.json().get("access_token")
        if not access_token:
            return None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        # Fetch user profile
        user_resp = await client.get(GITHUB_USER_URL, headers=headers)
        if user_resp.status_code != 200:
            return None

        user_data = user_resp.json()

        # Fetch primary email
        email: Optional[str] = user_data.get("email")
        if not email:
            emails_resp = await client.get(GITHUB_USER_EMAIL_URL, headers=headers)
            if emails_resp.status_code == 200:
                for e in emails_resp.json():
                    if e.get("primary") and e.get("verified"):
                        email = e["email"]
                        break

        return {
            "github_id": str(user_data.get("id", "")),
            "username": user_data.get("login", ""),
            "full_name": user_data.get("name") or "",
            "email": email or "",
        }


class OAuthRouter:
    """Helper to build OAuth redirect responses."""

    @staticmethod
    def redirect_to_github(state: str) -> RedirectResponse:
        """Redirect the user to GitHub's OAuth2 authorize page."""
        url = get_github_authorize_url(state)
        return RedirectResponse(url=url, status_code=302)
