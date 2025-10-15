from __future__ import annotations

import asyncio
import pytest
import app.api.chat as chat_module
from app.api.models import ChatRequest


@pytest.mark.streaming
@pytest.mark.api
def test_stream_chat_emits_error_and_done_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        status_code = 500
        def raise_for_status(self):
            raise RuntimeError("boom")
        async def aiter_lines(self):
            if False:
                yield ""

    class _CM:
        async def __aenter__(self):
            return _Resp()
        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Client:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        def stream(self, *args, **kwargs):
            return _CM()

    def _factory(*args: object, **kwargs: object) -> _Client:
        return _Client()
    monkeypatch.setattr(chat_module.httpx, "AsyncClient", _factory)
    req = ChatRequest(messages=[{"role": "user", "content": "hi"}])
    agen = asyncio.run(chat_module.stream_chat_request(req))

    events: list[str] = []
    async def _consume():
        async for s in agen:
            events.append(s)

    asyncio.run(_consume())

    assert any(e.startswith("event: error") for e in events)
    assert any(e.startswith("event: done") for e in events)
