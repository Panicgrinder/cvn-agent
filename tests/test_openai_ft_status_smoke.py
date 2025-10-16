from __future__ import annotations

import os
import sys
import types
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_openai_ft_status_cli_parsing_and_key_check(monkeypatch: "pytest.MonkeyPatch") -> None:
    # Stelle sicher, dass kein API-Key gesetzt ist
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from scripts import openai_ft_status as s
    # Setze Dummy-API-Key und stubbe Client/Funktionen, damit kein Netzaufruf erfolgt
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    class _DummyClient:
        class _FT:
            class _Jobs:
                def retrieve(self, job_id: str):
                    return {"id": job_id, "status": "succeeded", "fine_tuned_model": "ft-model"}
                def list_events(self, job_id: str, limit: int = 25):
                    return types.SimpleNamespace(data=[{"id": "e1", "created_at": 1, "level": "info", "message": "done"}])
            jobs = _Jobs()
        fine_tuning = _FT()
    class _DummyOpenAI:
        def __init__(self, api_key=None):
            self._client = _DummyClient()
            # Proxy-Attribute
            self.fine_tuning = self._client.fine_tuning
    monkeypatch.setattr(s, "OpenAI", _DummyOpenAI)
    # Simuliere CLI-Args für eine Momentaufnahme ohne Follow
    old_argv = sys.argv[:]
    sys.argv = ["openai_ft_status.py", "ftjob-123", "--no-follow"]
    try:
        # Sollte nun ohne Ausnahme durchlaufen und Snapshot drucken
        s.main()
    finally:
        sys.argv = old_argv
