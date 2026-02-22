"""Pydantic schemas for authentication."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Credentials for ``POST /api/v1/auth/login``."""

    username: str = Field(..., min_length=1, max_length=64, examples=["admin"])
    password: str = Field(..., min_length=1, examples=["secret"])


class RegisterRequest(BaseModel):
    """Payload for ``POST /api/v1/auth/register``."""

    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")


class TokenResponse(BaseModel):
    """JWT token pair returned after successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token lifetime in seconds")


class UserOut(BaseModel):
    """Public user representation (no password)."""

    id: str
    username: str
    email: str
    is_active: bool
    is_superuser: bool

    model_config = {"from_attributes": True}
