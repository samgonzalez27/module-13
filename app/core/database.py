"""Database configuration and session management.

This module reads `DATABASE_URL` from the environment when present so the
application can use Postgres in Docker/CI and SQLite locally as a fallback.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Prefer DATABASE_URL from environment (used in Docker/CI). Fall back to
# a local SQLite file for development and tests that don't set DATABASE_URL.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# SessionLocal is a factory used by the application to create sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # pylint: disable=invalid-name

Base = declarative_base()
