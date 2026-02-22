"""SQLAlchemy async engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from ..core.config import settings
from ..utils.logger import logger


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENV == "development",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Keep connections alive
    pool_recycle=3600,   # Recycle after 1 hour
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an :class:`AsyncSession` and commits on exit.

    Usage::

        @router.get("/")
        async def my_endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables (development / testing only). Use Alembic in production."""
    async with engine.begin() as conn:
        logger.info("Creating database tables…")
        await conn.run_sync(Base.metadata.create_all)
        logger.success("Database tables ready ✅")
