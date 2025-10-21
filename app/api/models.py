from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class ChatMessage(BaseModel):
    """
    Modell für eine Chat-Nachricht.
    """
    role: str
    content: str
    
class ChatRequest(BaseModel):
    """
    Modell für eine Chat-Anfrage.
    """
    messages: List[Dict[str, str]]
    model: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    # Optional: Profil-/Mandanten-ID für gezielte Policies oder Memories
    profile_id: Optional[str] = None
    # Optional: Session-ID für die Sitzungs-Memory
    session_id: Optional[str] = None
    
class ChatResponse(BaseModel):
    """
    Modell für eine Chat-Antwort.
    """
    content: str
    model: Optional[str] = None