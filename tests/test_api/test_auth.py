"""Tests for authentication endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestLogin:
    async def test_login_success(self, client: AsyncClient, test_user) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpassword"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_login_wrong_password(self, client: AsyncClient, test_user) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_login_unknown_user(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "password"},
        )
        assert response.status_code == 401

    async def test_login_missing_fields(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422


class TestRegister:
    async def test_register_success(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securepassword",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_duplicate_username(self, client: AsyncClient, test_user) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",  # Already exists
                "email": "other@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 409

    async def test_register_short_password(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={"username": "user", "email": "u@e.com", "password": "short"},
        )
        assert response.status_code == 422


class TestMe:
    async def test_me_authenticated(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["is_active"] is True

    async def test_me_unauthenticated(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
