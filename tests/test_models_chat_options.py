from __future__ import annotations

from typing import Any, Dict

from app.api.models import ChatOptions, ChatRequest


def test_chat_options_schema_accepts_and_dumps() -> None:
    opts = ChatOptions(
        host="http://localhost:11434",
        session_id="sid123",
        temperature=0.7,
        top_p=0.9,
        num_ctx=2048,
        stop=["\n\n", "<END>"]
    )
    req = ChatRequest(messages=[{"role": "user", "content": "hi"}], options=opts)
    dumped = req.model_dump()
    # options should be dumped as dict with expected keys
    assert isinstance(dumped.get("options"), dict)
    o: Dict[str, Any] = dumped["options"]
    assert o["session_id"] == "sid123"
    assert o["temperature"] == 0.7
    assert o["num_ctx"] == 2048
    assert o["stop"] == ["\n\n", "<END>"]


def test_chat_options_allows_dict_backcompat() -> None:
    opts: Dict[str, Any] = {"session_id": "s42", "temperature": 0.5}
    req = ChatRequest(messages=[{"role": "user", "content": "hi"}], options=opts)
    d = req.model_dump()
    assert d["options"]["session_id"] == "s42"
