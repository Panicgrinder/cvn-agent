from pydantic import BaseModel
from typing import List, Dict, Optional

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
    
class ChatResponse(BaseModel):
    """
    Modell für eine Chat-Antwort.
    """
    content: str
    model: Optional[str] = None