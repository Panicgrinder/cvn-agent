from fastapi import APIRouter, HTTPException
import os
import logging
from app.schemas import ChatRequest, ChatResponse, ChatMessage
from app.services.llm import generate_reply, system_message
from app.utils.convlog import create_log_record, log_turn
from app.utils.summarize import summarize_turn

router = APIRouter(prefix="/chat")

# Lade den Systemprompt einmal pro Prozessstart
_system_prompt_text = None

def _load_system_prompt() -> str:
    """Lädt den Systemprompt aus der Datei, falls noch nicht geladen."""
    global _system_prompt_text
    if _system_prompt_text is None:
        try:
            prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompt", "system.txt")
            with open(prompt_path, "r", encoding="utf-8") as f:
                _system_prompt_text = f.read().strip()
        except Exception as e:
            logging.warning(f"Fehler beim Laden des Systemprompts: {str(e)}")
            _system_prompt_text = ""
    return _system_prompt_text

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Verarbeitet eine Chat-Anfrage und gibt eine Antwort vom LLM zurück.
    Fügt automatisch einen Systemprompt hinzu, wenn keiner vorhanden ist.
    """
    # Überprüfe, ob Nachrichten vorhanden sind
    if not request.messages:
        raise HTTPException(status_code=400, detail="Keine Nachrichten erhalten")
    
    messages = list(request.messages)  # Kopie erstellen, um die Originaldaten nicht zu verändern
    
    # Prüfe, ob bereits ein Systemprompt vorhanden ist
    has_system_message = any(msg.role == "system" for msg in messages)
    
    # Füge Systemprompt hinzu, wenn keiner vorhanden ist
    if not has_system_message:
        prompt_text = _load_system_prompt()
        if prompt_text:
            messages.insert(0, system_message(prompt_text))
    
    try:
        # Generiere Antwort vom LLM
        response = await generate_reply(messages)
        
        # Optional: Erstelle Zusammenfassung für Logging
        try:
            summary = summarize_turn(
                [{"role": msg.role, "content": msg.content} for msg in messages], 
                response.content
            )
        except Exception as e:
            logging.warning(f"Fehler bei der Zusammenfassung: {str(e)}")
            summary = {"summary": "", "keyfacts": []}
            
        # Optional: Logge die Konversation
        try:
            log_entry = create_log_record(
                messages=[{"role": msg.role, "content": msg.content} for msg in messages],
                response=response.content,
                summary=summary.get("summary", "")
            )
            log_turn(log_entry)
        except Exception as e:
            logging.error(f"Fehler beim Loggen der Konversation: {str(e)}")
        
        return response
        
    except Exception as e:
        # Bei anderen Fehlern gib eine benutzerfreundliche Fehlermeldung zurück
        error_msg = f"Fehler bei der Verarbeitung: {str(e)}"
        logging.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)