from uuid import uuid4

from fastapi.testclient import TestClient
from app.api.main import app


client = TestClient(app)


def test_register_returns_token_and_token_works():
    unique = uuid4().hex[:8]
    username = f"u_{unique}"
    email = f"{unique}@example.com"
    password = "pw-token"

    # register - should return access_token and user fields
    r = client.post("/users/register", json={"username": username, "email": email, "password": password})
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == username
    assert data["email"] == email
    assert "access_token" in data

    # use token to call protected endpoint (no calculations yet, so just ensure authorization resolves)
    tok = data["access_token"]
    headers = {"Authorization": f"Bearer {tok}"}
    # list calculations (should be empty list)
    r_list = client.get("/calculations", headers=headers)
    assert r_list.status_code == 200
    assert isinstance(r_list.json(), list)
