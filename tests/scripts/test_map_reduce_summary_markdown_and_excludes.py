from __future__ import annotations

import os
import importlib
import json
import io
import contextlib
from pathlib import Path
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_summarize_markdown_and_merge(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.map_reduce_summary")

    docs: Path = tmp_path / "docs"
    docs.mkdir()
    md1: Path = docs / "A.md"
    md1.write_text("""
# Titel A

Einleitungstext.

## Abschnitt 1
- Punkt 1
- Punkt 2
""".strip(), encoding="utf-8")

    md2: Path = docs / "B.md"
    md2.write_text("""
# Titel B

Text.

### Unterpunkt
Weitere Details.
""".strip(), encoding="utf-8")

    out_dir: Path = tmp_path / "out"
    out_dir.mkdir()

    # Temporär eigenen Scope injizieren
    monkeypatch.setitem(mod.SCOPES, "TMPDOCS", str(docs))

    # run summarization for markdown scope
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.main([
            "--scopes", "TMPDOCS",
            "--out-dir", str(out_dir),
            "--max-files", "10",
        ])

    assert rc == 0
    data = json.loads(buf.getvalue())
    merged_path = data["merged"]
    merged = Path(merged_path).read_text(encoding="utf-8")
    # Should contain synthesized headings from both files or filenames as fallback
    assert ("Titel A" in merged) or ("A.md" in merged)
    assert ("Titel B" in merged) or ("B.md" in merged)


@pytest.mark.scripts
@pytest.mark.unit
def test_walk_scope_excludes_dirs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.map_reduce_summary")

    root: Path = tmp_path / "root"
    root.mkdir()
    included: Path = root / "keep"
    included.mkdir()
    excluded: Path = root / "node_modules"
    excluded.mkdir()

    (included / "file.txt").write_text("some content", encoding="utf-8")
    (excluded / "secret.txt").write_text("should be ignored", encoding="utf-8")

    out_dir: Path = tmp_path / "out2"
    out_dir.mkdir()

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        # Temporär Scope injizieren; node_modules ist per Default ausgeschlossen
        monkeypatch.setitem(mod.SCOPES, "TMPROOT", str(root))
        rc = mod.main([
            "--scopes", "TMPROOT",
            "--out-dir", str(out_dir),
            "--max-files", "50",
        ])

    assert rc == 0
    data = json.loads(buf.getvalue())
    merged_path = data["merged"]
    merged = Path(merged_path).read_text(encoding="utf-8")
    assert "some content" in merged
    assert "should be ignored" not in merged
