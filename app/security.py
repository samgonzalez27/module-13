"""Password hashing utilities using Passlib.

Provides a small, object-oriented wrapper `PasswordHasher` and convenience
module-level helpers `hash_password` and `verify_password` for ease of use in
the rest of the application.
"""
from __future__ import annotations

from passlib.context import CryptContext


class PasswordHasher:
    """Encapsulates password hashing behavior.

    Uses `passlib`'s `CryptContext` to support bcrypt and allow future upgrades
    while keeping a single place to change hashing policy.
    """

    def __init__(self, schemes: list[str] | None = None, deprecated: str | None = None):
        if schemes is None:
            # Use a widely-available and portable scheme by default for tests
            # and environments where the bcrypt backend may not be present.
            schemes = ["pbkdf2_sha256"]
        # Passlib expects `deprecated` to be a string or sequence when provided.
        # Only include it in the CryptContext call when it's not None.
        if deprecated is None:
            self._pwd_context = CryptContext(schemes=schemes)
        else:
            self._pwd_context = CryptContext(schemes=schemes, deprecated=deprecated)

    def hash(self, raw_password: str) -> str:
        """Hash a raw password and return the encoded hash."""
        return self._pwd_context.hash(raw_password)

    def verify(self, raw_password: str, hashed: str) -> bool:
        """Verify a raw password against the stored hash."""
        return self._pwd_context.verify(raw_password, hashed)


# Module-level default hasher and helpers
_default_hasher = PasswordHasher()


def hash_password(raw_password: str) -> str:
    """Hash `raw_password` using the default PasswordHasher instance.

    Returns the encoded password string suitable for storage.
    """
    return _default_hasher.hash(raw_password)


def verify_password(raw_password: str, hashed: str) -> bool:
    """Verify `raw_password` against the stored hash.

    Returns True when the password matches, False otherwise.
    """
    return _default_hasher.verify(raw_password, hashed)
