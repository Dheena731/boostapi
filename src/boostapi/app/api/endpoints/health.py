"""Health check endpoints for liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as aioredis
from boostapi._version import __version__
from ..deps import get_db, get_redis
from ...utils.logger import logger

router = APIRouter()


@router.get(
    "/",
    summary="Readiness probe",
    tags=["health"],
    responses={200: {"description": "All systems healthy"}, 503: {"description": "Degraded"}},
)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> dict:
    """
    Full readiness check — verifies database and Redis connectivity.

    Returns ``{"status": "healthy"}`` when all dependencies are reachable.
    """
    db_ok = True
    redis_ok = True
    errors: list[str] = []

    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_ok = False
        errors.append(f"db: {e}")
        logger.warning(f"Health check DB failure: {e}")

    try:
        await redis.ping()
    except Exception as e:
        redis_ok = False
        errors.append(f"redis: {e}")
        logger.warning(f"Health check Redis failure: {e}")

    overall = "healthy" if (db_ok and redis_ok) else "degraded"
    return {
        "status": overall,
        "version": __version__,
        "checks": {
            "db": "ok" if db_ok else "fail",
            "redis": "ok" if redis_ok else "fail",
        },
        "errors": errors,
    }


@router.get("/ping", summary="Liveness probe (no dependencies)")
async def ping() -> dict[str, str]:
    """Lightweight liveness probe — no DB or Redis required."""
    return {"status": "ok", "version": __version__}
