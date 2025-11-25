"""Pydantic schemas for user input/output used by the API."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, EmailStr
from pydantic import ConfigDict, field_validator, model_validator
from typing import Literal


CalcType = Literal["add", "subtract", "multiply", "divide"]


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class UserReadWithToken(UserRead):
    access_token: str
    token_type: str = "bearer"
    model_config = ConfigDict(from_attributes=True)


class CalculationCreate(BaseModel):
    a: float
    b: float
    type: str

    @field_validator("type", mode="before")
    def normalize_type(cls, v) -> str:
        if not isinstance(v, str):
            raise ValueError("type must be a string")
        low = v.lower()
        if low not in ("add", "subtract", "multiply", "divide"):
            raise ValueError(f"unsupported calculation type: {v!r}")
        return low

    @model_validator(mode="after")
    def check_division_by_zero(self):
        if self.type == "divide" and self.b == 0:
            raise ValueError("division by zero is not allowed in request")
        return self


class CalculationRead(BaseModel):
    id: int
    a: float
    b: float
    type: CalcType
    result: float | None = None
    user_id: int | None = None
    model_config = ConfigDict(from_attributes=True)
