# Overnight Evaluation (Teilrun – 50 Einträge)

- Tag: overnight-20251022
- Modus: ASGI (in-process)
- Ergebnisse: eval/results/results_20251022_0042_overnight-20251022.jsonl
- Zeit: 2025-10-22 00:42–00:48

## Zusammenfassung

- Erfolgreich: 2/50 (4.0%)
- RPG-Stil erkannt: 48/50 (96.0%)
- Durchschnittliche Dauer: 7022 ms

Top-Fehlschlagursachen

- rpg_style: 48
- term_inclusion: 24 (häufig fehlend: freundlich, abenteuer, empathisch, nachfrage, aufmuntern)

Pakete

- chai-ai_small_v1: 0/15 (∅ 5487 ms)
- combined_eval_001-100: 2/35 (∅ 7681 ms)

Hinweise

- Viele Antworten im RPG-Stil; die Checks erwarteten häufig neutral/allgemein.
	Für bessere Scores im Eval-Modus den Systemprompt explizit auf Evaluations-Style trimmen,
	oder Checks/Datensätze anpassen.
- Vollständiger Overnight-Run kann mit höherem Limit oder ohne `--limit` erfolgen.

Letzte Aktualisierung: 2025-10-22
