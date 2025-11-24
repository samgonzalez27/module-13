"""FastAPI calculator application with centralized logging."""
import logging
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Depends, Security
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..config.logging_config import configure_logging
from ..core.calculator import add, sub, mul, div
from ..core import models
from ..core.database import SessionLocal, engine, Base
from ..api.schemas import UserCreate, UserRead, LoginRequest, CalculationCreate, CalculationRead
from ..auth.security import hash_password, verify_password, create_token, verify_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Header
from typing import List

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


@app.get("/debug/headers")
def debug_headers(request: Request):
    """Debug-only endpoint: return request headers as a simple dict.

    Use this from the Swagger UI (or curl) to confirm whether the
    `Authorization` header is actually being sent to the server.
    """
    return dict(request.headers)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting FastAPI Calculator app")
    # ensure database tables exist for simple development/testing
    Base.metadata.create_all(bind=engine)


# Ensure tables exist even if startup event isn't triggered (tests may import module)
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


@app.post("/users/token")
def token(payload: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not db_user or not verify_password(payload.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    tok = create_token({"sub": db_user.username})
    return {"access_token": tok, "token_type": "bearer"}


bearer_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme), db: Session = Depends(get_db)):
    """Resolve the current user from an HTTP Bearer token.

    Uses `HTTPBearer` so OpenAPI will include a Bearer security scheme and
    the Swagger UI will show an Authorize button.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="authorization required")
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="invalid auth scheme")
    token = credentials.credentials
    payload = verify_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="invalid token")
    user = db.query(models.User).filter(models.User.username == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="invalid token")
    return user


@app.post("/calculations", response_model=CalculationRead, status_code=201)
def create_calculation(data: CalculationCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    calc = models.Calculation(a=data.a, b=data.b, type=data.type, user_id=current_user.id)
    db.add(calc)
    # compute and persist result
    calc.compute_result(persist=True)
    db.commit()
    db.refresh(calc)
    return CalculationRead.model_validate(calc)


@app.get("/calculations", response_model=List[CalculationRead])
def list_calculations(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(models.Calculation).filter(models.Calculation.user_id == current_user.id).all()
    return [CalculationRead.model_validate(i) for i in items]


@app.get("/calculations/{calc_id}", response_model=CalculationRead)
def get_calculation(calc_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    calc = db.query(models.Calculation).filter(models.Calculation.id == calc_id, models.Calculation.user_id == current_user.id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="calculation not found")
    return CalculationRead.model_validate(calc)


@app.put("/calculations/{calc_id}", response_model=CalculationRead)
def update_calculation(calc_id: int, data: CalculationCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    calc = db.query(models.Calculation).filter(models.Calculation.id == calc_id, models.Calculation.user_id == current_user.id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="calculation not found")
    calc.a = data.a
    calc.b = data.b
    calc.type = data.type
    calc.compute_result(persist=True, force=True)
    db.commit()
    db.refresh(calc)
    return CalculationRead.model_validate(calc)


@app.delete("/calculations/{calc_id}", status_code=204)
def delete_calculation(calc_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    calc = db.query(models.Calculation).filter(models.Calculation.id == calc_id, models.Calculation.user_id == current_user.id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="calculation not found")
    db.delete(calc)
    db.commit()
    return


@app.post("/users/login", response_model=UserRead)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user by username and password.

    Returns `UserRead` on success, 401 otherwise.
    """
    db_user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not db_user or not verify_password(payload.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    return UserRead.model_validate(db_user)
