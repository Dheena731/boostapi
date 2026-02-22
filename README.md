# 🛠️ BoostAPI

<p align="center">
  <strong>Production-ready FastAPI starter toolkit with Redis caching, JWT Auth & CLI scaffolding</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/boostapi/"><img src="https://img.shields.io/pypi/v/boostapi?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pypi.org/project/boostapi/"><img src="https://img.shields.io/pypi/pyversions/boostapi?logo=python&logoColor=white" alt="Python versions"></a>
  <a href="https://github.com/dhinakaran/boostapi/actions"><img src="https://img.shields.io/github/actions/workflow/status/dhinakaran/boostapi/ci.yml?label=CI&logo=github" alt="CI"></a>
  <a href="https://codecov.io/gh/dhinakaran/boostapi"><img src="https://img.shields.io/codecov/c/github/dhinakaran/boostapi?logo=codecov" alt="Coverage"></a>
  <a href="https://github.com/dhinakaran/boostapi/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"></a>
  <a href="https://github.com/dhinakaran/boostapi"><img src="https://img.shields.io/github/stars/dhinakaran/boostapi?style=flat&logo=github" alt="GitHub Stars"></a>
</p>

---

## ✨ Features

| Feature | Details |
|---|---|
| ⚡ **Redis Caching** | Built-in caching templates for instant responses |
| 🔐 **JWT Auth** | Secure authentication with refresh tokens built-in |
| 🗃️ **Async SQLAlchemy** | asyncpg driver, connection pooling, Alembic migrations |
| 🛠️ **CLI Scaffolding** | `boostapi quickstart myapp` → full project in seconds |
| 📦 **Zero-Config** | Works out of the box with sane defaults |
| 🚀 **Production-Grade** | Loguru logging, CORS, rate limiting, OpenAPI docs |

---

## ⚡ 2-Minute Quickstart

### Option A: Scaffold a New Project

```bash
# Install BoostAPI
pip install boostapi

# Scaffold a complete web application
boostapi quickstart my-app
cd my-app

# Start dependencies (PostgreSQL + Redis)
docker compose up -d

# Run migrations & start server
alembic upgrade head
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs — your API is live! 🎉

### Option B: Embed in Your App

```python
# myapp.py
from boostapi import create_app

app = create_app()
# uvicorn myapp:app --reload
```

### Option C: Custom Settings

```python
from boostapi import create_app
from boostapi.app.core.config import Settings

app = create_app(settings=Settings(
    POSTGRES_DB="mydb",
    REDIS_URL="redis://myredis:6379",
    SECRET_KEY="super-secret-change-me",
))
```

---

## 👨‍💻 Developer Guide

Once you've scaffolded your project, you can easily extend it to build your application.

### 1. Adding a Database Model

Models are built using SQLAlchemy 2.0. Define your models in `app/db/models.py`:

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from boostapi.app.db.database import Base

class Item(Base):
    __tablename__ = "items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
```

### 2. Database Migrations (Alembic)

After adding or modifying a model, generate and apply an Alembic migration:

```bash
# Generate a new migration script based on models
alembic revision --autogenerate -m "Add items table"

# Apply migrations to the database
alembic upgrade head
```

### 3. Creating a New API Route

Add your business logic and routes in `app/api/endpoints/`:

```python
# app/api/endpoints/items.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from boostapi.app.api.deps import get_db
from app.db.models import Item

router = APIRouter()

@router.get("/")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

Then register the router in `app/main.py`!

### 4. Protecting Routes (JWT)

To require authentication, inject the `get_current_user` dependency:

```python
from fastapi import Depends
from boostapi.app.api.deps import get_current_user
from boostapi.app.db.models import User

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}!"}
```

### 5. Using Redis Caching

Inject the Redis client using `get_redis` to cache expensive computations or DB queries:

```python
from fastapi import Depends
from redis.asyncio import Redis
from boostapi.app.api.deps import get_redis

@router.get("/stats")
async def get_stats(redis: Redis = Depends(get_redis)):
    cached = await redis.get("app_stats")
    if cached:
        return {"stats": cached, "cached": True}
    
    # Store with TTL (e.g., 60 seconds)
    stats = "expensive_computation_result"
    await redis.setex("app_stats", 60, stats)
    return {"stats": stats, "cached": False}
```

---

## 🔌 API Reference

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret"}'

# Returns:
# {"access_token": "eyJ...", "token_type": "bearer"}
```

### Health Check

```bash
curl http://localhost:8000/api/v1/health/
# {"status": "healthy", "version": "0.1.0", "db": "ok", "redis": "ok"}
```

---

## 🐳 Docker Compose

BoostAPI ships with a production-ready `docker-compose.yml`:

```yaml
# Included automatically via `boostapi quickstart`
services:
  db:    # postgres:16-alpine
  redis: # redis:7-alpine
  app:   # your FastAPI app
```

---

## ⚙️ Configuration

All settings are configurable via environment variables or `.env` file:

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_SERVER` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_USER` | `postgres` | DB username |
| `POSTGRES_PASSWORD` | `password` | DB password |
| `POSTGRES_DB` | `boostapi` | Database name |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `SECRET_KEY` | *(change me)* | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token TTL (minutes) |

---

## 🧪 Testing

```bash
pip install boostapi[dev]
pytest --cov=boostapi
```

---

## 🚀 Deployment

### Render / Fly.io

```bash
# Set environment variables in your hosting dashboard
# then:
uvicorn boostapi.app.main:app --host 0.0.0.0 --port $PORT
```

### Docker

```bash
docker build -t my-app .
docker compose up
```

### Publish to PyPI

```bash
pip install build twine
python -m build
twine upload dist/*
```

---

## 🏗️ Project Structure

```
my-app/                        # generated by `boostapi quickstart`
├── app/
│   ├── main.py                # create_app() entry point
│   ├── api/endpoints/         # auth, health, etc.
│   ├── core/                  # config, security
│   ├── db/                    # models, migrations
│   └── services/              # business logic
├── tests/                     # pytest suite (90%+ coverage)
├── docker-compose.yml
├── alembic.ini
└── .env
```

---

## 📄 License

MIT © [Dhinakaran](https://github.com/dheena731)
