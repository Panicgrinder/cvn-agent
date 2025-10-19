from __future__ import annotations

import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
@pytest.mark.unit
def test_request_id_header_on_400(monkeypatch: pytest.MonkeyPatch) -> None:
    # Rate-Limiter deaktivieren, nur Input-400 testen
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("REQUEST_MAX_INPUT_CHARS", "1")
    importlib.reload(importlib.import_module("app.core.settings"))
    app_mod = importlib.reload(importlib.import_module("app.main"))
    app = app_mod.app
    client = TestClient(app)

    try:
        resp = client.post("/chat", json={"messages": [{"role": "user", "content": "xx"}]})
        assert resp.status_code == 400
        # Unsere Middleware sollte die Request-ID setzen
        assert resp.headers.get("X-Request-ID") is not None
    finally:
        # Cleanup: env zurücksetzen und Module neu laden, damit Folgetests Standardwerte nutzen
        monkeypatch.delenv("REQUEST_MAX_INPUT_CHARS", raising=False)
        monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)
        importlib.reload(importlib.import_module("app.core.settings"))
        importlib.reload(importlib.import_module("app.main"))
