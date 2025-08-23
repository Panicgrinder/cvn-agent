from __future__ import annotations
from typing import List, Optional, Dict, Any
import httpx
import os

from ..core.settings import settings
from ..api.models import ChatMessage, ChatResponse

async def generate_reply(messages: List[ChatMessage]) -> ChatResponse:
    """
    Sendet Nachrichten an die Ollama Chat API und gibt eine ChatResponse zurück.
    
    Args:
        messages: Eine Liste von ChatMessage-Objekten, die an das LLM gesendet werden sollen
        
    Returns:
        ChatResponse: Die Antwort des LLM, verpackt in ein ChatResponse-Objekt
    """
    url = f"{settings.OLLAMA_HOST}/api/chat"
    
    # Konvertiere unsere Messages in Ollama-Format
    ollama_msgs: List[Dict[str, str]] = [{"role": m.role, "content": m.content} for m in messages]

    payload: Dict[str, Any] = {
        "model": settings.MODEL_NAME,
        "messages": ollama_msgs,
        "stream": False,
    }
    
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Extrahiere den Modell-Text aus der Antwort
            try:
                content = response.json()["message"]["content"]
            except (KeyError, ValueError):
                # Fallback, falls die Struktur anders ist
                content = response.text
                
            return ChatResponse(content=content)
            
    except httpx.HTTPStatusError as e:
        error_msg = f"LLM HTTP-Fehler {e.response.status_code}: Bitte Ollama prüfen."
        return ChatResponse(content=error_msg)
        
    except httpx.RequestError:
        error_msg = f"Die Verbindung zum LLM ist fehlgeschlagen. Prüfe, ob Ollama läuft und {settings.MODEL_NAME} gepullt ist."
        return ChatResponse(content=error_msg)

def system_message(text: str) -> ChatMessage:
    """
    Hilfsfunktion zum Erstellen einer System-Nachricht.
    
    Args:
        text: Der Inhalt der System-Nachricht
        
    Returns:
        ChatMessage: Eine ChatMessage mit der Rolle "system"
    """
    return ChatMessage(role="system", content=text)

def get_llm_options() -> Dict[str, Any]:
    """
    Holt LLM-Einstellungen aus Umgebungsvariablen.
    
    Returns:
        Dictionary mit Einstellungen für das LLM
    """
    options: Dict[str, Any] = {}
    
    # Kontextgröße
    if "LLM_NUM_CTX" in os.environ:
        try:
            num_ctx = int(os.environ["LLM_NUM_CTX"])
            options["num_ctx"] = num_ctx
        except ValueError:
            pass
    
    # Temperatur
    if "LLM_TEMPERATURE" in os.environ:
        try:
            temperature = float(os.environ["LLM_TEMPERATURE"])
            options["temperature"] = temperature
        except ValueError:
            pass
    
    return options

async def generate_completion(prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
    """
    Generiert eine Antwort vom LLM-Service.
    
    Args:
        prompt: Der Prompt für das LLM
        options: Optionale Einstellungen für das LLM
        
    Returns:
        Die generierte Antwort
    """
    url = f"{settings.OLLAMA_HOST}/api/generate"
    
    # Merge default options mit den übergebenen Optionen
    payload: Dict[str, Any] = {
        "model": settings.MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    
    if options:
        payload.update(options)
    
    try:
        async with httpx.AsyncClient() as client:
            headers: Dict[str, str] = {"Content-Type": "application/json"}
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("response", "")
    except Exception as e:
        print(f"Fehler bei der Generierung: {str(e)}")
        return ""