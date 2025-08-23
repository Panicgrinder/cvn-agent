import unittest
from unittest.mock import patch
from typing import Any, Dict, cast

from app.api.models import ChatRequest
from app.api.chat import process_chat_request
from app.core.prompts import EVAL_SYSTEM_PROMPT

class TestEvalMode(unittest.IsolatedAsyncioTestCase):
    async def test_eval_mode_overrides_system_prompt(self):
        sent_payload: Dict[str, Any] = {}

        class ResponseStub:
            status_code = 200
            def raise_for_status(self):
                return None
            def json(self):
                return {"message": {"content": "OK"}}

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                return None
            async def post(self, url, json, headers=None):
                nonlocal sent_payload
                sent_payload = cast(Dict[str, Any], json)
                return ResponseStub()

        with patch("app.api.chat.httpx.AsyncClient", FakeClient):
            req = ChatRequest(messages=[{"role": "user", "content": "Erkläre DNS"}])
            await process_chat_request(req, eval_mode=True, unrestricted_mode=False)

        # In process_chat_request senden wir direkt an Ollama; eval_mode wird nicht im Payload transportiert,
        # aber die System-Nachricht muss überschrieben sein.
        assert isinstance(sent_payload.get("messages"), list)
        assert sent_payload["messages"][0]["role"] == "system"
        assert sent_payload["messages"][0]["content"].strip() == EVAL_SYSTEM_PROMPT.strip()
        assert sent_payload["messages"][-1]["content"].find("DNS") >= 0
