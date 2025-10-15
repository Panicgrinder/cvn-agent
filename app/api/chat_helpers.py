"""
Hilfsfunktionen für den Chat-Endpunkt.
"""

import functools
from typing import List

from .models import ChatMessage
from app.core.prompts import DEFAULT_SYSTEM_PROMPT


@functools.lru_cache(maxsize=1)
def get_system_prompt() -> str:
    """
    Liefert den zentral definierten System-Prompt aus app.core.prompts.
    Der Prompt wird gecached, um wiederholte Zugriffe zu vermeiden.
    """
    return DEFAULT_SYSTEM_PROMPT.strip()


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