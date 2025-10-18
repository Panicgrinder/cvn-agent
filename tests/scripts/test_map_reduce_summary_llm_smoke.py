import os
import asyncio
import tempfile
from scripts import map_reduce_summary_llm as mrl


def test_map_reduce_summary_llm_heuristic_only():
    with tempfile.TemporaryDirectory() as tmp_root:
        ds_dir = os.path.join(tmp_root, "eval", "datasets")
        out_dir = os.path.join(tmp_root, "eval", "results", "summaries")
        os.makedirs(ds_dir, exist_ok=True)
        sample = os.path.join(ds_dir, "heuristic_sample.md")
        with open(sample, "w", encoding="utf-8") as f:
            f.write("# Sample\n\nDies ist eine Testdatei für die Heuristik.")

        # SCOPES temporär überschreiben (nur eval-datasets zeigt auf tmp)
        old_scopes = dict(mrl.SCOPES)
        try:
            mrl.SCOPES = {**mrl.SCOPES, "eval-datasets": ds_dir}
            rc = asyncio.run(mrl.amain([
                "--llm-scopes", "",
                "--heuristic-scopes", "eval-datasets",
                "--out-dir", out_dir,
                "--max-files", "1",
                "--max-chars", "200"
            ]))
        finally:
            mrl.SCOPES = old_scopes

        assert rc == 0
        files = [fn for fn in os.listdir(out_dir) if fn.startswith("summary_ALL_") and fn.endswith("_MIXED.md")]
        assert files, "Erwartete gemergte Summary-Datei fehlt"
