"""Pytest configuration: test fixtures, database & app setup."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from boostapi.app.main import create_app
from boostapi.app.core.config import Settings
from boostapi.app.db.database import Base, get_db
from boostapi.app.db.models import User
from boostapi.app.core.security import hash_password

# ── In-memory SQLite for tests ─────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        REDIS_URL="redis://localhost:6379",
        SECRET_KEY="test-secret-key-for-pytest",
        ENV="test",
    )


def _create_tables_compat(conn):
    """Create tables in SQLite for testing."""
    Base.metadata.create_all(conn)

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(_create_tables_compat)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncSession:
    TestingSessionLocal = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


class MockRedis:
    """Simple mock for Redis caching in tests."""
    def __init__(self):
        self._data = {}
    
    async def get(self, key):
        return self._data.get(key)
        
    async def setex(self, key, time, value):
        self._data[key] = value

    async def close(self):
        pass

@pytest_asyncio.fixture
async def mock_redis():
    return MockRedis()

@pytest_asyncio.fixture
async def client(db_session: AsyncSession, test_settings: Settings, mock_redis: MockRedis) -> AsyncClient:
    """HTTPX async test client with overridden DB dependency."""
    app = create_app(settings=test_settings)

    from boostapi.app.api.deps import get_redis

    async def override_get_db():
        yield db_session

    async def override_get_redis():
        yield mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create and persist a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpassword"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict[str, str]:
    """Return Authorization headers for the test user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpassword"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}



