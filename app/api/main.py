"""FastAPI calculator application with centralized logging."""
import logging
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..config.logging_config import configure_logging
from ..core.calculator import add, sub, mul, div
from ..core import models
from ..core.database import SessionLocal, engine, Base
from ..api.schemas import UserCreate, UserRead, LoginRequest
from ..auth.security import hash_password, verify_password

# ensure logging is configured (idempotent)
configure_logging()

logger = logging.getLogger("calculator")


class Operands(BaseModel):
    a: float
    b: float


app = FastAPI()

# static files live in the package root `app/static`, not next to this module
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def read_index():
    index = static_dir / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    logger.info("Starting FastAPI Calculator app")
    # ensure database tables exist for simple development/testing
    Base.metadata.create_all(bind=engine)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    logger.info("Incoming request %s %s", request.method, request.url)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled exception during request")
        raise
    duration = time.time() - start
    logger.info(
        "Completed %s %s with status=%s in %.3fs",
        request.method,
        request.url,
        response.status_code,
        duration,
    )
    return response


@app.get("/add")
def route_add(a: float, b: float):
    result = add(a, b)
    return {"operation": "add", "a": a, "b": b, "result": result}


@app.get("/sub")
def route_sub(a: float, b: float):
    result = sub(a, b)
    return {"operation": "sub", "a": a, "b": b, "result": result}


@app.get("/mul")
def route_mul(a: float, b: float):
    result = mul(a, b)
    return {"operation": "mul", "a": a, "b": b, "result": result}


@app.get("/div")
def route_div(a: float, b: float):
    try:
        result = div(a, b)
    except ZeroDivisionError as exc:
        logger.warning("Attempted division by zero: %s / %s", a, b)
        raise HTTPException(status_code=400, detail="division by zero") from exc
    return {"operation": "div", "a": a, "b": b, "result": result}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user.

    Accepts a `UserCreate` payload, hashes the password and stores the user.
    Returns a `UserRead` representation on success.
    """
    hashed = hash_password(user.password)
    db_user = models.User(username=user.username, email=user.email, password_hash=hashed)
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="username or email already exists")

    return UserRead.model_validate(db_user)


@app.post("/users/login", response_model=UserRead)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user by username and password.

    Returns `UserRead` on success, 401 otherwise.
    """
    db_user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not db_user or not verify_password(payload.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    return UserRead.model_validate(db_user)
