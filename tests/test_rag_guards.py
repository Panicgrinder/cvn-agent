from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import pytest

import app.api.chat as chat_module
from app.api.models import ChatRequest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_stream_rag_guard_does_not_require_index(monkeypatch: pytest.MonkeyPatch) -> None:
    # RAG aktivieren und load_index -> None zurückgeben
    from app.core.settings import settings
    monkeypatch.setenv("RAG_ENABLED", "true")
    settings.RAG_ENABLED = True  # sicherstellen (ENV reload vermeiden)

    # load_index stubbt None, retrieve darf nicht abstürzen (wird aufgrund Guard nicht aufgerufen)
    import utils.rag as rag_mod
    monkeypatch.setattr(rag_mod, "load_index", lambda p: None)

    # Minimaler Request
    req = ChatRequest(messages=[{"role": "user", "content": "frage"}])

    # Aufruf sollte erfolgreich einen Async-Generator zurückgeben, ohne Netzwerk/Index
    agen = await chat_module.stream_chat_request(req)
    assert agen is not None


async def _call_stream(req: ChatRequest):
    # Nicht iterieren, da das die Netzwerkphase öffnet; RAG-Injektion geschieht davor
    return await chat_module.stream_chat_request(req)


def _fake_client_factory():
    class _Resp:
        status_code = 200

        def json(self) -> Dict[str, Any]:
            return {"message": {"content": "ok"}}

        def raise_for_status(self) -> None:
            return

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url: str, json: Dict[str, Any], headers: Dict[str, str]):
            return _Resp()

    return _Client


@pytest.mark.unit
@pytest.mark.api
@pytest.mark.asyncio
async def test_nonstream_rag_guard_does_not_require_index(monkeypatch: pytest.MonkeyPatch) -> None:
    # RAG aktivieren und load_index -> None zurückgeben
    from app.core.settings import settings
    monkeypatch.setenv("RAG_ENABLED", "true")
    settings.RAG_ENABLED = True

    import utils.rag as rag_mod
    monkeypatch.setattr(rag_mod, "load_index", lambda p: None)

    # httpx AsyncClient stubben, damit kein Netzwerk erfolgt
    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _fake_client_factory()())

    req = ChatRequest(messages=[{"role": "user", "content": "frage"}])
    # Sollte ohne Exception durchlaufen, obwohl kein RAG-Index existiert
    resp = await chat_module.process_chat_request(req)
    assert isinstance(resp.content, str)