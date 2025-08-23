# Empfehlungen zur weiteren Bereinigung des Projekts

## Abgeschlossene Maßnahmen
1. ✅ System-Prompt-Dateien synchronisiert und Code-Referenzen aktualisiert
   - `app/prompt/system.txt` und `data/system.txt` haben nun identischen Inhalt
   - Code-Pfade wurden in `app/api/chat_helpers.py` aktualisiert, um den Pfad in `app/prompt/system.txt` zu priorisieren

2. ✅ Chat-Router verbessert
   - Fehlerbehandlung aus `app/api/endpoints/chat.py` in `app/routers/chat.py` integriert
   - Robustere Fehlerbehandlung für leere Nachrichten und LLM-Fehler

3. ✅ Entfernen von redundanten Chat-Implementierungen
   - `app/api/endpoints/chat.py` wurde als veraltet markiert
   - `app/main.py` wurde aktualisiert, um nur den Router aus `app/routers/chat.py` zu verwenden
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
   - Entscheidung, ob die Endpunkte unter `app/api/` oder `app/routers/` organisiert werden sollen
   - Einheitliche Struktur für alle Endpunkte

2. Konsolidierung der eval-utils
   - Überprüfen, ob Funktionen aus `scripts/run_eval.py` in `utils/eval_utils.py` verschoben werden können
   - Verbessert die Wartbarkeit und Wiederverwendbarkeit