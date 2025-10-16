from __future__ import annotations

import asyncio
import importlib
from typing import Any, Dict

import pytest


@pytest.mark.unit
@pytest.mark.parametrize(
    "eval_mode,unrestricted_mode,expected_temp_max",
    [
        (False, False, 1.0),
        (True, False, 0.25),
        (False, True, 1.0),
    ],
)
def test_prompt_selection_non_stream(eval_mode: bool, unrestricted_mode: bool, expected_temp_max: float, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.chat import process_chat_request
    from app.api.models import ChatRequest
    import httpx

    # Fake httpx client, der eine einfache Antwort zurückgibt
    class _Resp:
        status_code = 200
        def json(self) -> Dict[str, Any]:
            return {"message": {"content": "ok"}}
        def raise_for_status(self) -> None:
            return

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self
        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False
        async def post(self, url: str, json: Dict[str, Any], headers: Dict[str, str]) -> _Resp:
            # Erster Eintrag sollte system sein und Temperatur-Regel gilt
            assert json["messages"][0]["role"] == "system"
            temp = float(json.get("options", {}).get("temperature", 0.0))
            assert temp <= expected_temp_max + 1e-9
            return _Resp()

    # Monkeypatch AsyncClient, sodass process_chat_request unseren Client nutzt
    def _factory(*args: Any, **kwargs: Any) -> Any:
        return _Client()
    monkeypatch.setattr(httpx, "AsyncClient", _factory)

    req = ChatRequest(messages=[{"role": "user", "content": "hi"}])
    res = asyncio.run(process_chat_request(req, eval_mode=eval_mode, unrestricted_mode=unrestricted_mode))
    assert res.content == "ok"


@pytest.mark.unit
def test_options_parsing_num_predict_and_top_p(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.chat import process_chat_request
    from app.api.models import ChatRequest
    import httpx

    captured: Dict[str, Any] = {}

    class _Resp:
        status_code = 200
        def json(self) -> Dict[str, Any]:
            return {"message": {"content": "ok"}}
        def raise_for_status(self) -> None:
            return

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self
        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False
        async def post(self, url: str, json: Dict[str, Any], headers: Dict[str, str]) -> _Resp:
            captured.update(json.get("options", {}))
            return _Resp()

    def _factory(*args: Any, **kwargs: Any) -> Any:
        return _Client()
    monkeypatch.setattr(httpx, "AsyncClient", _factory)

    # num_predict über max_tokens und top_p als String, der floatbar ist
    req = ChatRequest(messages=[{"role": "user", "content": "hi"}], options={"max_tokens": 999999, "top_p": "0.7", "temperature": 0.9})
    res = asyncio.run(process_chat_request(req))
    assert res.content == "ok"
    # Sollte auf REQUEST_MAX_TOKENS gekappt werden und top_p als float übernommen
    assert isinstance(captured.get("num_predict"), int)
    from app.core.settings import settings
    assert 1 <= captured["num_predict"] <= settings.REQUEST_MAX_TOKENS
    assert abs(float(captured.get("top_p", 0.0)) - 0.7) < 1e-6


@pytest.mark.unit
def test_context_notes_injection(tmp_path: "Any", monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.chat import process_chat_request
    from app.api.models import ChatRequest
    import httpx
    import app.api.chat as chat_module

    notes_file = tmp_path / "ctx.md"
    notes_file.write_text("Kontext123", encoding="utf-8")

    # Kontext-Notizen direkt aktivieren und Laden stubben
    monkeypatch.setattr(chat_module.settings, "CONTEXT_NOTES_ENABLED", True, raising=False)
    from typing import Iterable
    def _stub_load(paths: Iterable[str], max_chars: int = 4000) -> str:
        return notes_file.read_text(encoding="utf-8")
    monkeypatch.setattr(chat_module, "load_context_notes", _stub_load)

    class _Resp:
        status_code = 200
        def json(self) -> Dict[str, Any]:
            return {"message": {"content": "ok"}}
        def raise_for_status(self) -> None:
            return

    captured: Dict[str, Any] = {}

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self
        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False
        async def post(self, url: str, json: Dict[str, Any], headers: Dict[str, str]) -> _Resp:
            captured["payload"] = json
            return _Resp()

    def _factory(*args: Any, **kwargs: Any) -> Any:
        return _Client()
    monkeypatch.setattr(httpx, "AsyncClient", _factory)

    req = ChatRequest(messages=[{"role": "user", "content": "hi"}])
    res = asyncio.run(process_chat_request(req))
    assert res.content == "ok"
    msgs = captured.get("payload", {}).get("messages", [])
    assert "Kontext123" in msgs[1]["content"]
