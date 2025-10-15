# Empfehlungen zur weiteren Bereinigung des Projekts

## Abgeschlossene Maßnahmen

1. ✅ System-Prompt-Zentralisierung
   - Zentrale Quelle ist `app/core/prompts.py`. `app/prompt/system.txt` bleibt als optionales Template bestehen und wird nicht produktiv referenziert.
   - `app/api/chat_helpers.py` referenziert keine Dateien mehr und nutzt ebenfalls die zentrale Prompt-Konstante.

2. ✅ Chat-Router verbessert
   - Veraltete Router und Endpunkte entfernt; aktuelle Chat-Logik liegt unter `app/api/chat.py`
   - Robustere Fehlerbehandlung für leere Nachrichten und LLM-Fehler

3. ✅ Entfernen von redundanten Chat-Implementierungen
   - `app/api/endpoints/` wurde entfernt; zentraler Einstieg ist `app/api/chat.py` und `app/main.py`.
   - `app/main.py` verwendet direkt `process_chat_request` aus `app/api/chat.py`
   - Der direkte Chat-Endpunkt in `app/main.py` wurde entfernt
   - Logging und Zusammenfassung wurden in den Chat-Router integriert

4. ✅ Konsolidieren der ChatMessage-Implementierungen
   - `utils/message_helpers.py` wurde als veraltet markiert
   - Hinweise auf die Verwendung von `app/schemas.py` und `app/services/llm.py` wurden hinzugefügt

5. ✅ Bereinigen der virtuellen Umgebungen
   - Feststellung: `venv/` Verzeichnis existiert nicht oder wurde bereits entfernt
   - Die `.venv/` Umgebung bleibt als einzige virtuelle Umgebung aktiv

## Empfohlene nächste Maßnahmen

### Niedrige Priorität

1. Anpassen der Import-Pfade
   - Empfehlung: Konsequente Verwendung von relativen Imports innerhalb des app-Pakets
   - Vorteile: Bessere Modularisierung, einfacheres Refactoring, einheitliche Struktur

## Langfristige Überlegungen

1. Klare Trennung zwischen API-Endpunkten und Routers
   - Endpunkte sind konsolidiert unter `app/api/`; `app/routers/` wurde entfernt
   - Einheitliche Struktur für alle Endpunkte

2. Konsolidierung der eval-utils
   - Überprüfen, ob Funktionen aus `scripts/run_eval.py` in `utils/eval_utils.py` verschoben werden können
   - Verbessert die Wartbarkeit und Wiederverwendbarkeit

3. Copilot Code-Suche (@workspace / #codebase)
   - Empfehlung: Remote-Index primär nutzen; lokaler Index als Fallback.
   - Regelmäßig pushen, damit der Remote-Index aktuell bleibt.
