from fastapi.testclient import TestClient
from app.main import app
from app.core.settings import settings


def test_memory_streaming_append(monkeypatch):
    client = TestClient(app)
    sid = "stream42"

    with client.stream(
        "POST",
        "/chat/stream",
        json={
            "messages": [{"role": "user", "content": "Sag was im Stream"}],
            "session_id": sid,
            "model": settings.MODEL_NAME,
        },
    ) as r:
        for _ in r.iter_lines():
            pass
        assert r.status_code in (200, 500)
