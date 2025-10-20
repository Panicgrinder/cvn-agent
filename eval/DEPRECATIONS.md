# Deprecations (Eval)

- Datei `eval/eval-21-40_demo_v1.0.json` war ein Duplikat der Version unter `eval/datasets/` und wurde durch `eval/eval-21-40_fantasy_v1.0.*` ersetzt; Top‑Level‑Duplikate werden via Cleanup entfernt.
- Historische Pfade/Generatoren können zeitweise `eval/*.jsonl` erzeugen. Ergebnisse liegen dauerhaft unter `eval/results/` (gitignored).
