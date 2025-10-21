"""
Dieses Modul stellt Funktionen zum Loggen von Konversationsdaten zur Verfügung.
Die Logs werden als JSONL-Dateien in data/logs/ gespeichert.
"""

import os
import json
import datetime
from utils.time_utils import now_iso
from typing import Dict, List, Optional, Any


def create_log_record(
    messages: List[Dict[str, str]],
    response: str,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    summary: Optional[str] = None,
    labels: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Erstellt einen Logeintrag für eine Konversation.
    
    Args:
        messages: Liste der Nachrichten in der Konversation (z.B. [{"role": "user", "content": "..."}, ...])
        response: Die Antwort des Modells
        tool_calls: Optionale Liste der ausgeführten Tool-Aufrufe
        summary: Optionale Zusammenfassung der Konversation
        labels: Optionale Kennzeichnungen/Labels für die Konversation
        
    Returns:
        Ein Dictionary mit dem Logeintrag
    """
    # Einheitlicher ISO-Zeitstempel (lokale Zeit, mit Offset falls gesetzt)
    timestamp = now_iso()
    
    log_record: Dict[str, Any] = {
        "timestamp": timestamp,
        "messages": messages,
        "response": response,
    }
    
    if tool_calls:
        log_record["tool_calls"] = tool_calls
    
    if summary:
        log_record["summary"] = summary
        
    if labels:
        log_record["labels"] = labels
    
    return log_record


def log_turn(data: Dict[str, Any]) -> None:
    """
    Loggt einen Konversations-Turn in eine JSONL-Datei.
    
    Die Datei wird im Format data/logs/YYYY-MM-DD.jsonl gespeichert.
    
    Args:
        data: Dictionary mit den zu loggenden Daten
    """
    # Stelle sicher, dass das Logs-Verzeichnis existiert
    log_dir = os.path.join("data", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Erstelle den Dateinamen basierend auf dem aktuellen Datum
    today = datetime.date.today()
    filename = f"{today.isoformat()}.jsonl"
    filepath = os.path.join(log_dir, filename)
    
    # Schreibe den Logeintrag in die Datei
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")