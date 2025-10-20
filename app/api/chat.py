import httpx
import logging
import time
import json as _json
from typing import Dict, Any, List, Optional

from ..core.settings import settings
from ..core.prompts import EVAL_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT, UNRESTRICTED_SYSTEM_PROMPT
from ..core.content_management import modify_prompt_for_freedom
from ..utils.session_memory import session_memory
from utils.context_notes import load_context_notes
from .models import ChatRequest, ChatResponse

# Logger konfigurieren
logger = logging.getLogger(__name__)

async def stream_chat_request(
    request: ChatRequest,
    eval_mode: bool = False,
    unrestricted_mode: bool = False,
    client: Optional[httpx.AsyncClient] = None,
    request_id: Optional[str] = None,
):
    """
    Startet eine Streaming-Anfrage an das Modell und liefert ein Async-Generator
    mit SSE-Formatierten Daten (data: <chunk>\n\n). Bei Abschluss wird ein 'done'-Event gesendet.
    """
    # Nachrichten normalisieren
    messages: List[Dict[str, str]] = []
    for m in request.messages:
        if isinstance(m, dict):
            role = m.get("role", "user")
            content = m.get("content", "")
        else:
            role = getattr(m, "role", "user")
            content = getattr(m, "content", "")
        messages.append({"role": role, "content": content})

    # Systemprompt auswählen/ersetzen
    if eval_mode:
        logger.info(f"Eval-Modus aktiv (stream): Ersetze Systemprompt rid={request_id}")
        messages = [msg for msg in messages if msg.get("role") != "system"]
        sys_prompt = EVAL_SYSTEM_PROMPT
        # Optional: Policy-Hook anwenden
        if getattr(settings, "CONTENT_POLICY_ENABLED", False):
            try:
                sys_prompt = modify_prompt_for_freedom(sys_prompt)
            except Exception:
                pass
        messages.insert(0, {"role": "system", "content": sys_prompt})
    elif unrestricted_mode:
        logger.info(f"Uneingeschränkter Modus aktiv (stream): Ersetze Systemprompt rid={request_id}")
        messages = [msg for msg in messages if msg.get("role") != "system"]
        sys_prompt = UNRESTRICTED_SYSTEM_PROMPT
        if getattr(settings, "CONTENT_POLICY_ENABLED", False):
            try:
                sys_prompt = modify_prompt_for_freedom(sys_prompt)
            except Exception:
                pass
        messages.insert(0, {"role": "system", "content": sys_prompt})
    else:
        if not any(msg.get("role") == "system" for msg in messages):
            sys_prompt = DEFAULT_SYSTEM_PROMPT
            if getattr(settings, "CONTENT_POLICY_ENABLED", False):
                try:
                    sys_prompt = modify_prompt_for_freedom(sys_prompt)
                except Exception:
                    pass
            messages.insert(0, {"role": "system", "content": sys_prompt})

    # Optionale Kontext-Notizen injizieren (als zusätzliche System-Nachricht)
    try:
        enabled = bool(getattr(settings, "CONTEXT_NOTES_ENABLED", False))
        from typing import Optional as _Optional
        notes: _Optional[str] = None
        try:
            notes = load_context_notes(
                getattr(settings, "CONTEXT_NOTES_PATHS", []),
                getattr(settings, "CONTEXT_NOTES_MAX_CHARS", 4000),
            )
        except Exception:
            notes = None
        # Füge Notizen ein, wenn aktiviert ODER Notizen vorhanden sind
        if (enabled or notes) and notes:
            messages.insert(1, {"role": "system", "content": f"[Kontext-Notizen]\n{notes}"})
    except Exception:
        # Fehler beim Laden der Notizen ignorieren
        pass

    # Optionen
    from typing import Dict as _Dict, Any as _Any
    req_model = getattr(request, "model", None)
    req_options: _Dict[str, _Any] = getattr(request, "options", None) or {}
    temperature: float = float(req_options.get("temperature", settings.TEMPERATURE))
    base_host: str = str(req_options.get("host", settings.OLLAMA_HOST))
    # num_predict Alias: max_tokens zulassen (Kompatibilität zu CLI)
    try:
        requested_tokens_raw = req_options.get("num_predict", req_options.get("max_tokens", settings.REQUEST_MAX_TOKENS))
        requested_tokens = int(requested_tokens_raw)
    except Exception:
        requested_tokens = settings.REQUEST_MAX_TOKENS
    num_predict = max(1, min(requested_tokens, settings.REQUEST_MAX_TOKENS))
    if eval_mode:
        temperature = min(temperature, 0.25)
    top_p_val = req_options.get("top_p")
    try:
        top_p: Optional[float] = float(top_p_val) if top_p_val is not None else None
    except Exception:
        top_p = None

    # Session Memory: optional bestehenden Verlauf voranstellen
    try:
        if getattr(settings, "SESSION_MEMORY_ENABLED", False):
            from typing import Optional as _Optional, Dict as _Dict, Any as _Any
            opts: _Optional[_Dict[str, _Any]] = getattr(request, "options", None)
            sess_id: _Optional[str] = None
            if isinstance(opts, dict):
                _val = opts.get("session_id")
                sess_id = _val if isinstance(_val, str) else None
            if isinstance(sess_id, str) and sess_id:
                prior = session_memory.get(sess_id)
                if prior:
                    # Systemprompt möglichst an erster Stelle behalten
                    sys_msgs = [m for m in messages if m.get("role") == "system"]
                    non_sys = [m for m in messages if m.get("role") != "system"]
                    # prior sind Mappings[str,str]; in Dict[str,str] kopieren
                    prior_cast = [{"role": str(m.get("role", "user")), "content": str(m.get("content", ""))} for m in prior]
                    messages = sys_msgs + prior_cast + non_sys
    except Exception:
        pass

    ollama_payload: Dict[str, Any] = {
        "model": req_model or settings.MODEL_NAME,
        "messages": messages,
        "stream": True,
        "options": {"temperature": temperature, "num_predict": num_predict},
    }
    if top_p is not None:
        ollama_payload["options"]["top_p"] = top_p

    ollama_url = f"{base_host}/api/chat"

    headers = {"Content-Type": "application/json"}
    if request_id:
        headers[settings.REQUEST_ID_HEADER] = request_id
    if getattr(settings, "LOG_JSON", False):
        logger.info(
            _json.dumps({
                "event": "model_request",
                "url": ollama_url,
                "model": ollama_payload.get("model"),
                "options": ollama_payload.get("options", {}),
                "stream": True,
                "request_id": request_id,
            }, ensure_ascii=False)
        )
    else:
        logger.info(
            f"Sende Streaming-Anfrage an Ollama: {ollama_url} model={ollama_payload.get('model')} opts={ollama_payload.get('options', {})} rid={request_id}"
        )

    async def _gen():
        started = time.time()
        try:
            async def _do_stream(_client: httpx.AsyncClient):
                async with _client.stream("POST", ollama_url, json=ollama_payload, headers=headers) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = _json.loads(line)
                            # Ollama sendet inkrementelle Inhalte unter message.content
                            content = data.get("message", {}).get("content")
                            if content:
                                yield f"data: {content}\n\n"
                            if data.get("done"):
                                break
                        except Exception:
                            # Fallback: rohen Inhalt weiterreichen
                            yield f"data: {line}\n\n"

            if client is not None:
                async for chunk in _do_stream(client):
                    yield chunk
            else:
                async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as temp_client:
                    async for chunk in _do_stream(temp_client):
                        yield chunk

        except Exception as e:
            if getattr(settings, "LOG_JSON", False):
                logger.exception(_json.dumps({"event": "model_error", "error": str(e), "request_id": request_id}, ensure_ascii=False))
            else:
                logger.exception(f"Streaming-Fehler: {e}")
            # Fehler als SSE senden
            yield f"event: error\ndata: {str(e)}\n\n"
        finally:
            duration_ms = int((time.time() - started) * 1000)
            if getattr(settings, "LOG_JSON", False):
                logger.info(_json.dumps({"event": "model_stream_done", "duration_ms": duration_ms, "request_id": request_id}, ensure_ascii=False))
            else:
                logger.info(f"Streaming abgeschlossen in {duration_ms} ms rid={request_id}")
            # Done-Event signalisieren
            yield "event: done\ndata: {}\n\n"

    return _gen()

