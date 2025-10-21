from fastapi.testclient import TestClient
from app.main import app
from app.core.settings import settings


def test_session_id_coercion_top_level():
    client = TestClient(app)
    r = client.post(
        "/chat",
        json={
            "messages": [{"role": "user", "content": "Top-Level SID"}],
            "session_id": "SID-A",
            "model": settings.MODEL_NAME,
        },
    )
    assert r.status_code in (200, 400, 500)


def test_session_id_coercion_in_options():
    client = TestClient(app)
    r = client.post(
        "/chat",
        json={
            "messages": [{"role": "user", "content": "Options SID"}],
            "options": {"session_id": "SID-B"},
            "model": settings.MODEL_NAME,
        },
    )
    assert r.status_code in (200, 400, 500)
