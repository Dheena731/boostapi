"""FastAPI dependency injectors: database session, current user."""

from __future__ import annotations

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.security import decode_access_token
from ..db.database import AsyncSessionLocal, get_db
from ..db.models import User

# Re-export for convenience
__all__ = ["get_db", "get_current_user", "get_redis"]

bearer_scheme = HTTPBearer(auto_error=False)

# ── Redis ─────────────────────────────────────────────────────────────────────
_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return (or lazily create) a shared Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool


# ── Auth ──────────────────────────────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the *Bearer* token from ``Authorization`` header and return the
    authenticated :class:`User`.

    Raises:
        :class:`fastapi.HTTPException` 401 if the token is missing/invalid.
        :class:`fastapi.HTTPException` 403 if the user is inactive.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
        username: str | None = payload.get("sub")
        if username is None:
            raise unauthorized
    except JWTError:
        raise unauthorized

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        raise unauthorized
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user has superuser privileges."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges",
        )
    return current_user
