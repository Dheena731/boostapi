"""Security utilities: JWT creation, verification, and password hashing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

# ── Password hashing ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return *True* if *plain_password* matches *hashed_password*."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT ───────────────────────────────────────────────────────────────────────
def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: Value stored in the ``sub`` claim (usually user ID or username).
        expires_delta: Custom lifetime; defaults to ``ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Args:
        token: Raw JWT string.

    Returns:
        Decoded payload dictionary.

    Raises:
        :class:`jose.JWTError` if the token is invalid or expired.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def get_subject_from_token(token: str) -> str | None:
    """
    Extract the ``sub`` claim from a JWT, returning *None* on any error.

    Useful when you want a soft failure instead of an exception.
    """
    try:
        payload = decode_access_token(token)
        return payload.get("sub")
    except JWTError:
        return None
