import os
import tempfile
import sys
from scripts import open_latest_summary as ols


def test_open_latest_summary_print_only():
    with tempfile.TemporaryDirectory() as tmp:
        summaries = os.path.join(tmp, "eval", "results", "summaries")
        os.makedirs(summaries, exist_ok=True)
        sample = os.path.join(summaries, "summary_ALL_20250101_0000_MIXED.md")
        with open(sample, "w", encoding="utf-8") as f:
            f.write("# merged\n")

        # Rufe main mit --print auf (öffnet keine Datei)
        argv_backup = sys.argv[:]
        try:
            sys.argv = ["prog", "--print", "--dir", summaries]
            rc = ols.main()
        finally:
            sys.argv = argv_backup
        assert rc == 0
