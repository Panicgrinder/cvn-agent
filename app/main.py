from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
from typing import Dict, Any

from .core.settings import settings
from .api.models import ChatRequest, ChatResponse
from .api.chat import process_chat_request

# Logger-Konfiguration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI-App erstellen
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
)

# CORS-Middleware hinzufügen
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """Gesundheitscheck für den API-Server."""
    return {"status": "ok", "time": time.time()}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    """
    Chat-Endpunkt, der Anfragen an das Sprachmodell weiterleitet und Antworten zurückgibt.
    
    Args:
        request: Die Chat-Anfrage mit Nachrichten
        req: Die FastAPI-Request (wird automatisch injiziert)
        
    Returns:
        Die Chat-Antwort mit der generierten Nachricht
    """
    try:
        # Extrahiere Parameter aus den Rohdaten
        request_data = await req.json()
        eval_mode = request_data.get("eval_mode", False)
        unrestricted_mode = request_data.get("unrestricted_mode", False)
        
        logger.info(f"Chat-Anfrage erhalten mit {len(request.messages)} Nachrichten, Eval-Modus: {eval_mode}, Uneingeschränkter Modus: {unrestricted_mode}")
        
        # Verarbeite die Anfrage
        response = await process_chat_request(request, eval_mode=eval_mode, unrestricted_mode=unrestricted_mode)
        return response
        
    except Exception as e:
        logger.exception(f"Fehler bei der Verarbeitung der Chat-Anfrage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interner Serverfehler: {str(e)}",
        )

@app.get("/")
async def root():
    """
    Root-Endpunkt für einfache Gesundheitsprüfung
    """
    return {"message": "CVN Agent API ist aktiv"}
