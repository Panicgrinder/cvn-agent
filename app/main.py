from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from typing import cast as _cast
import json as _json
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
from typing import Dict, Any

from .core.settings import settings
from .api.models import ChatRequest, ChatResponse, ChatMessage
from typing import Mapping as _Mapping, Union as _Union
from .api.chat import process_chat_request, stream_chat_request
import os as _os
import platform as _platform
import fastapi as _fastapi

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
        def __init__(self, app: Any):
            super().__init__(app)
            self.lock = threading.Lock()
            self.window = float(settings.RATE_LIMIT_WINDOW_SEC)
            self.capacity = max(1, int(settings.RATE_LIMIT_REQUESTS_PER_MINUTE))
            self.burst = max(0, int(settings.RATE_LIMIT_BURST))
            from typing import Deque
            self.buckets: Dict[str, Deque[float]] = defaultdict(deque)

        async def dispatch(self, request: Request, call_next):
            # Exempt Pfade (z. B. Health)
            if request.url.path in set(settings.RATE_LIMIT_EXEMPT_PATHS):
                return await call_next(request)

            # Bestimme den Client-Key
            client_host = request.client.host if request.client else "unknown"
            if client_host in set(settings.RATE_LIMIT_TRUSTED_IPS):
                return await call_next(request)
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
                headers = {
                    "Retry-After": str(int(self.window)),
                    "X-RateLimit-Limit": str(self.capacity + self.burst),
                    "X-RateLimit-Window": str(int(self.window)),
                }
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Bitte später erneut versuchen.",
                    headers=headers,
                )
            response = await call_next(request)
            try:
                # Informative Header setzen
                from typing import Deque
                q2: Deque[float] = self.buckets[client_host]
                remaining = max(0, (self.capacity + self.burst) - len(q2))
                response.headers["X-RateLimit-Limit"] = str(self.capacity + self.burst)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Window"] = str(int(self.window))
            except Exception:
                pass
            return response

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


@app.get("/version", status_code=status.HTTP_200_OK)
async def version_info() -> Dict[str, Any]:
    """Gibt Version und Laufzeitinformationen der Anwendung zurück."""
    return {
        "app_name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "git_sha": _os.getenv("GIT_SHA"),
        "build_time": _os.getenv("BUILD_TIME"),
        "python_version": _platform.python_version(),
        "fastapi_version": getattr(_fastapi, "__version__", None),
    }


# Einfache Middleware für Request-ID und JSON-Logs
@app.middleware("http")
async def request_context_mw(request: Request, call_next):
    rid = request.headers.get(settings.REQUEST_ID_HEADER) or request.headers.get("X-Request-Id")
    if not rid:
        # einfache, lokale ID (Zeit-basiert)
        rid = f"req-{int(time.time()*1000)}"
    start = time.time()
    try:
        # request-id in state für spätere Nutzung (z. B. im Handler)
        try:
            setattr(request.state, "request_id", rid)
        except Exception:
            pass
        response = _cast(Response, await call_next(request))
        duration_ms = int((time.time() - start) * 1000)
        if settings.LOG_JSON:
            logger.info(
                _json.dumps({
                    "event": "request",
                    "path": request.url.path,
                    "method": request.method,
                    "status": int(response.status_code),
                    "duration_ms": duration_ms,
                    "request_id": rid,
                }, ensure_ascii=False)
            )
        else:
            logger.info(f"{request.method} {request.url.path} -> {int(response.status_code)} [{duration_ms} ms] rid={rid}")
        response.headers[settings.REQUEST_ID_HEADER] = rid
        return response
    except Exception as exc:
        duration_ms = int((time.time() - start) * 1000)
        if settings.LOG_JSON:
            logger.exception(_json.dumps({"event": "error", "path": request.url.path, "request_id": rid, "duration_ms": duration_ms, "error": str(exc)}, ensure_ascii=False))
        else:
            logger.exception(f"Fehler bei {request.url.path} rid={rid}: {exc}")
        # HTTPException in eine reguläre Antwort umwandeln, damit TestClient/Clients eine Response erhalten
        if isinstance(exc, HTTPException):
            # Merge evtl. vorhandene Exception-Header mit unserer Request-ID
            from typing import Any as _Any, Mapping as _Mapping, cast as _typing_cast
            raw_headers: _Any = getattr(exc, "headers", None)
            headers: Dict[str, str] = {settings.REQUEST_ID_HEADER: str(rid)}
            try:
                if isinstance(raw_headers, dict):
                    m: _Mapping[object, object] = _typing_cast(_Mapping[object, object], raw_headers)
                    for key_obj, val_obj in m.items():
                        k: str = str(key_obj)
                        v: str = str(val_obj)
                        headers[k] = v
            except Exception:
                pass
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=headers,
            )
        raise

def _get_content_from_message(m: _Union[ChatMessage, _Mapping[str, str]]) -> str:
    """Extrahiert den Content unabhängig davon, ob die Message ein ChatMessage oder ein Dict ist."""
    if isinstance(m, ChatMessage):
        return m.content or ""
    try:
        return str(m.get("content", ""))
    except Exception:
        return ""


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
        # Extrahiere Parameter aus den Rohdaten (typisiert)
        _raw = await req.json()
        from typing import Dict as _Dict, Any as _Any, cast as _typing_cast
        request_data: _Dict[str, _Any] = _typing_cast(_Dict[str, _Any], _raw if isinstance(_raw, dict) else {})
        eval_mode = bool(request_data.get("eval_mode", False))
        unrestricted_mode = bool(request_data.get("unrestricted_mode", False))

        # Eingabelängenprüfung (robust gegen gemischte Typen in messages)
        total_chars = 0
        for m in request.messages:
            total_chars += len(_get_content_from_message(m))
        if total_chars > settings.REQUEST_MAX_INPUT_CHARS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input zu lang: {total_chars} Zeichen (Limit {settings.REQUEST_MAX_INPUT_CHARS}).",
            )

        rid = getattr(req.state, "request_id", None)
        logger.info(
            f"Chat-Anfrage erhalten mit {len(request.messages)} Nachrichten, Eval-Modus: {eval_mode}, Uneingeschränkter Modus: {unrestricted_mode}, rid={rid}"
        )

        # Verarbeite die Anfrage
        response = await process_chat_request(
            request,
            eval_mode=eval_mode,
            unrestricted_mode=unrestricted_mode,
            client=None,
            request_id=rid,
        )
        return response

    except HTTPException:
        # Bekannte HTTP-Fehler (z. B. 400 bei zu langem Input) unverändert durchreichen
        raise
    except Exception as e:
        logger.exception(f"Fehler bei der Verarbeitung der Chat-Anfrage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interner Serverfehler: {str(e)}",
        )

from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, req: Request):
    """Streaming-Variante des Chat-Endpunkts (SSE-ähnliches Format)."""
    try:
        request_data = await req.json()
        eval_mode = request_data.get("eval_mode", False)
        unrestricted_mode = request_data.get("unrestricted_mode", False)
        rid = getattr(req.state, "request_id", None)
        gen = await stream_chat_request(
            request,
            eval_mode=eval_mode,
            unrestricted_mode=unrestricted_mode,
            client=None,
            request_id=rid,
        )
        return StreamingResponse(gen, media_type="text/event-stream")
    except HTTPException:
        # HTTP-Exceptions (falls sie auftreten) direkt durchreichen
        raise
    except Exception as e:
        logger.exception(f"Fehler bei der Streaming-Chat-Anfrage: {str(e)}")
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
