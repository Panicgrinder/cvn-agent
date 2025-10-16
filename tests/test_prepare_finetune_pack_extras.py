from __future__ import annotations

import os
import json
from typing import Any, Dict, List

import pytest

from scripts.prepare_finetune_pack import prepare_pack, _write_jsonl


def _mk_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


@pytest.mark.scripts
@pytest.mark.unit
def test_prepare_pack_dedupe_and_min_output(tmp_path: "os.PathLike[str]") -> None:
    src = os.path.join(tmp_path, "src.jsonl")
    rows = [
        {"messages": [{"role": "user", "content": "A"}, {"role": "assistant", "content": "Antwort eins"}]},
        {"messages": [{"role": "user", "content": "A"}, {"role": "assistant", "content": "Antwort zwei"}]},
        {"messages": [{"role": "user", "content": "B"}, {"role": "assistant", "content": "Kurz"}]},
    ]
    _mk_jsonl(src, rows)

    res = prepare_pack(src, out_dir=str(tmp_path), format="openai_chat", train_ratio=0.5, seed=1, min_output_chars=6)
    assert res.get("ok")
    counts = res.get("counts", {})
    # Dedupe entfernt doppelte Instruction "A", kurze Antwort "Kurz" wird gefiltert -> 1 verbleibender Eintrag
    assert counts.get("total") == 1
    assert os.path.exists(str(res.get("train")))
    assert os.path.exists(str(res.get("val")))
    # Bei train_ratio=0.5 ist der Split deterministisch: 0/1 oder 1/0, hier 0 train, 1 val
    assert counts.get("train") in (0, 1)
    assert counts.get("val") in (0, 1)


@pytest.mark.scripts
@pytest.mark.unit
def test_prepare_pack_empty_or_all_filtered(tmp_path: "os.PathLike[str]") -> None:
    src = os.path.join(tmp_path, "empty.jsonl")
    # Leere Datei
    with open(src, "w", encoding="utf-8") as f:
        f.write("")
    res = prepare_pack(src, out_dir=str(tmp_path), format="openai_chat")
    assert not res.get("ok") and "Leere" in str(res.get("error"))

    # Datei mit nur zu kurzen Outputs
    src2 = os.path.join(tmp_path, "short.jsonl")
    rows = [
        {"messages": [{"role": "user", "content": "A"}, {"role": "assistant", "content": "x"}]},
    ]
    _mk_jsonl(src2, rows)
    res2 = prepare_pack(src2, out_dir=str(tmp_path), format="openai_chat", min_output_chars=5)
    assert not res2.get("ok") and "gefiltert" in str(res2.get("error"))
