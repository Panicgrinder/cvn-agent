import os
import time
import json
import tempfile
import unittest
from typing import Dict, Any

from scripts.run_eval import load_prompts

class TestEvalLoader(unittest.IsolatedAsyncioTestCase):
    async def test_newer_file_wins_on_same_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            f_old = os.path.join(tmp, "a.jsonl")
            f_new = os.path.join(tmp, "b.jsonl")

            rec_old: Dict[str, Any] = {"id": "eval-999", "prompt": "ALT", "must_include": ["alt"]}
            rec_new: Dict[str, Any] = {"id": "eval-999", "prompt": "NEU", "must_include": ["neu"]}

            with open(f_old, "w", encoding="utf-8") as f:
                f.write(json.dumps(rec_old, ensure_ascii=False) + "\n")
            # Stelle sicher, dass mtime unterschiedlich ist
            time.sleep(1.1)
            with open(f_new, "w", encoding="utf-8") as f:
                f.write(json.dumps(rec_new, ensure_ascii=False) + "\n")

            items = await load_prompts([os.path.join(tmp, "*.jsonl")])
            by_id = {i["id"]: i for i in items}
            assert "eval-999" in by_id
            assert by_id["eval-999"]["prompt"] == "NEU"
