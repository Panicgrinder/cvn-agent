from __future__ import annotations

import os
import json
from typing import Any, Dict, List

import pytest

from scripts.prepare_finetune_pack import prepare_pack


def _mk_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


@pytest.mark.scripts
@pytest.mark.unit
def test_prepare_pack_no_dedupe_counts(tmp_path: "os.PathLike[str]") -> None:
    src = os.path.join(tmp_path, "src.jsonl")
    rows = [
        {"messages": [{"role": "user", "content": "A"}, {"role": "assistant", "content": "Antwort eins"}]},
        {"messages": [{"role": "user", "content": "A"}, {"role": "assistant", "content": "Antwort zwei"}]},
    ]
    _mk_jsonl(src, rows)

    res = prepare_pack(src, out_dir=str(tmp_path), format="openai_chat", train_ratio=0.5, seed=1, min_output_chars=1, dedupe_by_instruction=False)
    assert res.get("ok")
    counts = res.get("counts", {})
    assert counts.get("total") == 2
    assert os.path.exists(str(res.get("train")))
    assert os.path.exists(str(res.get("val")))
