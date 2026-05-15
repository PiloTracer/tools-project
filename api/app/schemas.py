from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field


class LocalLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    is_superuser: bool
    auth: str = "local"


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=1024)
    display_name: str | None = None
    is_superuser: bool = False


class AdminUserUpdate(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=1024)
    display_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class AdminUserOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    is_active: bool
    is_superuser: bool

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    items: list[AdminUserOut]
