"""Application factory for BoostAPI."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from boostapi._version import __version__
from .core.config import Settings
from .api.endpoints import auth, health
from .db.database import engine
from .utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle."""
    # ── Startup ──────────────────────────────────────────────
    logger.info(f"🛠️  BoostAPI v{__version__} starting up…")
    logger.info(f"📦  Database: {app.state.settings.DATABASE_URL.split('@')[-1]}")
    logger.info(f"🗄️   Redis: {app.state.settings.REDIS_URL}")

    yield

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("👋 BoostAPI shutting down gracefully…")
    await engine.dispose()
    logger.info("✅ Database connections closed")


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Application factory — the single entry point to create a BoostAPI API.

    Args:
        settings: Optional :class:`Settings` instance. Reads from environment
                  variables / ``.env`` file when *None*.

    Returns:
        A fully configured :class:`fastapi.FastAPI` instance.

    Example::

        from boostapi import create_app
        app = create_app()
    """
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title="🛠️ BoostAPI",
        description=(
            "Production-ready FastAPI template with Redis caching, JWT auth, and CLI scaffolding."
        ),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        openapi_tags=[
            {
                "name": "auth",
                "description": "JWT-based authentication — obtain and refresh tokens",
            },
            {
                "name": "health",
                "description": "Liveness & readiness probes for orchestration platforms",
            },
        ],
    )

    # Store settings on app state for lifespan access
    app.state.settings = settings

    # ── Middleware ────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next: object) -> Response:
        """Append X-Process-Time header to every response."""
        start = time.perf_counter()
        response: Response = await call_next(request)  # type: ignore[arg-type]
        duration = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        return response

    # ── Routers ───────────────────────────────────────────────
    prefix = settings.API_V1_STR
    app.include_router(auth.router, prefix=f"{prefix}/auth", tags=["auth"])
    app.include_router(health.router, prefix=f"{prefix}/health", tags=["health"])

    # ── Root endpoint ─────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "message": "🛠️ BoostAPI Semantic Search API",
            "version": __version__,
            "docs": "/docs",
            "redoc": "/redoc",
        }

    # ── Exception handlers ────────────────────────────────────
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": "Resource not found", "path": str(request.url.path)},
        )

    logger.success(f"✅ BoostAPI app created — docs at /docs")
    return app
