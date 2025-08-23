# Evaluierungswerkzeug für CVN Agent

Dieses Verzeichnis enthält Tools zur Evaluierung des CVN Agents.

## Dateien

- `prompts.jsonl`: Eine JSONL-Datei mit Testfällen für die Evaluierung
- Jeder Eintrag enthält eine ID, eine Liste von Nachrichten und Prüfbedingungen

## Format der prompts.jsonl

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