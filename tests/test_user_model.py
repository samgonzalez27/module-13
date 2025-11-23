"""Tests for the User model."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import User


@pytest.fixture(scope="function")
def test_db():
    """Create a test database session."""
    # Use in-memory SQLite for tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_user_creation(test_db):
    """Test creating a user with valid data."""
    user = User(username="testuser", email="test@example.com", password_hash="hashedpassword")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.password_hash == "hashedpassword"
    assert user.created_at is not None


def test_username_unique_constraint(test_db):
    """Test that username must be unique."""
    user1 = User(username="testuser", email="test1@example.com", password_hash="hash1")
    user2 = User(username="testuser", email="test2@example.com", password_hash="hash2")
    test_db.add(user1)
    test_db.commit()

    test_db.add(user2)
    with pytest.raises(Exception):  # IntegrityError
        test_db.commit()


def test_email_unique_constraint(test_db):
    """Test that email must be unique."""
    user1 = User(username="user1", email="test@example.com", password_hash="hash1")
    user2 = User(username="user2", email="test@example.com", password_hash="hash2")
    test_db.add(user1)
    test_db.commit()

    test_db.add(user2)
    with pytest.raises(Exception):  # IntegrityError
        test_db.commit()