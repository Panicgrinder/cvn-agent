import httpx
import logging
from typing import Dict, Any

from ..core.settings import settings
from ..core.prompts import EVAL_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT, UNRESTRICTED_SYSTEM_PROMPT
from .models import ChatRequest, ChatResponse

# Logger konfigurieren
logger = logging.getLogger(__name__)

async def process_chat_request(request: ChatRequest, eval_mode: bool = False, unrestricted_mode: bool = False) -> ChatResponse:
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
        messages = list(request.messages)
        
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

        ollama_payload: Dict[str, Any] = {
            "model": req_model or settings.MODEL_NAME,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        # API-Endpunkt für Ollama Chat (Host ggf. überschrieben)
        ollama_url = f"{base_host}/api/chat"
        
        # Anfrage an Ollama senden
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"Sende Anfrage an Ollama: {ollama_url}")
            
            response = await client.post(
                ollama_url,
                json=ollama_payload,
                headers={"Content-Type": "application/json"}
            )
            
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
            return ChatResponse(
                content=generated_content,
                model=settings.MODEL_NAME
            )
            
    except Exception as e:
        logger.exception(f"Fehler bei der Verarbeitung der Chat-Anfrage: {str(e)}")
        # Gib eine Fehlerantwort zurück
        return ChatResponse(
            content=f"Entschuldigung, bei der Verarbeitung Ihrer Anfrage ist ein Fehler aufgetreten: {str(e)}",
            model=settings.MODEL_NAME
        )