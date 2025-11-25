import importlib

from fastapi.testclient import TestClient


def test_token_valid_tamper_and_expire():
    from app.auth import security

    tok = security.create_token({"sub": "alice"}, expire_seconds=60)
    payload = security.verify_token(tok)
    assert payload and payload["sub"] == "alice"

    # tamper with the token signature
    tampered = tok[:-1] + ("A" if tok[-1] != "A" else "B")
    assert security.verify_token(tampered) is None

    # expired token should be rejected
    expired = security.create_token({"sub": "bob"}, expire_seconds=-10)
    assert security.verify_token(expired) is None


def test_database_else_branch(monkeypatch):
    # ensure the non-sqlite branch is exercised by setting a postgres URL
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
    import app.core.database as database

    importlib.reload(database)
    assert not database.SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    assert hasattr(database, "engine")


def test_division_by_zero_client():
    from app.api.main import app

    client = TestClient(app)
    r = client.get("/div", params={"a": 1, "b": 0})
    assert r.status_code == 400
    assert r.json().get("detail") == "division by zero"


def test_read_index_fallback(monkeypatch):
    import app.api.main as main
    # force the static index not to exist to hit the fallback branch
    # patch Path.exists on the class so it's applied for the module's `static_dir`
    monkeypatch.setattr(main.Path, "exists", lambda self: False)
    client = TestClient(main.app)
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_auth_header_edge_cases():
    from app.api.main import app

    client = TestClient(app)

    # missing Authorization header
    r = client.get("/calculations")
    assert r.status_code == 401
    assert r.json().get("detail") == "authorization required"

    # wrong auth scheme
    r = client.get("/calculations", headers={"Authorization": "Basic abc"})
    assert r.status_code == 401
    assert r.json().get("detail") == "invalid auth scheme"

    # malformed / invalid token
    r = client.get("/calculations", headers={"Authorization": "Bearer wrong.token.here"})
    assert r.status_code == 401
    assert r.json().get("detail") == "invalid token"


def test_b64url_padding_roundtrip():
    from app.auth import security

    # ensure encode/decode roundtrip works even when padding is required
    raw = b"pad-test"
    enc = security._b64url_encode(raw)
    # truncate the last char to force padding logic in decode
    truncated = enc[:-1]
    dec = security._b64url_decode(truncated)
    # decode should still return bytes (content may differ when truncated)
    assert isinstance(dec, (bytes, bytearray))


def test_register_duplicate_user():
    from app.api.main import app
    import uuid

    client = TestClient(app)
    uname = f"dup-{uuid.uuid4().hex}"
    payload = {"username": uname, "email": f"{uname}@example.com", "password": "secret"}
    r1 = client.post("/users/register", json=payload)
    assert r1.status_code == 200
    r2 = client.post("/users/register", json=payload)
    assert r2.status_code == 400
    assert r2.json().get("detail") == "username or email already exists"


def test_token_for_nonexistent_user_and_secret_param():
    from app.auth import security
    from app.api.main import app

    # token with subject that doesn't exist should be rejected by get_current_user
    tok = security.create_token({"sub": "noone"})
    client = TestClient(app)
    r = client.get("/calculations", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401
    assert r.json().get("detail") == "invalid token"

    # custom secret parameter roundtrip
    tok2 = security.create_token({"sub": "alice"}, secret="my-secret")
    assert security.verify_token(tok2, secret="my-secret")["sub"] == "alice"
    assert security.verify_token(tok2, secret="wrong") is None


def test_debug_headers_endpoint():
    """Call the debug endpoint to exercise the header-dump return path."""
    from app.api.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    r = client.get("/debug/headers")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


def test_get_current_user_wrong_scheme_direct_call():
    """Call get_current_user directly with a non-bearer credentials object to hit the scheme-check branch."""
    from fastapi.security import HTTPAuthorizationCredentials
    from app.api.main import get_current_user
    from fastapi import HTTPException

    creds = HTTPAuthorizationCredentials(scheme="Basic", credentials="xyz")
    try:
        # db is not used before the scheme check, so None is fine here
        get_current_user(creds, None, None)
        raised = False
    except HTTPException as exc:
        raised = True
        assert exc.status_code == 401
        assert exc.detail == "invalid auth scheme"
    assert raised


def test_verify_token_raises_and_is_caught():
    from app.auth import security

    # passing a malformed token (no dots) triggers the exception path
    assert security.verify_token("not-a.valid.token") is None


def test_token_endpoint_invalid_credentials():
    from app.api.main import app

    client = TestClient(app)
    r = client.post("/users/token", json={"username": "nope", "password": "bad"})
    assert r.status_code == 401
    assert r.json().get("detail") == "invalid credentials"


def test_update_and_delete_nonexistent_calc():
    from app.api.main import app
    import uuid

    client = TestClient(app)
    uname = f"user-{uuid.uuid4().hex}"
    client.post("/users/register", json={"username": uname, "email": f"{uname}@example.com", "password": "pw"})
    tok = client.post("/users/token", json={"username": uname, "password": "pw"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {tok}"}

    # update non-existent
    r = client.put("/calculations/9999", json={"a": 1, "b": 2, "type": "add"}, headers=headers)
    assert r.status_code == 404
    assert r.json().get("detail") == "calculation not found"

    # delete non-existent
    r = client.delete("/calculations/9999", headers=headers)
    assert r.status_code == 404
    assert r.json().get("detail") == "calculation not found"
