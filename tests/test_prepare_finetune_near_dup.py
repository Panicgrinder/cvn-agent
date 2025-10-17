from __future__ import annotations
from typing import Any, Dict, List
import json
import os

from scripts.prepare_finetune_pack import prepare_pack


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def test_near_duplicate_threshold_filters(tmp_path: "Any") -> None:
    # openai_chat Format: erste user-Nachricht ist Instruction
    rows = [
        {"messages": [{"role": "user", "content": "Sag bitte Hallo"}, {"role": "assistant", "content": "Hallo!"}]},
        {"messages": [{"role": "user", "content": "Sage bitte Hallo"}, {"role": "assistant", "content": "Hallo!"}]},
        {"messages": [{"role": "user", "content": "Erkläre die Sonne"}, {"role": "assistant", "content": "Die Sonne ist..."}]},
    ]
    src = os.path.join(str(tmp_path), "src.jsonl")
    _write_jsonl(src, rows)
    # Hohe Schwelle 0.9: "Sag Hallo" vs "Sage Hallo" sind ähnlich, aber nicht zu 90% identisch → beide bleiben
    res1 = prepare_pack(src, out_dir=str(tmp_path), format="openai_chat", train_ratio=1.0, min_output_chars=0, near_dup_threshold=0.9)
    assert res1.get("ok") is True
    counts1 = res1["counts"]["total"]
    assert counts1 == 3

    # Mittlere Schwelle 0.5: die beiden Hallo-Varianten sollten als Near-Dupe zusammenfallen → nur 2 unikate
    res2 = prepare_pack(src, out_dir=str(tmp_path), format="openai_chat", train_ratio=1.0, min_output_chars=0, near_dup_threshold=0.5)
    assert res2.get("ok") is True
    counts2 = res2["counts"]["total"]
    assert counts2 == 2
