"""
HINWEIS: Diese Datei ist veraltet und wurde durch app/routers/chat.py ersetzt.

Die Funktionalität wurde in app/routers/chat.py zusammengeführt, 
die folgende Verbesserungen bietet:
- Automatisches Laden des Systemprompts
- Bessere Fehlerbehandlung
- Unterstützung für ChatRequest-Objekte

Diese Datei wird in einer zukünftigen Version entfernt werden.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from ...schemas import ChatMessage, ChatResponse
from ...services.llm import generate_reply

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(messages: List[ChatMessage]):
    """
    VERALTET: Bitte app/routers/chat.py verwenden.
    
    Chatendpunkt, der Nachrichten an das LLM sendet und eine Antwort zurückgibt.
    """
    if not messages:
        raise HTTPException(status_code=400, detail="Keine Nachrichten erhalten")
    
    response = await generate_reply(messages)
    return response