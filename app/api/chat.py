import httpx
import logging
from typing import Dict, Any, List, Optional

from ..core.settings import settings
from ..core.prompts import EVAL_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT, UNRESTRICTED_SYSTEM_PROMPT
from .models import ChatRequest, ChatResponse

# Logger konfigurieren
logger = logging.getLogger(__name__)

async def process_chat_request(
    request: ChatRequest,
    eval_mode: bool = False,
    unrestricted_mode: bool = False,
    client: Optional[httpx.AsyncClient] = None,
) -> ChatResponse:
    """
    Verarbeitet eine Chat-Anfrage und gibt eine Antwort zurück.
    
    Args:
        request: Die Chat-Anfrage
        eval_mode: Wenn True, wird der RPG-Modus deaktiviert
        unrestricted_mode: Wenn True, werden keine Inhaltsfilter angewendet
        
    Returns:
        Die Chat-Antwort
    """
    try:
        # Systemprompt je nach Modus ersetzen
        # Normalisiere eingehende Nachrichten zu einfachen Dicts, damit .get sicher ist
        messages: List[Dict[str, str]] = []
        for m in request.messages:
            if isinstance(m, dict):
                role = m.get("role", "user")
                content = m.get("content", "")
            else:
                role = getattr(m, "role", "user")
                content = getattr(m, "content", "")
            messages.append({"role": role, "content": content})
        
        if eval_mode:
            logger.info("Eval-Modus aktiv: Ersetze Systemprompt")
            
            # Entferne alle vorhandenen Systemprompts
            messages = [msg for msg in messages if msg.get("role") != "system"]
            
            # Füge einen neuen neutralen Systemprompt hinzu
            messages.insert(0, {
                "role": "system",
                "content": EVAL_SYSTEM_PROMPT
            })
        elif unrestricted_mode:
            logger.info("Uneingeschränkter Modus aktiv: Ersetze Systemprompt")
            
            # Entferne alle vorhandenen Systemprompts
            messages = [msg for msg in messages if msg.get("role") != "system"]
            
            # Füge einen uneingeschränkten Systemprompt hinzu
            messages.insert(0, {
                "role": "system",
                "content": UNRESTRICTED_SYSTEM_PROMPT
            })
        else:
            # Prüfe, ob bereits ein Systemprompt vorhanden ist
            has_system = any(msg.get("role") == "system" for msg in messages)
            
            if not has_system:
                # Füge den Standard-Systemprompt hinzu
                messages.insert(0, {
                    "role": "system",
                    "content": DEFAULT_SYSTEM_PROMPT
                })
        # Bereite die Payload für Ollama vor (Overrides aus Request berücksichtigen)
        from typing import Dict as _Dict, Any as _Any
        req_model = getattr(request, "model", None)
        req_options: _Dict[str, _Any] = getattr(request, "options", None) or {}
        temperature: float = float(req_options.get("temperature", settings.TEMPERATURE))
        base_host: str = str(req_options.get("host", settings.OLLAMA_HOST))

        # Erzwinge sicheres Token-Limit (num_predict) – clamp auf Maximalwert
        try:
            requested_tokens = int(req_options.get("num_predict", settings.REQUEST_MAX_TOKENS))
        except Exception:
            requested_tokens = settings.REQUEST_MAX_TOKENS
        num_predict = max(1, min(requested_tokens, settings.REQUEST_MAX_TOKENS))

        # In Eval-Modus: neutralere Einstellungen
        if eval_mode:
            temperature = min(temperature, 0.25)

        ollama_payload: Dict[str, Any] = {
            "model": req_model or settings.MODEL_NAME,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            },
        }

        # API-Endpunkt für Ollama Chat (Host ggf. überschrieben)
        ollama_url = f"{base_host}/api/chat"
        
        # Anfrage an Ollama senden
        # Gemeinsamen Client wiederverwenden, wenn übergeben; sonst temporären erzeugen
        async def _post_with(_client: httpx.AsyncClient):
            logger.info(f"Sende Anfrage an Ollama: {ollama_url}")
            response = await _client.post(
                ollama_url,
                json=ollama_payload,
                headers={"Content-Type": "application/json"}
            )
            return response

        if client is not None:
            response = await _post_with(client)
        else:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as temp_client:
                response = await _post_with(temp_client)

        # Fehler bei Statuscode != 200
        response.raise_for_status()

        # Verarbeite die Antwort
        result = response.json()

        # Extrahiere die generierte Nachricht
        generated_content = result.get("message", {}).get("content", "")

        # Debug-Logausgabe
        content_preview = generated_content[:100] + "..." if len(generated_content) > 100 else generated_content
        logger.info(f"Antwort von Ollama erhalten. Inhalt: {content_preview}")

        # Erstelle die Chat-Antwort
        return ChatResponse(content=generated_content, model=settings.MODEL_NAME)
            
    except Exception as e:
        logger.exception(f"Fehler bei der Verarbeitung der Chat-Anfrage: {str(e)}")
        # Gib eine Fehlerantwort zurück
        return ChatResponse(
            content=f"Entschuldigung, bei der Verarbeitung Ihrer Anfrage ist ein Fehler aufgetreten: {str(e)}",
            model=settings.MODEL_NAME
        )