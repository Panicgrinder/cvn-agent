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

# Optional: Einfache In-Memory Rate-Limit Middleware (pro IP)
if settings.RATE_LIMIT_ENABLED:
    from starlette.middleware.base import BaseHTTPMiddleware
    from collections import defaultdict, deque
    import threading

    class _RateLimiter(BaseHTTPMiddleware):
        def __init__(self, app):
            super().__init__(app)  # type: ignore[arg-type]
            self.lock = threading.Lock()
            self.window = 60.0
            self.capacity = max(1, int(settings.RATE_LIMIT_REQUESTS_PER_MINUTE))
            self.burst = max(0, int(settings.RATE_LIMIT_BURST))
            from typing import Deque
            self.buckets: Dict[str, Deque[float]] = defaultdict(deque)

        async def dispatch(self, request: Request, call_next):
            # Bestimme den Client-Key
            client_host = request.client.host if request.client else "unknown"
            now = time.time()
            allow = True

            with self.lock:
                from typing import Deque
                q: Deque[float] = self.buckets[client_host]
                # Fenster bereinigen
                cutoff = now - self.window
                while q and q[0] < cutoff:
                    q.popleft()
                # Limit prüfen: capacity + burst
                limit = self.capacity + self.burst
                if len(q) >= limit:
                    allow = False
                else:
                    q.append(now)

            if not allow:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Bitte später erneut versuchen.",
                )

            return await call_next(request)

    app.add_middleware(_RateLimiter)

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

        # Eingabelängenprüfung (robust gegen fehlende Felder)
        total_chars = sum(len(str(m.get("content", ""))) for m in request.messages)
        if total_chars > settings.REQUEST_MAX_INPUT_CHARS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input zu lang: {total_chars} Zeichen (Limit {settings.REQUEST_MAX_INPUT_CHARS}).",
            )

        logger.info(
            f"Chat-Anfrage erhalten mit {len(request.messages)} Nachrichten, Eval-Modus: {eval_mode}, Uneingeschränkter Modus: {unrestricted_mode}"
        )

        # Verarbeite die Anfrage
        response = await process_chat_request(
            request, eval_mode=eval_mode, unrestricted_mode=unrestricted_mode
        )
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
