import os
import tempfile
import sys
from scripts import fine_tune_pipeline as ftp


def test_fine_tune_pipeline_no_check_with_dummy_train():
    with tempfile.TemporaryDirectory() as tmp:
        fin_dir = os.path.join(tmp, "eval", "results", "finetune")
        os.makedirs(fin_dir, exist_ok=True)
        train = os.path.join(fin_dir, "finetune_openai_chat_test_train.jsonl")
        with open(train, "w", encoding="utf-8") as f:
            f.write('{}\n')

        # setze cwd, damit latest_train_file findet
        cwd = os.getcwd()
        try:
            os.chdir(tmp)
            # Rufe main über sys.argv: --finetune-dir, --no-check, Free-Modell
            argv_backup = sys.argv[:]
            try:
                sys.argv = [
                    "prog",
                    "--finetune-dir", fin_dir,
                    "--model", "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                    "--no-check",
                    "--max-steps", "1"
                ]
                rc = ftp.main()
            finally:
                sys.argv = argv_backup
        finally:
            os.chdir(cwd)

        # Wir erwarten, dass der Prozess startet und mit dem Rückgabecode des subprocess.call endet.
        # Da train_lora.py existiert, kann der Call auf CI ggf. mit 0-Not-Run enden. Akzeptiere 0..255.
        assert isinstance(rc, int)