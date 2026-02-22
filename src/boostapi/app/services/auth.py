"""Authentication service: user retrieval and credential verification."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import hash_password, verify_password
from ..db.models import User


class AuthService:
    """Business logic for authentication and user management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by their username or return *None*."""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def authenticate(self, username: str, password: str) -> User | None:
        """
        Verify credentials and return the authenticated user or *None*.

        Uses constant-time bcrypt comparison to prevent timing attacks.
        """
        user = await self.get_by_username(username)
        if user is None:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        is_superuser: bool = False,
    ) -> User:
        """Create and persist a new user with a hashed password."""
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_superuser=is_superuser,
        )
        self.db.add(user)
        await self.db.flush()  # Assign ID without committing
        return user
