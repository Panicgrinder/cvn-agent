# Evaluierungswerkzeug für CVN Agent

Dieses Verzeichnis enthält Tools und Daten zur Evaluierung des CVN Agents.

Struktur:

- `datasets/`: Eingabedateien für die Evaluierung (Prompts), z. B. `eval-*.json` oder `.jsonl`
- `config/`: Konfiguration (z. B. `synonyms.json` für Keyword-Prüfungen)
- `results/`: Ausgabedateien der Evaluierung (generiert, `results_*.jsonl`)

Hinweis: Private, lokale Synonyme können in `config/synonyms.local.json` gepflegt werden (git-ignoriert). Diese werden automatisch mit `config/synonyms.json` gemerged. Eine Vorlage liegt als `config/synonyms.local.sample.json` bei.

## Format der Datasets (JSON/JSONL)

```json
{
  "id": "eval-001",
  "messages": [
    {"role": "user", "content": "Stelle dich kurz vor."}
  ],
  "checks": {
    "must_include": ["Begriff1", "Begriff2", "Begriff3"]
  }
}
```

- `id`: Eindeutige ID des Testfalls
- `messages`: Liste von Nachrichten, die an den Chat-Endpunkt gesendet werden
- `checks`: Prüfbedingungen für die Antwort
  - `must_include`: Liste von Begriffen, die in der Antwort enthalten sein müssen