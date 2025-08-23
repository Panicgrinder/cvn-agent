from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RollRequest(BaseModel):
    dice_expression: str = Field(..., description="z.B. '2d6+3' oder 'd20'")
    reason: Optional[str] = Field(None, description="Optionale Beschreibung des Wurfs")


class RollResponse(BaseModel):
    expression: str
    result: int
    details: List[int] = Field(..., description="Einzelne Würfelergebnisse")
    reason: Optional[str] = None


class StateApplyRequest(BaseModel):
    changes: Dict[str, Any] = Field(..., description="Änderungen am Weltzustand")


class StateResponse(BaseModel):
    state: Dict[str, Any] = Field(..., description="Der aktuelle Weltzustand")
