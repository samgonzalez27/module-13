"""Postgres integration tests for Calculation persistence.

These tests run only when the environment variable `DATABASE_URL` is set
(the CI workflow sets this to a PostgreSQL service). Locally they will be
skipped so developers aren't required to run a local Postgres instance.
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Calculation
from app.schemas import CalculationCreate


@pytest.fixture(scope="module")
def pg_session():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("Postgres DATABASE_URL not set; skipping integration tests")

    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_insert_calculation_persists(pg_session):
    # use schema to validate input first (integration with schema layer)
    payload = CalculationCreate(a=2.0, b=3.0, type="add")
    calc = Calculation(a=payload.a, b=payload.b, type=payload.type, result=None)
    pg_session.add(calc)
    pg_session.commit()
    pg_session.refresh(calc)

    assert calc.id is not None
    assert calc.a == 2.0
    assert calc.b == 3.0
    assert calc.type == "add"


def test_invalid_type_rejected_before_db(pg_session):
    # schema-level validation should prevent invalid types reaching the DB
    with pytest.raises(Exception):
        CalculationCreate(a=1, b=1, type="noop")


def test_divide_by_zero_rejected_by_schema(pg_session):
    with pytest.raises(Exception):
        CalculationCreate(a=1, b=0, type="divide")
