"""
ArmPilot-AI — Auth Package
Central exports for authentication utilities.
"""

from app.auth.password import hash_password, verify_password, needs_rehash
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_subject,
    get_token_type,
)
from app.auth.authentication import (
    get_current_user,
    get_current_active_user,
    get_optional_user,
)
from app.auth.permissions import (
    RequireRole,
    require_admin,
    require_user,
    require_viewer,
    check_permission,
)

__all__ = [
    "hash_password",
    "verify_password",
    "needs_rehash",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_token_subject",
    "get_token_type",
    "get_current_user",
    "get_current_active_user",
    "get_optional_user",
    "RequireRole",
    "require_admin",
    "require_user",
    "require_viewer",
    "check_permission",
]
