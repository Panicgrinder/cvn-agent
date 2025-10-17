from __future__ import annotations

import os
import json
from typing import Any, Dict, List

import pytest

from scripts.prepare_finetune_pack import prepare_pack


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


@pytest.mark.scripts
@pytest.mark.unit
def test_prepare_pack_alpaca_empty_outputs_filtered(tmp_path: "os.PathLike[str]") -> None:
    src = os.path.join(tmp_path, "alpaca.jsonl")
    rows = [
        {"instruction": "Erkläre X", "input": "", "output": ""},
        {"instruction": "Erkläre Y", "input": "", "output": "Kurz"},
        {"instruction": "Erkläre Z", "input": "", "output": "Dies ist genügend lang"},
    ]
    _write_jsonl(src, rows)
    res = prepare_pack(src, out_dir=str(tmp_path), format="alpaca", train_ratio=1.0, min_output_chars=10)
    # Nur der dritte Eintrag bleibt
    assert res.get("ok") is True
    assert res["counts"]["total"] == 1


@pytest.mark.scripts
@pytest.mark.unit
def test_prepare_pack_alpaca_near_dup_threshold_extremes(tmp_path: "os.PathLike[str]") -> None:
    src = os.path.join(tmp_path, "alpaca_dup.jsonl")
    rows = [
        {"instruction": "Sag bitte Hallo", "input": "", "output": "Hallo!"},
        {"instruction": "Sage bitte Hallo", "input": "", "output": "Hallo!"},
        {"instruction": "Erkläre die Sonne", "input": "", "output": "Die Sonne ist ein Stern."},
    ]
    _write_jsonl(src, rows)

    # near_dup_threshold=0.0 (aus): es findet keine Near-Dedupe statt → 3 total
    r0 = prepare_pack(src, out_dir=str(tmp_path), format="alpaca", train_ratio=1.0, min_output_chars=0, near_dup_threshold=0.0)
    assert r0.get("ok")
    assert r0["counts"]["total"] == 3

    # near_dup_threshold sehr niedrig -> sollte Duplikate aggressiv entfernen → 2 total
    r1 = prepare_pack(src, out_dir=str(tmp_path), format="alpaca", train_ratio=1.0, min_output_chars=0, near_dup_threshold=0.2)
    assert r1.get("ok")
    assert r1["counts"]["total"] == 2

    # near_dup_threshold=1.0 -> nur exakt identische Token-Sets wären Dups; hier bleiben 3
    r2 = prepare_pack(src, out_dir=str(tmp_path), format="alpaca", train_ratio=1.0, min_output_chars=0, near_dup_threshold=1.0)
    assert r2.get("ok")
    assert r2["counts"]["total"] == 3
