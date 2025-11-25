from uuid import uuid4

from fastapi.testclient import TestClient
from app.api.main import app


client = TestClient(app)


def test_division_by_zero_returns_400():
    r = client.get("/div", params={"a": 1, "b": 0})
    assert r.status_code == 400
    assert r.json()["detail"] == "division by zero"


def test_register_user_and_duplicate():
    unique = uuid4().hex[:8]
    payload = {"username": f"u_{unique}", "email": f"{unique}@example.com", "password": "pw"}

    # first registration should succeed
    r = client.post("/users/register", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert "id" in data

    # second registration with same username/email should fail
    r2 = client.post("/users/register", json=payload)
    assert r2.status_code == 400
    assert "already exists" in r2.json()["detail"]


def test_login_success_and_failures():
    unique = uuid4().hex[:8]
    username = f"u_{unique}"
    email = f"{unique}@example.com"
    password = "pw123"

    # create the user first
    r = client.post("/users/register", json={"username": username, "email": email, "password": password})
    assert r.status_code == 200

    # correct credentials -> success and return token
    r_login = client.post("/users/login", json={"email": email, "password": password})
    assert r_login.status_code == 200
    d = r_login.json()
    assert "access_token" in d
    assert d["token_type"] == "bearer"

    # wrong password -> unauthorized
    r_wrong = client.post("/users/login", json={"email": email, "password": "wrong"})
    assert r_wrong.status_code == 401
    assert r_wrong.json()["detail"] == "invalid credentials"

    # non-existent email -> unauthorized
    r_no = client.post("/users/login", json={"email": "noone@example.com", "password": "pw"})
    assert r_no.status_code == 401
    assert r_no.json()["detail"] == "invalid credentials"
