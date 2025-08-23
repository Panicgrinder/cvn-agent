"""
Hilfsfunktionen für den Chat-Endpunkt.
"""

import os
import functools
from typing import List

from ..schemas import ChatMessage

# Cache für den System-Prompt
_SYSTEM_PROMPT: str | None = None

@functools.lru_cache(maxsize=1)
def get_system_prompt() -> str:
    """
    Lädt den System-Prompt aus der Datei system.txt.
    Der Prompt wird gecached, um wiederholtes Laden zu vermeiden.
    
    Returns:
        Der Inhalt der system.txt-Datei
    """
    global _SYSTEM_PROMPT
    
    if _SYSTEM_PROMPT is not None:
        return _SYSTEM_PROMPT
        
    try:
        # Suche system.txt in verschiedenen möglichen Verzeichnissen
        possible_paths = [
            os.path.join("app", "prompt", "system.txt"),  # Hauptpfad (bevorzugt)
            os.path.join("data", "system.txt"),           # Alternativer Pfad
            os.path.join("app", "data", "system.txt"),
            "system.txt",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    _SYSTEM_PROMPT = f.read().strip()
                return _SYSTEM_PROMPT
                
        # Fallback, wenn keine Datei gefunden wurde
        _SYSTEM_PROMPT = "Du bist ein hilfreicher KI-Assistent. Beantworte die Fragen des Nutzers klar und präzise."
        return _SYSTEM_PROMPT
        
    except Exception:
        # Bei Fehler, verwende einen Standard-Prompt
        _SYSTEM_PROMPT = "Du bist ein hilfreicher KI-Assistent. Beantworte die Fragen des Nutzers klar und präzise."
        return _SYSTEM_PROMPT


def ensure_system_message(messages: List[ChatMessage]) -> List[ChatMessage]:
    """
    Stellt sicher, dass die Nachrichtenliste einen System-Turn enthält.
    Wenn kein System-Turn vorhanden ist, wird einer am Anfang eingefügt.
    
    Args:
        messages: Liste von ChatMessage-Objekten
        
    Returns:
        Liste von ChatMessage-Objekten mit garantiertem System-Turn
    """
    # Prüfe, ob bereits ein System-Turn vorhanden ist
    has_system = any(msg.role == "system" for msg in messages)
    
    if not has_system:
        # Füge System-Turn am Anfang ein
        system_content = get_system_prompt()
        system_message = ChatMessage(role="system", content=system_content)
        return [system_message] + messages
    
    return messages