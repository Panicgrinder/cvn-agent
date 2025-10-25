from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional, Any, Union, cast


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
    # Weitere Sampling-/Steuerungsoptionen (Ollama/llama.cpp)
    top_k: Optional[int] = None
    min_p: Optional[float] = None
    typical_p: Optional[float] = None
    tfs_z: Optional[float] = None
    mirostat: Optional[int] = None  # 0,1,2
    mirostat_tau: Optional[float] = None
    mirostat_eta: Optional[float] = None
    penalize_newline: Optional[bool] = None

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
    # Akzeptiert ChatMessage-Objekte und/oder Dicts (rückwärtskompatibel)
    messages: List[Union[ChatMessage, Dict[str, str]]]
    model: Optional[str] = None
    # Akzeptiert entweder ein freies Dict (rückwärtskompatibel) oder ChatOptions (validiert)
    options: Optional[Union[Dict[str, Any], ChatOptions]] = None
    # Optional: Profil-/Mandanten-ID für gezielte Policies oder Memories
    profile_id: Optional[str] = None
    # Optional: Session-ID für die Sitzungs-Memory
    session_id: Optional[str] = None

    @field_validator("messages", mode="before")
    @classmethod
    def _coerce_messages(cls, v: Any) -> Any:
        """
        Erlaubt gemischte Eingaben (Dicts/Objekte) und normalisiert auf ChatMessage/Dict.
        - Wenn ein Element bereits ChatMessage ist: belassen
        - Wenn ein Dict mit role/content: akzeptieren
        - Sonst: best-effort Extraktion über Attribute
        """
        try:
            from typing import Any as _Any, List as _List, Union as _Union, Dict as _Dict
            if isinstance(v, (list, tuple)):
                seq: _List[_Any] = list(cast(_List[_Any], v))
            else:
                return cast(Any, v)
        except Exception:
            return cast(Any, v)
        out: _List[_Union[ChatMessage, _Dict[str, str]]] = []
        for m in seq:
            if isinstance(m, ChatMessage):
                out.append(m)
            elif isinstance(m, dict):
                mm = cast(Dict[Any, Any], m)
                role = str(mm.get("role", "user"))
                content = str(mm.get("content", ""))
                out.append({"role": role, "content": content})
            else:
                role = str(getattr(m, "role", "user"))
                content = str(getattr(m, "content", ""))
                out.append({"role": role, "content": content})
        return out
    
class ChatResponse(BaseModel):
    """
    Modell für eine Chat-Antwort.
    """
    content: str
    model: Optional[str] = None