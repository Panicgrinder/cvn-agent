import os
from typing import List

import pytest
from pathlib import Path

import scripts.map_reduce_summary_llm as mr


@pytest.mark.asyncio
async def test_process_scope_llm_uses_stub(tmp_path):
    # Arrange: create a small text file
    base = Path(mr.PROJECT_ROOT) / ".__tmp_tests__" / "llm"
    base.mkdir(parents=True, exist_ok=True)
    p: Path = base / "sample.md"
    p.write_text("Hello World", encoding="utf-8")

    called: List[str] = []

    async def fake_llm(client, api_url: str, path: str, run_id: str, max_chars: int, num_predict: int, temperature: float) -> str:
        called.append(path)
        # keep it simple to avoid cross-drive relpath issues
        return f"Datei: {os.path.basename(path)}\nZusammenfassung: OK"

    # Patch llm function
    orig = mr.llm_summarize_file
    mr.llm_summarize_file = fake_llm
    try:
        # Act: use use_llm=True, but with stubbed function, no network used
        res = await mr.process_scope(
            scope="tmp",
            scope_dir=str(base),
            use_llm=True,
            api_url="http://unused/chat",
            asgi=False,
            run_id="run1",
            max_files=0,
            max_chars=200,
            num_predict=128,
            temperature=0.1,
            concurrency=1,
        )
    finally:
        mr.llm_summarize_file = orig
        try:
            import shutil
            shutil.rmtree(base.parent)
        except Exception:
            pass

    # Assert
    assert len(res) == 1
    assert "Zusammenfassung: OK" in res[0]
    assert called and os.path.normcase(os.path.abspath(called[0])) == os.path.normcase(str(p.resolve()))


@pytest.mark.asyncio
async def test_process_scope_heuristic_minimal_fallback(tmp_path, monkeypatch):
    # Arrange: create a small text file
    base = Path(mr.PROJECT_ROOT) / ".__tmp_tests__" / "heur"
    base.mkdir(parents=True, exist_ok=True)
    p: Path = base / "a.txt"
    p.write_text("content", encoding="utf-8")

    # Force heuristic_summarize_file to None to hit minimal fallback
    # pyright: ignore[reportUnknownMemberType] - monkeypatch modifies attribute dynamically for tests
    monkeypatch.setattr(mr, "heuristic_summarize_file", None, raising=False)  # type: ignore[attr-defined]

    # Act
    res = await mr.process_scope(
        scope="tmp",
        scope_dir=str(base),
        use_llm=False,
        api_url="http://unused/chat",
        asgi=False,
        run_id="r",
        max_files=0,
        max_chars=50,
        num_predict=64,
        temperature=0.0,
        concurrency=1,
    )

    # Assert: minimal fallback includes file rel path and content
    assert len(res) == 1
    assert "Datei:" in res[0]
    assert "content" in res[0]
    try:
        import shutil
        shutil.rmtree(base.parent)
    except Exception:
        pass
