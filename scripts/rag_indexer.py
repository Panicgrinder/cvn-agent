from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from utils.rag import build_index, save_index


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Baue einen einfachen TF-IDF RAG-Index über .md/.txt Dateien")
    p.add_argument("--input", nargs="+", help="Dateien oder Verzeichnisse (.md/.txt)")
    p.add_argument("--out", default=str(Path("eval/results/rag/index.json")), help="Pfad zur Indexdatei (JSON)")
    args = p.parse_args(argv)

    if not args.input:
        print("Keine Eingabe angegeben. Beispiel: --input docs eval/config")
        return 2

    idx = build_index(args.input)
    save_index(idx, args.out)
    print(f"Index erstellt: {args.out} (Dokumente: {idx.n_docs}, Vokabeln: {len(idx.df)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
