"""
HINWEIS: Diese Datei ist veraltet und wird durch app/schemas.py (ChatMessage)
und app/services/llm.py (system_message) ersetzt.

Diese Datei wird in einer zukünftigen Version entfernt werden.
"""

from typing import Dict

class ChatMessage:
    """Repräsentiert eine Nachricht in einem Chat."""
    
    def __init__(self, role: str, content: str):
        """
        Initialisiert eine neue Chat-Nachricht.
        
        Args:
            role: Die Rolle des Nachrichtensenders (z.B. "system", "user", "assistant")
            content: Der Inhalt der Nachricht
        """
        self.role = role
        self.content = content
        
    def to_dict(self) -> Dict[str, str]:
        """Konvertiert die Nachricht in ein Dictionary."""
        return {
            "role": self.role,
            "content": self.content
        }

def system_message(text: str) -> ChatMessage:
    """
    Hilfsfunktion zum Erstellen einer System-Nachricht.
    
    Args:
        text: Der Inhalt der System-Nachricht
        
    Returns:
        ChatMessage: Eine ChatMessage mit der Rolle "system"
    """
    return ChatMessage(role="system", content=text)