async def process_chat_request(
    request: ChatRequest,
    eval_mode: bool = False,
    unrestricted_mode: bool = False,
    client: Optional[httpx.AsyncClient] = None,
    request_id: Optional[str] = None,
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
        # Nachrichten normalisieren
        messages: List[Dict[str, str]] = []
        for m in request.messages:
            if isinstance(m, dict):
                role = m.get("role", "user")
                content = m.get("content", "")
            else:
                role = getattr(m, "role", "user")
                content = getattr(m, "content", "")
            messages.append({"role": role, "content": content})

        # Systemprompt auswählen/ersetzen
        if eval_mode:
            logger.info(f"Eval-Modus aktiv: Ersetze Systemprompt rid={request_id}")
            messages = [msg for msg in messages if msg.get("role") != "system"]
            sys_prompt = EVAL_SYSTEM_PROMPT
            if getattr(settings, "CONTENT_POLICY_ENABLED", False):
                try:
                    sys_prompt = modify_prompt_for_freedom(sys_prompt)
                except Exception:
                    pass
            messages.insert(0, {"role": "system", "content": sys_prompt})
        elif unrestricted_mode:
            logger.info(f"Uneingeschränkter Modus aktiv: Ersetze Systemprompt rid={request_id}")
            messages = [msg for msg in messages if msg.get("role") != "system"]
            sys_prompt = UNRESTRICTED_SYSTEM_PROMPT
            if getattr(settings, "CONTENT_POLICY_ENABLED", False):
                try:
                    sys_prompt = modify_prompt_for_freedom(sys_prompt)
                except Exception:
                    pass
            messages.insert(0, {"role": "system", "content": sys_prompt})
        else:
            if not any(msg.get("role") == "system" for msg in messages):
                sys_prompt = DEFAULT_SYSTEM_PROMPT
                if getattr(settings, "CONTENT_POLICY_ENABLED", False):
                    try:
                        sys_prompt = modify_prompt_for_freedom(sys_prompt)
                    except Exception:
                        pass
                messages.insert(0, {"role": "system", "content": sys_prompt})

        # Optionale Kontext-Notizen injizieren (als zusätzliche System-Nachricht)
        try:
            enabled = bool(getattr(settings, "CONTEXT_NOTES_ENABLED", False))
            from typing import Optional as _Optional
            notes: _Optional[str] = None
            try:
                notes = load_context_notes(
                    getattr(settings, "CONTEXT_NOTES_PATHS", []),
                    getattr(settings, "CONTEXT_NOTES_MAX_CHARS", 4000),
                )
            except Exception:
                notes = None
            if (enabled or notes) and notes:
                messages.insert(1, {"role": "system", "content": f"[Kontext-Notizen]\n{notes}"})
        except Exception:
            pass

    # Options/Overrides
        from typing import Dict as _Dict, Any as _Any
        req_model = getattr(request, "model", None)
        req_options: _Dict[str, _Any] = getattr(request, "options", None) or {}
        temperature: float = float(req_options.get("temperature", settings.TEMPERATURE))
        base_host: str = str(req_options.get("host", settings.OLLAMA_HOST))
        # num_predict Alias: max_tokens zulassen (Kompatibilität zu CLI)
        try:
            requested_tokens_raw = req_options.get("num_predict", req_options.get("max_tokens", settings.REQUEST_MAX_TOKENS))
            requested_tokens = int(requested_tokens_raw)
        except Exception:
            requested_tokens = settings.REQUEST_MAX_TOKENS
        num_predict = max(1, min(requested_tokens, settings.REQUEST_MAX_TOKENS))
        if eval_mode:
            temperature = min(temperature, 0.25)
        # Optional: top_p aus Optionen übernehmen, wenn gesetzt
        top_p_val = req_options.get("top_p")
        try:
            top_p: Optional[float] = float(top_p_val) if top_p_val is not None else None
        except Exception:
            top_p = None

        # Session Memory (optional): bisherigen Verlauf voranstellen
        try:
            if getattr(settings, "SESSION_MEMORY_ENABLED", False):
                from typing import Optional as _Optional, Dict as _Dict, Any as _Any
                opts2: _Optional[_Dict[str, _Any]] = getattr(request, "options", None)
                sess_id2: _Optional[str] = None
                if isinstance(opts2, dict):
                    _val2 = opts2.get("session_id")
                    sess_id2 = _val2 if isinstance(_val2, str) else None
                if isinstance(sess_id2, str) and sess_id2:
                    prior2 = session_memory.get(sess_id2)
                    if prior2:
                        sys_msgs2 = [m for m in messages if m.get("role") == "system"]
                        non_sys2 = [m for m in messages if m.get("role") != "system"]
                        prior2_cast = [{"role": str(m.get("role", "user")), "content": str(m.get("content", ""))} for m in prior2]
                        messages = sys_msgs2 + prior2_cast + non_sys2
        except Exception:
            pass

        ollama_payload: Dict[str, Any] = {
            "model": req_model or settings.MODEL_NAME,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": num_predict},
        }
        if top_p is not None:
            # Nur setzen, wenn sinnvoller Wert
            ollama_payload["options"]["top_p"] = top_p

        ollama_url = f"{base_host}/api/chat"

        async def _post_with(_client: httpx.AsyncClient):
            # Downstream-Header inkl. Request-ID propagieren
            headers = {"Content-Type": "application/json"}
            if request_id:
                headers[settings.REQUEST_ID_HEADER] = request_id
            # Logging (JSON/Plain)
            if getattr(settings, "LOG_JSON", False):
                logger.info(
                    _json.dumps({
                        "event": "model_request",
                        "url": ollama_url,
                        "model": ollama_payload.get("model"),
                        "options": ollama_payload.get("options", {}),
                        "stream": bool(ollama_payload.get("stream", False)),
                        "request_id": request_id,
                    }, ensure_ascii=False)
                )
            else:
                logger.info(
                    f"Sende Anfrage an Ollama: {ollama_url} model={ollama_payload.get('model')} "
                    f"opts={ollama_payload.get('options', {})} rid={request_id}"
                )
            started = time.time()
            resp = await _client.post(ollama_url, json=ollama_payload, headers=headers)
            # Dauer anhängen (wird nach raise_for_status detailliert geloggt)
            setattr(resp, "_started", started)
            return resp

        if client is not None:
            response = await _post_with(client)
        else:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as temp_client:
                response = await _post_with(temp_client)

        response.raise_for_status()
        result = response.json()
        generated_content = result.get("message", {}).get("content", "")

        max_len = max(0, int(getattr(settings, "LOG_TRUNCATE_CHARS", 200)))
        preview = generated_content if len(generated_content) <= max_len else (generated_content[:max_len] + "...")
        # Dauer falls vorhanden
        started = getattr(response, "_started", None)
        duration_ms = int((time.time() - started) * 1000) if isinstance(started, float) else None
        if getattr(settings, "LOG_JSON", False):
            logger.info(
                _json.dumps({
                    "event": "model_response",
                    "model": ollama_payload.get("model"),
                    "status": int(response.status_code),
                    "duration_ms": duration_ms,
                    "preview": preview,
                    "request_id": request_id,
                }, ensure_ascii=False)
            )
        else:
            if duration_ms is not None:
                logger.info(f"Antwort von Ollama erhalten. {duration_ms} ms rid={request_id} Inhalt: {preview}")
            else:
                logger.info(f"Antwort von Ollama erhalten. rid={request_id} Inhalt: {preview}")

        # Session Memory (optional): neuen Nutzer-Input und Modell-Antwort ablegen
        try:
            if getattr(settings, "SESSION_MEMORY_ENABLED", False):
                from typing import Optional as _Optional, Dict as _Dict, Any as _Any
                opts3: _Optional[_Dict[str, _Any]] = getattr(request, "options", None)
                sess_id3: _Optional[str] = None
                if isinstance(opts3, dict):
                    _val3 = opts3.get("session_id")
                    sess_id3 = _val3 if isinstance(_val3, str) else None
                if isinstance(sess_id3, str) and sess_id3:
                    # Nur die letzten Benutzer- und Assistenten-Nachrichten persistieren
                    new_msgs = [m for m in messages if m.get("role") in ("user", "assistant")]
                    # Antwort ebenfalls hinzufügen
                    new_msgs.append({"role": "assistant", "content": generated_content})
                    # parameter erwartet List[Mapping[str,str]]; Dicts sind kompatibel
                    session_memory.put_and_trim(
                        sess_id3,
                        new_msgs,  # type: ignore[arg-type]
                        max_messages=int(getattr(settings, "SESSION_MEMORY_MAX_MESSAGES", 20)),
                        max_chars=int(getattr(settings, "SESSION_MEMORY_MAX_CHARS", 12000)),
                    )
        except Exception:
            pass

        return ChatResponse(content=generated_content, model=settings.MODEL_NAME)
    except Exception as e:
        if getattr(settings, "LOG_JSON", False):
            logger.exception(_json.dumps({"event": "model_error", "error": str(e), "request_id": request_id}, ensure_ascii=False))
        else:
            logger.exception(f"Fehler bei der Verarbeitung der Chat-Anfrage: {str(e)}")
        return ChatResponse(content=f"Entschuldigung, bei der Verarbeitung Ihrer Anfrage ist ein Fehler aufgetreten: {str(e)}", model=settings.MODEL_NAME)