from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
@pytest.mark.api
def test_root_has_request_id_header() -> None:
    app_mod = importlib.import_module("app.main")
    client = TestClient(app_mod.app)
    r = client.get("/")
    assert r.status_code == 200
    # Middleware sollte eine X-Request-ID gesetzt haben
    assert r.headers.get(app_mod.settings.REQUEST_ID_HEADER)
