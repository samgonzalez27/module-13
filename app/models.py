"""SQLAlchemy models for the application."""

from sqlalchemy import Column, Integer, String, DateTime, func

from .database import Base


class User(Base):
    """SQLAlchemy ORM model representing an application user.

    The model stores a hashed password and the creation timestamp.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False  # pylint: disable=not-callable
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} username={self.username!r}>"

    def to_dict(self) -> dict:
        """Return a dictionary representation of the user (safe for JSON responses).

        The returned dict intentionally omits `password_hash`.
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at,
        }
