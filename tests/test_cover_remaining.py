import pytest

from fastapi.testclient import TestClient

from app.api import main
from app.api.schemas import CalculationCreate
from pydantic import ValidationError
from app.core.models import User


client = TestClient(main.app)


def test_operands_and_basic_arithmetic_routes():
    # exercise the Operands model by instantiating it
    op = main.Operands(a=3, b=4)
    assert op.a == 3
    assert op.b == 4

    r = client.get("/add", params={"a": 3, "b": 4})
    assert r.status_code == 200
    assert r.json()["result"] == 7

    r = client.get("/sub", params={"a": 10, "b": 4})
    assert r.status_code == 200
    assert r.json()["result"] == 6

    r = client.get("/mul", params={"a": 6, "b": 7})
    assert r.status_code == 200
    assert r.json()["result"] == 42


def test_calculationcreate_non_string_type_raises():
    with pytest.raises(ValidationError):
        CalculationCreate(a=1, b=2, type=123)


def test_user_repr_and_to_dict_cover():
    u = User()
    u.id = 1
    u.username = "bob"
    u.email = "bob@example.com"
    u.password_hash = "x"
    # created_at left as default None to ensure to_dict includes it
    d = u.to_dict()
    assert d["id"] == 1
    assert d["username"] == "bob"
    # repr works
    r = repr(u)
    assert "User" in r


def test_read_index_serves_file():
    # When the static index exists, the root should serve the file (HTML)
    r = client.get("/")
    assert r.status_code == 200
    ct = r.headers.get("content-type", "")
    assert "text/html" in ct
    assert "<!doctype html" in r.text.lower()
