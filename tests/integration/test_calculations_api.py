from uuid import uuid4

from fastapi.testclient import TestClient
from app.api.main import app


client = TestClient(app)


def get_token(email: str, password: str):
    r = client.post("/users/token", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_calculation_crud_flow():
    unique = uuid4().hex[:8]
    username = f"u_{unique}"
    email = f"{unique}@example.com"
    password = "pwtok"

    # register
    r = client.post("/users/register", json={"username": username, "email": email, "password": password})
    assert r.status_code == 200

    token = get_token(email, password)
    headers = {"Authorization": f"Bearer {token}"}

    # create calculation
    payload = {"a": 3, "b": 4, "type": "add"}
    r = client.post("/calculations", json=payload, headers=headers)
    assert r.status_code == 201
    calc = r.json()
    assert calc["a"] == 3
    assert calc["b"] == 4
    assert calc["type"] == "add"
    assert calc["result"] == 7
    calc_id = calc["id"]

    # list calculations
    r = client.get("/calculations", headers=headers)
    assert r.status_code == 200
    items = r.json()
    assert any(it["id"] == calc_id for it in items)

    # get single
    r = client.get(f"/calculations/{calc_id}", headers=headers)
    assert r.status_code == 200
    single = r.json()
    assert single["id"] == calc_id

    # update
    r = client.put(f"/calculations/{calc_id}", json={"a": 10, "b": 5, "type": "subtract"}, headers=headers)
    assert r.status_code == 200
    updated = r.json()
    assert updated["result"] == 5

    # delete
    r = client.delete(f"/calculations/{calc_id}", headers=headers)
    assert r.status_code == 204

    # ensure gone
    r = client.get(f"/calculations/{calc_id}", headers=headers)
    assert r.status_code == 404
