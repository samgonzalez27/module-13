"""Pydantic schemas for user input/output.

- `UserCreate` for incoming user creation payloads (contains `password`).
- `UserRead` for returning user data to clients (omits `password_hash`).

This file uses Pydantic v2 conventions (`model_config = ConfigDict(from_attributes=True)`)
so schemas can be created with `.model_validate()` or `.model_validate()` from
ORM objects/dicts.
"""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, EmailStr
from pydantic import ConfigDict


class UserCreate(BaseModel):
    """Schema for user creation requests.

    Includes the plain-text `password` field which will be hashed before
    storing in the database.
    """

    username: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    """Schema for returning user data to clients.

    This deliberately omits any password or password_hash fields.
    """

    id: int
    username: str
    email: EmailStr
    created_at: datetime | None = None

    # enable ORM-style population (Pydantic v2)
    model_config = ConfigDict(from_attributes=True)
