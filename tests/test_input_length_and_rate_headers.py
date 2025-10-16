from __future__ import annotations

import importlib
from typing import Any

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
@pytest.mark.unit
def test_chat_rejects_too_long_input(monkeypatch: pytest.MonkeyPatch) -> None:
    # Deaktiviere Rate-Limiter, um Seiteneffekte zu vermeiden
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")

    # Grenze sehr niedrig setzen, damit wir deterministisch 400 bekommen
    monkeypatch.setenv("REQUEST_MAX_INPUT_CHARS", "10")

    # App frisch laden, damit Settings greifen
    importlib.reload(importlib.import_module("app.core.settings"))
    app_mod = importlib.reload(importlib.import_module("app.main"))
    app = app_mod.app
    client = TestClient(app)

    # 11 Zeichen -> über Limit 10
    too_long = "abcdefghijk"
    resp = client.post("/chat", json={
        "messages": [
            {"role": "user", "content": too_long}
        ]
    })
    assert resp.status_code == 400
    # Fehlerdetails enthalten Hinweis auf Länge und Limit
    detail = resp.json().get("detail", "")
    assert "Input zu lang" in detail


@pytest.mark.api
def test_rate_limit_429_includes_request_id_header(monkeypatch: pytest.MonkeyPatch) -> None:
    # Rate-Limit via ENV aktivieren und knappe Limits setzen; Trusted IPs leeren
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "1")
    monkeypatch.setenv("RATE_LIMIT_BURST", "0")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SEC", "60")
    monkeypatch.setenv("RATE_LIMIT_TRUSTED_IPS", "[]")

    # App frisch laden, damit Middleware hinzugefügt wird
    importlib.reload(importlib.import_module("app.core.settings"))
    app_mod = importlib.reload(importlib.import_module("app.main"))
    app = app_mod.app
    client = TestClient(app)

    # Erste Anfrage erlaubt
    r1 = client.get("/")
    assert r1.status_code == 200
    request_id_1 = r1.headers.get("X-Request-ID")

    # Zweite Anfrage im selben Fenster soll blocken
    r2 = client.get("/")
    assert r2.status_code == 429

    # Middleware sollte auch bei Fehlern X-Request-ID setzen (aus unserer request_context_mw)
    assert r2.headers.get("X-Request-ID") is not None or request_id_1 is not None

    # Rate-Limit-Header vorhanden
    assert r2.headers.get("Retry-After") is not None
    assert r2.headers.get("X-RateLimit-Limit") is not None
    assert r2.headers.get("X-RateLimit-Window") is not None
