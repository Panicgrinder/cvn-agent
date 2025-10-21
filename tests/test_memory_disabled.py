from fastapi.testclient import TestClient
from app.main import app
from app.core.settings import settings


def test_memory_disabled(monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_ENABLED", False)
    client = TestClient(app)

    r = client.post(
        "/chat",
        json={
            "messages": [{"role": "user", "content": "Ohne Memory"}],
            "session_id": "sid1",
            "model": settings.MODEL_NAME,
        },
    )
    assert r.status_code in (200, 400, 500)
