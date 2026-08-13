"""
ArmPilot-AI — Password Hashing
bcrypt-based password hashing and verification.
"""

from __future__ import annotations

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plain-text password."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


def needs_rehash(hashed: str) -> bool:
    """Check if a hash should be rehashed (e.g. after algorithm upgrade)."""
    return _pwd_context.needs_update(hashed)
