from __future__ import annotations

from pydantic import BaseModel, Field

PASSWORD_MIN_LEN = 8
PASSWORD_MAX_LEN = 32


class LoginRequest(BaseModel):
    password: str = Field(..., min_length=1)


class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    role: str
    password: str = Field(..., min_length=PASSWORD_MIN_LEN, max_length=PASSWORD_MAX_LEN)


class UpdateUserRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    role: str | None = None
    password: str | None = Field(default=None, min_length=PASSWORD_MIN_LEN, max_length=PASSWORD_MAX_LEN)
