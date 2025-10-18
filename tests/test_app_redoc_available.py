from __future__ import annotations

from fastapi.testclient import TestClient
import importlib
import pytest


@pytest.mark.api
@pytest.mark.unit
def test_redoc_served() -> None:
    app_mod = importlib.import_module("app.main")
    client = TestClient(app_mod.app)
    r = client.get("/redoc")
    assert r.status_code == 200
    assert "redoc" in r.text.lower()
