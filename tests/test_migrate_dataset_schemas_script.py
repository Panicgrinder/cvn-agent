from __future__ import annotations

import os
import json
from typing import Any, Dict, List

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_migrate_dataset_schemas_happy_path(tmp_path: "os.PathLike[str]") -> None:
    # Simuliertes Projekt mit eval/datasets
    project_root = tmp_path
    eval_dir = os.path.join(project_root, "eval", "datasets")
    os.makedirs(eval_dir, exist_ok=True)
    src = os.path.join(eval_dir, "eval-21-40_fantasy_v1.0.json")

    # JSON-Array mit prompt und must_include
    data: List[Dict[str, Any]] = [
        {"id": "demo-1", "prompt": "Sag Hallo", "must_include": ["Hallo"]},
        {"id": "demo-2", "messages": [{"role": "user", "content": "Schon gut"}], "checks": {"must_include": ["gut"]}},
    ]
    with open(src, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    # Modul importieren und CWD auf Projektwurzel setzen
    import scripts.migrate_dataset_schemas as mod
    cwd_before = os.getcwd()
    os.chdir(project_root)
    try:
        ok = mod.migrate_demo_dataset()
        assert ok is True

        # Zieldatei ist jetzt JSONL mit migrierten Feldern
        with open(src, "r", encoding="utf-8") as f:
            lines = [json.loads(l) for l in f.read().splitlines() if l.strip()]
        assert isinstance(lines, list) and len(lines) == 2
        # Erster Eintrag migriert prompt->messages und must_include->checks.must_include
        first = lines[0]
        assert "prompt" not in first and "messages" in first
        assert "must_include" not in first and "checks" in first and "must_include" in first["checks"]
    finally:
        os.chdir(cwd_before)
