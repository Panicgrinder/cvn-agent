from __future__ import annotations

import os
import json
from typing import List, Dict, Any

import pytest


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


@pytest.mark.scripts
@pytest.mark.unit
def test_rerun_failed_handles_eval_prefix_normalization(tmp_path: "os.PathLike[str]") -> None:
    # Arrange: künstliche Verzeichnisstruktur
    proj = tmp_path
    datasets_dir = os.path.join(proj, "eval", "datasets")
    results_dir = os.path.join(proj, "eval", "results")
    os.makedirs(datasets_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    # Dataset enthält IDs einmal mit eval- Präfix und einmal ohne
    ds_file = os.path.join(datasets_dir, "eval-00.jsonl")
    _write_jsonl(ds_file, [
        {"id": "eval-item-1", "messages": [{"role": "user", "content": "Sag hallo"}]},
        {"id": "item-2", "messages": [{"role": "user", "content": "Sag tschuess"}]},
    ])

    # Results enthält fehlgeschlagene Einträge mit gemischten Varianten
    res_file = os.path.join(results_dir, "results_20250101_1200.jsonl")
    _write_jsonl(res_file, [
        {"_meta": True},
        {"item_id": "item-1", "success": False},         # sollte auf eval-item-1 matchen
        {"item_id": "eval-item-2", "success": False},     # sollte auf item-2 matchen
    ])

    # Monkeypatch Konstanten im rerun_failed-Modul auf tmp-Verzeichnisse
    from scripts import rerun_failed as rf
    rf.DATASETS_DIR = datasets_dir
    rf.RESULTS_DIR = results_dir
    rf.TMP_DIR = os.path.join(results_dir, "tmp")

    # Act
    rc = rf.main()

    # Assert
    assert rc == 0
    # Finde erzeugte ReRun-Datei
    out_tmp_dir = rf.TMP_DIR
    outs = [os.path.join(out_tmp_dir, f) for f in os.listdir(out_tmp_dir) if f.endswith('.jsonl')]
    assert len(outs) == 1
    out_path = outs[0]
    with open(out_path, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    # beide Items sollten enthalten sein, unabhängig von eval- Präfix in results/dataset
    ids = {r.get("id") for r in lines}
    assert ids == {"eval-item-1", "item-2"}
