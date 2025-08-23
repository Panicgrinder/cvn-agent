"""
Vergleich und Zusammenführung der Chat-Router aus routers/chat.py und api/endpoints/chat.py

Analyse:
  - APIRouter mit Präfix "/chat"
  - System-Prompts werden aus `app/core/prompts.py` bezogen (keine system.txt mehr)
  - Fügt Systemprompt direkt hinzu, wenn keiner vorhanden ist
  - Ruft generate_reply() direkt auf

  - APIRouter ohne Präfix
  - Nutzt ensure_system_message() aus app/api/chat_helpers.py
  - Prüft auf leere Nachrichten mit HTTPException
  - Ruft generate_reply() direkt auf

Hauptunterschiede:
1. Pfad: "/chat" vs "/"
2. Systemprompt-Handling: direkt vs über Hilfsfunktion
3. Fehlerbehandlung: Keine vs. explizite Prüfung auf leere Nachrichten

Empfehlung:
- Altes Router-Setup wurde entfernt.
- Aktuelle Chat-Verarbeitung: `app/api/chat.py` mit `process_chat_request` und Modus-Handling (eval/unrestricted).
"""