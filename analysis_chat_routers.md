"""
Vergleich und Zusammenführung der Chat-Router aus routers/chat.py und api/endpoints/chat.py

Analyse:
- app/routers/chat.py:
  - APIRouter mit Präfix "/chat"
  - _load_system_prompt() lädt System-Prompt aus app/prompt/system.txt
  - Fügt Systemprompt direkt hinzu, wenn keiner vorhanden ist
  - Ruft generate_reply() direkt auf

- app/api/endpoints/chat.py:
  - APIRouter ohne Präfix
  - Nutzt ensure_system_message() aus app/api/chat_helpers.py
  - Prüft auf leere Nachrichten mit HTTPException
  - Ruft generate_reply() direkt auf

Hauptunterschiede:
1. Pfad: "/chat" vs "/"
2. Systemprompt-Handling: direkt vs über Hilfsfunktion
3. Fehlerbehandlung: Keine vs. explizite Prüfung auf leere Nachrichten

Empfehlung:
- app/routers/chat.py scheint die aktuellere Version zu sein
- Die Fehlerbehandlung aus app/api/endpoints/chat.py sollte übernommen werden
- Das app/api/endpoints/chat.py Modul kann nach der Zusammenführung entfernt werden
"""