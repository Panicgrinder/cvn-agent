from __future__ import annotations

import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
@pytest.mark.unit
def test_rate_limit_headers_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    # Enable limiter and trusted IPs empty to enforce checks
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "5")
    monkeypatch.setenv("RATE_LIMIT_BURST", "0")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SEC", "10")
    monkeypatch.setenv("RATE_LIMIT_TRUSTED_IPS", "[]")

    # Reload settings/app
    importlib.reload(importlib.import_module("app.core.settings"))
    app_mod = importlib.reload(importlib.import_module("app.main"))
    client = TestClient(app_mod.app)

    r = client.get("/")
    assert r.status_code == 200
    assert r.headers.get("X-RateLimit-Limit") is not None
    assert r.headers.get("X-RateLimit-Remaining") is not None
    assert r.headers.get("X-RateLimit-Window") is not None
