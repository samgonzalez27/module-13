"""Password hashing utilities using Passlib.

Provides a small, object-oriented wrapper `PasswordHasher` and convenience
module-level helpers `hash_password` and `verify_password` for ease of use in
the rest of the application.
"""
from __future__ import annotations

from passlib.context import CryptContext
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Dict, Any

import jwt
from jwt import PyJWTError


class PasswordHasher:
    def __init__(self, schemes: list[str] | None = None, deprecated: str | None = None):
        if schemes is None:
            schemes = ["pbkdf2_sha256"]
        if deprecated is None:
            self._pwd_context = CryptContext(schemes=schemes)
        else:
            self._pwd_context = CryptContext(schemes=schemes, deprecated=deprecated)

    def hash(self, raw_password: str) -> str:
        return self._pwd_context.hash(raw_password)

    def verify(self, raw_password: str, hashed: str) -> bool:
        return self._pwd_context.verify(raw_password, hashed)


_default_hasher = PasswordHasher()


def hash_password(raw_password: str) -> str:
    return _default_hasher.hash(raw_password)


def verify_password(raw_password: str, hashed: str) -> bool:
    return _default_hasher.verify(raw_password, hashed)


# Minimal JWT-like functions (HMAC-SHA256, no external dependency)
_JWT_SECRET = os.environ.get("SECRET_KEY", "dev-secret-change-me")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = 4 - (len(s) % 4)
    if padding != 4:
        s = s + ("=" * padding)
    return base64.urlsafe_b64decode(s.encode("ascii"))


def create_token(payload: Dict[str, Any], secret: str | None = None, expire_seconds: int = 3600) -> str:
    """Create a JWT using HS256.

    The `secret` parameter is optional and overrides the environment `SECRET_KEY`.
    """
    if secret is None:
        secret = _JWT_SECRET
    now = int(time.time())
    body = {**payload, "iat": now, "exp": now + expire_seconds}
    token = jwt.encode(body, secret, algorithm="HS256")
    # PyJWT returns a string in modern versions
    return token


def verify_token(token: str, secret: str | None = None) -> Dict[str, Any] | None:
    """Verify the JWT and return the payload or None on failure."""
    if secret is None:
        secret = _JWT_SECRET
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except PyJWTError:
        return None
