# Authentication Guide

ArmPilot-AI supports JWT-based authentication and GitHub OAuth2 for securing API access.

## Overview

| Method | Flow | Use Case |
|--------|------|----------|
| JWT (email/password) | Register → Login → Token | API clients, CLI |
| GitHub OAuth2 | Redirect → Callback → Token | Web dashboard |

## JWT Authentication

### Register

```
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "armpilot_user",
  "password": "secure_password_123"
}
```

**Response:**

```json
{
  "user": {
    "id": "usr_abc123",
    "email": "user@example.com",
    "username": "armpilot_user",
    "created_at": "2026-08-11T14:00:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

### Login

```
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password_123"
}
```

### Using the Token

Include the access token in the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Refresh Token

Access tokens expire after 60 minutes (configurable). Use the refresh token to get a new pair:

```
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Logout

```
POST /auth/logout
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Change Password

```
POST /auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "old_password",
  "new_password": "new_secure_password"
}
```

### Get Profile

```
GET /auth/me
Authorization: Bearer <access_token>
```

## GitHub OAuth2

### Setup

1. Create a GitHub OAuth App at https://github.com/settings/developers
2. Set the callback URL to `http://localhost:8000/auth/oauth/github/callback`
3. Configure in environment:

```bash
ARMPILOT_OAUTH_GITHUB_CLIENT_ID=your_client_id
ARMPILOT_OAUTH_GITHUB_CLIENT_SECRET=your_client_secret
```

### Flow

1. Redirect user to `GET /auth/oauth/github`
2. User authorizes on GitHub
3. GitHub redirects to `/auth/oauth/github/callback?code=...`
4. Backend exchanges code for tokens
5. Returns `UserWithToken` response

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `JWT_SECRET_KEY` | (required) | Secret key for signing tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token lifetime |

## Production Security

```bash
# Generate a strong secret
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Set in .env
ARMPILOT_JWT_SECRET_KEY=<generated_secret>
```

**Never use the default secret key in production.**
