from __future__ import annotations

import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_404_has_request_id_header() -> None:
    app_mod = importlib.import_module("app.main")
    app = app_mod.app
    client = TestClient(app)
    r = client.get("/definitely-not-found")
    assert r.status_code == 404
    assert r.headers.get("X-Request-ID")
