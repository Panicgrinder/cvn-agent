import os
import glob
import tempfile
from scripts import todo_gather as tg


def test_todo_gather_write_md():
    with tempfile.TemporaryDirectory() as tmp_root:
        results_dir = os.path.join(tmp_root, "eval", "results")
        summaries_dir = os.path.join(results_dir, "summaries")
        os.makedirs(results_dir, exist_ok=True)
        # Module-Globals patchen
        tg.PROJECT_ROOT = tmp_root
        tg.RESULTS_DIR = results_dir
        tg.SUMMARIES_DIR = summaries_dir
        # kleine Results-Datei anlegen (passt auf Pattern results_*.jsonl)
        sample = os.path.join(results_dir, "results_20250101_0000.jsonl")
        with open(sample, "w", encoding="utf-8") as f:
            f.write('{"id":"eval-001","success":true,"rpg_mode":false,"duration_ms": 10, "package":"p1"}\n')
            f.write('{"id":"eval-002","success":false,"rpg_mode":true,"duration_ms": 20, "package":"p1"}\n')

        # Act
        before = set(glob.glob(os.path.join(summaries_dir, "todo_status_*.md")))
        rc = tg.main(["--write-md"])
        after = set(glob.glob(os.path.join(summaries_dir, "todo_status_*.md")))

        # Assert
        assert rc == 0
        assert len(after) >= len(before)
        assert any(os.path.getsize(p) > 0 for p in after)
