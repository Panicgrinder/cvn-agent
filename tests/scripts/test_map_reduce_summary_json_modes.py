from __future__ import annotations

import os
import json
import importlib

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_summarize_json_and_jsonl(tmp_path: "os.PathLike[str]") -> None:
    mod = importlib.import_module("scripts.map_reduce_summary")

    # JSON
    p_json = os.path.join(tmp_path, "a.json")
    with open(p_json, "w", encoding="utf-8") as f:
        json.dump({"x": 1, "y": [1,2,3]}, f)
    out1 = mod.summarize_file(p_json)
    assert "JSON-Objekt" in out1 or "Top-Level-Felder" in out1

    # JSONL
    p_jsonl = os.path.join(tmp_path, "b.jsonl")
    with open(p_jsonl, "w", encoding="utf-8") as f:
        f.write(json.dumps({"id": 1, "a": 1}) + "\n")
        f.write(json.dumps({"id": 2, "b": 2}) + "\n")
        f.write(json.dumps({"id": 3, "a": 3, "b": 4}) + "\n")
    out2 = mod.summarize_file(p_jsonl)
    assert "JSONL" in out2 and ("Felder" in out2 or "Beispiel" in out2)
