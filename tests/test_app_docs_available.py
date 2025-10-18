from __future__ import annotations

from fastapi.testclient import TestClient
import importlib
import pytest


@pytest.mark.api
@pytest.mark.unit
def test_docs_served() -> None:
    app_mod = importlib.import_module("app.main")
    client = TestClient(app_mod.app)
    r = client.get("/docs")
    assert r.status_code == 200
    # Swagger UI enthält ein script-Tag mit 'swagger-ui'
    assert "swagger-ui" in r.text or "Swagger UI" in r.text
