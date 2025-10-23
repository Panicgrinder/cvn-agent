"""
DEPRECATED MODULE
=================

Dieses Modul ist veraltet. Bitte importiere Modelle ab sofort aus
`app.api.models` statt aus `app.schemas`.

Es bleibt als dünne Weiterleitung bestehen, um ältere Importe nicht sofort zu brechen.
Künftige Versionen können diese Datei vollständig entfernen.
"""

from typing import Any

# Laufzeit: einfache Weiterleitung (typisiert als Any, um Checker-Konflikte zu vermeiden)
from app.api import models as _models
ChatMessage: Any = _models.ChatMessage
ChatRequest: Any = _models.ChatRequest
ChatResponse: Any = _models.ChatResponse

__all__ = ["ChatMessage", "ChatRequest", "ChatResponse"]
