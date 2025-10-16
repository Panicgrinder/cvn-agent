from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
@pytest.mark.api
def test_root_endpoint_basic() -> None:
    # Schnelltest für den Root-Handler
    app_mod = importlib.import_module("app.main")
    client = TestClient(app_mod.app)
    r = client.get("/")
    assert r.status_code == 200
    assert r.json().get("message")
