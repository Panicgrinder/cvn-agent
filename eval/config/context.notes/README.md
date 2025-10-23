Dieses Verzeichnis enthält „angeheftete“ Kontext-Referenzen für den Agenten.

- .ref-Dateien verweisen auf die tatsächlichen Zieldateien (erste Zeile Pfad).
- Die Verarbeitungsreihenfolge kann über eine optionale ORDER.txt (oder order.txt/.order) gesteuert werden.
  - Eine Zeile pro Dateiname; Leerzeilen und Zeilen mit # werden ignoriert.
  - Dateien, die nicht gelistet sind, werden anschließend alphabetisch angehängt.
  - Meta‑Dateien `ORDER.*` und `README.*` werden vom Loader ignoriert und nicht injiziert.

Beispiel-ORDER:

```
AGENT_BEHAVIOR.ref
DONELOG.ref
REPORTS.ref
TODO.ref
WORKSPACE_INDEX.ref
```
