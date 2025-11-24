"""Tests for Calculation compute behavior and user foreign-key relation."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Calculation, User


@pytest.fixture(scope="function")
def test_db():
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


def test_compute_and_persist_default(test_db):
    calc = Calculation(a=2, b=3, type="add")
    # compute_result should persist by default
    val = calc.compute_result()
    assert val == 5
    assert calc.result == 5


def test_compute_without_persist(test_db):
    calc = Calculation(a=10, b=4, type="subtract")
    val = calc.compute_result(persist=False)
    assert val == 6
    assert calc.result is None


def test_force_overwrite_existing_result(test_db):
    calc = Calculation(a=6, b=3, type="divide", result=2.0)
    # default persist True should overwrite when force=True
    val = calc.compute_result(force=True)
    assert val == 2.0
    assert calc.result == 2.0


def test_user_foreign_key_relationship(test_db):
    user = User(username="owner", email="owner@example.com", password_hash="x")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    calc = Calculation(a=1, b=2, type="multiply", user_id=user.id)
    test_db.add(calc)
    test_db.commit()
    test_db.refresh(calc)

    assert calc.user is not None
    assert calc.user.id == user.id


def test_unsupported_type_raises():
    calc = Calculation(a=1, b=1, type="noop")
    with pytest.raises(ValueError):
        calc.compute_result(persist=False)
