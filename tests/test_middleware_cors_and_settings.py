from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_rate_limit_exempt_and_trusted(monkeypatch: pytest.MonkeyPatch) -> None:
    # Enge Limits aktivieren
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "1")
    monkeypatch.setenv("RATE_LIMIT_BURST", "0")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SEC", "60")
    # Ersten App-Start verwenden, um den tatsächlichen client_host zu ermitteln
    importlib.reload(importlib.import_module("app.core.settings"))
    app_mod1 = importlib.reload(importlib.import_module("app.main"))
    app1 = app_mod1.app

    seen_host: list[str] = []
    from typing import Any
    @app1.middleware("http")
    async def _capture_host(request: Any, call_next: Any):
        client = getattr(request, "client", None)
        host = getattr(client, "host", None)
        if isinstance(host, str):
            seen_host.append(host)
        return await call_next(request)

    client1 = TestClient(app1)
    # /health ist exempt und triggert Middleware
    r1 = client1.get("/health")
    assert r1.status_code == 200
    assert seen_host, "Kein client_host erfasst"
    host = seen_host[-1]

    # App mit trusted host neu laden
    import json as _json
    monkeypatch.setenv("RATE_LIMIT_TRUSTED_IPS", _json.dumps([host]))
    importlib.reload(importlib.import_module("app.core.settings"))
    app_mod2 = importlib.reload(importlib.import_module("app.main"))
    app2 = app_mod2.app
    client2 = TestClient(app2)

    ok = client2.get("/")
    assert ok.status_code == 200
    again = client2.get("/")
    assert again.status_code == 200


@pytest.mark.api
def test_cors_headers_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "[\"http://localhost:3000\"]")
    importlib.reload(importlib.import_module("app.core.settings"))
    app_mod = importlib.reload(importlib.import_module("app.main"))
    app = app_mod.app
    client = TestClient(app)

    resp = client.options("/", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
    })
    # Starlette setzt CORS-Header bei passender Origin
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"


@pytest.mark.unit
def test_settings_cors_validator_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    # Verschiedene Eingaben prüfen
    from app.core.settings import Settings

    s1 = Settings.model_validate({"BACKEND_CORS_ORIGINS": "a,b , c "})
    assert s1.BACKEND_CORS_ORIGINS == ["a", "b", "c"]

    s2 = Settings.model_validate({"BACKEND_CORS_ORIGINS": "[\"x\", \"y\"]"})
    assert s2.BACKEND_CORS_ORIGINS == ["x", "y"]

    s3 = Settings.model_validate({"BACKEND_CORS_ORIGINS": ""})
    assert s3.BACKEND_CORS_ORIGINS == []
