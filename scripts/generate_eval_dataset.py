#!/usr/bin/env python
"""
Generate a JSONL evaluation dataset with synthetic prompts.

Usage:
  python scripts/generate_eval_dataset.py --start 101 --count 200 --out eval/datasets/eval-101-300_generated_v1.0.jsonl

Each item has schema:
  {"id": "eval-<n>", "messages": [{"role":"user","content": "..."}], "checks": {"must_include": ["..."]}}
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Dict

TOPIC_TEMPLATES: List[str] = [
    "Fasse sachlich zusammen: {subject}",
    "Nenne kurz drei Aspekte zu: {subject}",
    "Erkläre neutral in einem Satz: {subject}",
    "Gib einen praktischen Tipp zu: {subject}",
    "Formuliere höflich und knapp: {subject}",
]

SUBJECTS: List[str] = [
    "Zeitmanagement",
    "Teamkommunikation",
    "Fehlersuche im Code",
    "Versionskontrolle (Git)",
    "Tests schreiben (pytest)",
    "Typprüfung (mypy, pyright)",
    "Dokumentation kurz halten",
    "Prioritäten setzen",
    "Lernen und Üben",
    "Projektplanung",
    "Requirements klären",
    "Zieldefinition",
    "Feedback einholen",
    "Konflikte sachlich lösen",
    "Release-Checkliste",
    "Lesbarer Code",
    "Refactoring klein starten",
    "Review-Kriterien",
    "CI-Status prüfen",
    "Logs interpretieren",
]

# Words we often want included to exercise term_inclusion
INCLUDE_WORDS: List[List[str]] = [
    ["freundlich", "klar"],
    ["neutral", "sachlich"],
    ["kurz", "präzise"],
    ["Hinweis", "Beispiel"],
    ["Schritt", "Ziel"],
    ["Plan", "Priorität"],
    ["Übung", "Feedback"],
    ["Empathie", "nachfragen"],
    ["aufmuntern", "unterstützen"],
    ["Risik", "Abwägung"],
]


def make_item(num: int, tpl_idx: int, subj_idx: int) -> Dict[str, object]:
    tpl = TOPIC_TEMPLATES[tpl_idx % len(TOPIC_TEMPLATES)]
    subj = SUBJECTS[subj_idx % len(SUBJECTS)]
    prompt = tpl.format(subject=subj)
    inc = INCLUDE_WORDS[(num + tpl_idx + subj_idx) % len(INCLUDE_WORDS)]
    return {
        "id": f"eval-{num:03d}",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "checks": {
            "must_include": inc
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()

    start = args.start
    count = args.count
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    items: List[Dict[str, object]] = []
    for i in range(count):
        n = start + i
        items.append(make_item(n, i, n))

    with open(out_path, "w", encoding="utf-8") as f:
        for obj in items:
            # write as JSONL without importing json to keep it simple
            import json as _json
            f.write(_json.dumps(obj, ensure_ascii=False) + "\n")

    print(f"Wrote {len(items)} items to {out_path}")


if __name__ == "__main__":
    main()
