"""SQLAlchemy models for the application."""

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import relationship

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



class Calculation(Base):
    """SQLAlchemy ORM model representing a calculation request/result.

    Fields:
    - id: primary key
    - a: first numeric operand
    - b: second numeric operand
    - type: operation type (e.g. 'add', 'subtract', ...)
    - result: optional numeric result
    """

    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    a = Column(Float, nullable=False)
    b = Column(Float, nullable=False)
    type = Column(String, nullable=False, index=True)
    result = Column(Float, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # SQLAlchemy relationship to `User` (optional)
    user = relationship("User", backref="calculations")

    def compute_result(self, persist: bool = True, force: bool = False) -> float:
        """Compute the calculation result using the operations module.

        By default, the computed result is persisted to `self.result`. Set
        `persist=False` to compute without modifying the model. If `force` is
        True the stored `result` will be overwritten regardless of whether it
        already exists.

        Returns:
            The computed numeric result.
        """
        # local import to avoid circular imports at module import time
        # Use the CalculationFactory to obtain an operation object.
        from .factory import CalculationFactory

        factory = CalculationFactory()
        op = factory.get(self.type)
        computed = op.compute(self.a, self.b)

        if persist and (self.result is None or force):
            self.result = computed

        return computed

    def __repr__(self) -> str:
        return f"<Calculation id={self.id!r} type={self.type!r} a={self.a!r} b={self.b!r} result={self.result!r}>"

    def to_dict(self) -> dict:
        return {"id": self.id, "a": self.a, "b": self.b, "type": self.type, "result": self.result}
