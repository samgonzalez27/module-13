import subprocess
import sys

import pytest

from fastapi.testclient import TestClient

from app.api import main


client = TestClient(main.app)


def test_division_by_zero_api():
    r = client.get("/div", params={"a": 1, "b": 0})
    assert r.status_code == 400
    assert "division by zero" in r.json().get("detail", "")


def test_startup_event_runs_and_logs():
    """Test that startup event can be called without error.
    
    Run in a subprocess to avoid event loop conflicts with Playwright tests.
    """
    code = """
import asyncio
from app.api.main import startup_event
asyncio.run(startup_event())
print("OK")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd="/home/samuel/school-projects/module-13",
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "OK" in result.stdout