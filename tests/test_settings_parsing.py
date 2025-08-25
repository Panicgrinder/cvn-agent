from __future__ import annotations

from importlib import reload
from pytest import MonkeyPatch

from app.core import settings as settings_module


def test_settings_parsing_from_env(monkeypatch: MonkeyPatch) -> None:
    # Set env vars
    monkeypatch.setenv("PROJECT_NAME", "My App")
    monkeypatch.setenv("PROJECT_DESCRIPTION", "Desc")
    monkeypatch.setenv("PROJECT_VERSION", "9.9.9")
    # In pydantic-settings v2 müssen Listenfelder als JSON serialisiert werden
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "[\"http://localhost:3000\", \"http://127.0.0.1:5173\"]")
    monkeypatch.setenv("OLLAMA_HOST", "http://host:11434")
    monkeypatch.setenv("MODEL_NAME", "m:1")

    # Recreate settings via module reload (settings instance is created at import time)
    reload(settings_module)
    s = settings_module.settings

    assert s.PROJECT_NAME == "My App"
    assert s.PROJECT_DESCRIPTION == "Desc"
    assert s.PROJECT_VERSION == "9.9.9"

    assert s.BACKEND_CORS_ORIGINS == [
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
    assert s.OLLAMA_HOST == "http://host:11434"
    assert s.MODEL_NAME == "m:1"
