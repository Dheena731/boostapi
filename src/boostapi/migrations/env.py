"""Alembic migration environment for BoostAPI."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from boostapi.app.core.config import settings
from boostapi.app.db.database import Base

# Import all models so Alembic detects them automatically
from boostapi.app.db import models  # noqa: F401

config = context.config
fileConfig(config.config_file_name)  # type: ignore[arg-type]

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live DB connection needed)."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.connect() as conn:
        await conn.run_sync(
            lambda sync_conn: context.configure(
                connection=sync_conn,
                target_metadata=target_metadata,
                compare_type=True,
            )
        )
        async with conn.begin():
            await conn.run_sync(lambda _: context.run_migrations())

    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
