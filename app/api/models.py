from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Union


class ChatOptions(BaseModel):
    """
    Erweiterte Options für den Chat-Request (validiert via Pydantic).

    Hinweis: Die Normalisierung/Begrenzung erfolgt weiterhin in
    `app/api/chat_helpers.normalize_ollama_options`. Dieses Schema stellt sicher,
    dass typische Felder eine erwartbare Form haben.
    """
    # Allgemein/Steuerung
    host: Optional[str] = None
    session_id: Optional[str] = None

    # Sampling/Decoding
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    num_predict: Optional[int] = None  # Alias für max_tokens
    max_tokens: Optional[int] = None
    num_ctx: Optional[int] = None
    repeat_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    seed: Optional[int] = None
    repeat_last_n: Optional[int] = None
    # stop: Liste von Stop-Token; zur Kompatibilität erlauben wir auch einzelne Strings
    stop: Optional[Union[List[str], str]] = None

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
    # Akzeptiert entweder ein freies Dict (rückwärtskompatibel) oder ChatOptions (validiert)
    options: Optional[Union[Dict[str, Any], ChatOptions]] = None
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