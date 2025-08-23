from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, Field


class ChatMessage(BaseModel):
    """
    Repräsentiert eine Nachricht in einem Chat.
    """
    role: str
    content: str


class ChatRequest(BaseModel):
    """
    Request-Schema für den /chat Endpoint.
    """
    messages: List[ChatMessage]


class ChatRequest(BaseModel):
    """
    Repräsentiert eine Chat-Anfrage.
    """
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    """
    Repräsentiert die Antwort auf eine Chat-Anfrage.
    """
    content: str


class RollRequest(BaseModel):
    """
    Request-Schema für den /roll Endpoint.
    """
    dice_expression: str = Field(..., description="z.B. '2d6+3' oder 'd20'")
    reason: Optional[str] = Field(None, description="Optionale Beschreibung des Wurfs")


class RollResponse(BaseModel):
    """
    Response-Schema für den /roll Endpoint.
    """
    expression: str
    result: int
    details: List[int] = Field(..., description="Einzelne Würfelergebnisse")
    reason: Optional[str] = None


class StateApplyRequest(BaseModel):
    """
    Request-Schema für den /state/apply Endpoint.
    """
    changes: Dict[str, Any] = Field(..., description="Änderungen am Weltzustand")


class StateResponse(BaseModel):
    """
    Response-Schema für den /state Endpoint.
    """
    state: Dict[str, Any] = Field(..., description="Der aktuelle Weltzustand")
