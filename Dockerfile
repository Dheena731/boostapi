# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools
RUN pip install --no-cache-dir build hatchling

COPY pyproject.toml README.md ./
COPY src/ src/

RUN python -m build --wheel --outdir /dist


# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN addgroup --system boostapi && adduser --system --group boostapi

# Install runtime dependencies only
COPY --from=builder /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Copy alembic config
COPY alembic.ini ./
COPY src/boostapi/migrations/ src/boostapi/migrations/

# Create logs directory
RUN mkdir -p logs && chown -R boostapi:boostapi logs

USER boostapi

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health/ping')" || exit 1

CMD ["uvicorn", "boostapi.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
