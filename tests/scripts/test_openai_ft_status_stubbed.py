from __future__ import annotations

import importlib
import io
import contextlib
import types
import pytest


class _Ev:
    def __init__(self, id: str, created_at: int, level: str, message: str) -> None:  # noqa: A002
        self.id = id
        self.created_at = created_at
        self.level = level
        self.message = message
    from typing import Dict, Any
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "level": self.level,
            "message": self.message,
        }


class _Job:
    def __init__(self, id: str, status: str, model: str = "gpt-4o", ftm: str | None = None) -> None:  # noqa: A002
        self.id = id
        self.status = status
        self.model = model
        self.fine_tuned_model = ftm
    from typing import Dict, Any
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "model": self.model,
            "fine_tuned_model": self.fine_tuned_model,
        }


class _Client:
    def __init__(self, jobs_seq: list[_Job], events_seq: list[list[_Ev]]) -> None:
        self._jobs_seq = jobs_seq
        self._events_seq = events_seq
        self._idx = 0
        self.fine_tuning = types.SimpleNamespace(
            jobs=types.SimpleNamespace(
                retrieve=self._retrieve,
                list_events=self._list_events,
            )
        )

    def _retrieve(self, job_id: str):  # noqa: ANN001
        return self._jobs_seq[min(self._idx, len(self._jobs_seq)-1)]

    def _list_events(self, job_id: str, limit: int = 25):  # noqa: ANN001
        evs = self._events_seq[min(self._idx, len(self._events_seq)-1)]
        self._idx = min(self._idx + 1, len(self._jobs_seq)-1)
        return types.SimpleNamespace(data=evs[:limit])


@pytest.mark.scripts
@pytest.mark.unit
def test_openai_ft_status_no_follow(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.import_module("scripts.openai_ft_status")
    monkeypatch.setenv("OPENAI_API_KEY", "x")

    # Snapshot mode: one job + events
    client = _Client(
        jobs_seq=[_Job("ftjob-1", "running")],
        events_seq=[[ _Ev("e1", 1, "info", "start"), _Ev("e2", 2, "warn", "warming up") ]],
    )

    # Patch OpenAI to return our client
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setattr(mod, "OpenAI", lambda api_key=None: client)  # type: ignore[no-any-return]

    buf = io.StringIO()
    import sys
    with contextlib.redirect_stdout(buf):
        # Simuliere CLI
        sys.argv = ["openai_ft_status.py", "ftjob-1", "--no-follow"]
        mod.main()
    out = buf.getvalue()
    assert "Job ftjob-1 status=running" in out
    assert "warming up" in out


@pytest.mark.scripts
@pytest.mark.unit
def test_openai_ft_status_follow_terminates(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.import_module("scripts.openai_ft_status")
    monkeypatch.setenv("OPENAI_API_KEY", "x")

    # Simuliere running -> succeeded mit zwei Polls
    jobs = [_Job("ftjob-2", "running"), _Job("ftjob-2", "succeeded", ftm="ft:gpt2")]  # noqa: PIE796
    events = [
        [ _Ev("e1", 1, "info", "start") ],
        [ _Ev("e2", 2, "info", "done") ],
    ]
    client = _Client(jobs, events)

    monkeypatch.setattr(mod, "OpenAI", lambda api_key=None: client)  # type: ignore[no-any-return]
    # Beschleunige die Schleife
    monkeypatch.setattr(mod, "time", types.SimpleNamespace(sleep=lambda x: None))

    buf = io.StringIO()
    import sys
    with contextlib.redirect_stdout(buf):
        sys.argv = ["openai_ft_status.py", "ftjob-2", "--interval", "1"]
        mod.main()
    out = buf.getvalue()
    assert "status=running" in out
    assert "status=succeeded" in out