from __future__ import annotations

import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
@pytest.mark.unit
def test_version_endpoint_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    # Frisch laden, um saubere Settings zu haben
    importlib.reload(importlib.import_module("app.core.settings"))
    app_mod = importlib.reload(importlib.import_module("app.main"))
    app = app_mod.app
    client = TestClient(app)
    r = client.get("/version")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("app_name"), str)
    assert isinstance(data.get("version"), str)
    # envs können None sein
    assert "git_sha" in data and "build_time" in data
    assert isinstance(data.get("python_version"), str)


@pytest.mark.api
def test_version_endpoint_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_SHA", "abc1234")
    monkeypatch.setenv("BUILD_TIME", "2025-10-19T12:00:00Z")
    importlib.reload(importlib.import_module("app.core.settings"))
    app_mod = importlib.reload(importlib.import_module("app.main"))
    app = app_mod.app
    client = TestClient(app)
    r = client.get("/version")
    assert r.status_code == 200
    data = r.json()
    assert data.get("git_sha") == "abc1234"
    assert data.get("build_time") == "2025-10-19T12:00:00Z"