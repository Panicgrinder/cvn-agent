from __future__ import annotations

import importlib
import asyncio
from pathlib import Path
import json
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_openai_chat_include_failures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.export_finetune")

    # Results with one success and one failure
    res_file = tmp_path / "results_aa.jsonl"
    res_file.write_text("\n".join([
        json.dumps({"item_id": "eval-1", "success": True, "response": "ok", "source_file": "d.jsonl"}),
        json.dumps({"item_id": "eval-2", "success": False, "response": "bad", "failed_checks": ["x"], "source_file": "d.jsonl"}),
    ]), encoding="utf-8")

    class _Item:
        def __init__(self, id_: str) -> None:
            self.id = id_
            self.source_package = "pack"
            self.messages = [
                {"role": "system", "content": "rules"},
                {"role": "user", "content": f"question for {id_}"},
            ]

    from typing import Any, List
    async def _load_items(_patterns: Any = None) -> List[_Item]:
        return [_Item("eval-1"), _Item("eval-2")]

    monkeypatch.setattr(mod.run_eval, "load_evaluation_items", _load_items)
    monkeypatch.setattr(mod.run_eval, "DEFAULT_DATASET_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(mod.run_eval, "DEFAULT_EVAL_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(mod.run_eval, "DEFAULT_FILE_PATTERN", "*.jsonl", raising=False)

    out = asyncio.run(mod.export_from_results(str(res_file), out_dir=str(tmp_path), format="openai_chat", include_failures=True))
    assert out["ok"] is True and out["count"] == 2
    # read the written file
    p = Path(out["out"]).read_text(encoding="utf-8").splitlines()
    recs = [json.loads(ln) for ln in p if ln.strip()]
    assert len(recs) == 2
    # assistant message appended at the end
    for rec in recs:
        msgs = rec["messages"]
        assert msgs[-1]["role"] == "assistant"