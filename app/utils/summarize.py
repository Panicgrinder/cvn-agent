"""
Dieses Modul stellt Funktionen zur Zusammenfassung von Konversationen bereit.
"""

import re
from typing import Any, Callable, Dict, List, Optional


def extract_key_points(text: str, max_points: int = 5) -> List[str]:
    """
    Extrahiert wichtige Punkte aus einem Text mittels einfacher Heuristik.
    
    Args:
        text: Der zu analysierende Text
        max_points: Maximale Anzahl an Schlüsselpunkten
        
    Returns:
        Liste mit Schlüsselpunkten
    """
    # Einfache Heuristik: Sätze, die mit wichtigen Markern beginnen
    important_markers: List[str] = [
        r"wichtig ist,? dass",
        r"beachte,? dass",
        r"zu?sammenfassend",
        r"zusammen?gefasst",
        r"im ergebnis",
        r"schlussfolgernd",
        r"daher",
        r"deshalb",
        r"folglich",
        r"abschließend",
    ]
    
    # Teile den Text in Sätze
    sentences: List[str] = re.split(r'(?<=[.!?])\s+', text)
    
    # Identifiziere Sätze mit wichtigen Markern
    key_sentences: List[str] = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Prüfe auf wichtige Marker
        for marker in important_markers:
            if re.search(marker, sentence.lower()):
                key_sentences.append(sentence)
                break
    
    # Wenn nicht genug wichtige Sätze gefunden wurden, verwende die längsten Sätze
    if len(key_sentences) < max_points:
        # Sortiere Sätze nach Länge (längere zuerst), leere Sätze ignorieren
        remaining_sentences: List[str] = [s for s in sentences if s and s.strip() and s not in key_sentences]
        remaining_sentences.sort(key=len, reverse=True)
        
        # Füge die längsten Sätze hinzu, bis max_points erreicht ist
        key_sentences.extend(remaining_sentences[:max_points - len(key_sentences)])
    
    # Gekürzte Version verwenden, wenn die Sätze zu lang sind
    key_points: List[str] = []
    for sentence in key_sentences[:max_points]:
        # Kürze lange Sätze
        if len(sentence) > 100:
            shortened: str = sentence[:97] + "..."
        else:
            shortened = sentence
        key_points.append(shortened)
    
    return key_points


def create_simple_summary(messages: List[Dict[str, str]], response: str) -> str:
    """
    Erstellt eine einfache Zusammenfassung einer Konversation mittels Heuristik.
    
    Args:
        messages: Liste der Nachrichten
        response: Die Antwort des Assistenten
        
    Returns:
        Zusammenfassung als Text
    """
    # Extrahiere den letzten Nutzer-Input
    user_inputs: List[str] = [msg["content"] for msg in messages if msg["role"] == "user"]
    last_user_input: str = user_inputs[-1] if user_inputs else ""
    
    # Kürze die Eingabe, wenn sie zu lang ist
    if len(last_user_input) > 50:
        user_summary: str = last_user_input[:47] + "..."
    else:
        user_summary = last_user_input
    
    # Kürze die Antwort, wenn sie zu lang ist
    if len(response) > 100:
        response_summary: str = response[:97] + "..."
    else:
        response_summary = response
    
    # Einfache Zusammenfassung erstellen
    summary = f"Nutzer fragte nach '{user_summary}'. Antwort: '{response_summary}'"
    
    return summary


def summarize_turn(
    messages: List[Dict[str, str]],
    response: str,
    use_llm: bool = False,
    llm_function: Optional[Callable[[List[Dict[str, str]], str], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Fasst einen Konversations-Turn zusammen.
    
    Args:
        messages: Liste der Nachrichten in der Konversation
        response: Die Antwort des Assistenten
        use_llm: Ob ein LLM für die Zusammenfassung verwendet werden soll
        llm_function: Optional. Funktion, die ein LLM für komplexere Zusammenfassung aufruft
        
    Returns:
        Dictionary mit Zusammenfassung und Schlüsselpunkten
    """
    result: Dict[str, Any] = {}
    
    if use_llm and llm_function:
        # Platzhalter für zukünftige LLM-basierte Zusammenfassungen
        llm_result: Dict[str, Any] = llm_function(messages, response)
        result["summary"] = llm_result.get("summary", "")
        result["keyfacts"] = llm_result.get("keyfacts", [])
    else:
        # Einfache heuristische Zusammenfassung
        result["summary"] = create_simple_summary(messages, response)
        result["keyfacts"] = extract_key_points(response)
    
    return result


# Hier kann später eine LLM-basierte Zusammenfassungsfunktion implementiert werden
def llm_summarize(messages: List[Dict[str, str]], response: str) -> Dict[str, Any]:
    """
    Platzhalter für zukünftige LLM-basierte Zusammenfassung.
    
    Args:
        messages: Liste der Nachrichten
        response: Die Antwort des Assistenten
        
    Returns:
        Dictionary mit Zusammenfassung und Schlüsselpunkten
    """
    # TODO: Implementiere LLM-basierte Zusammenfassung
    # Dies würde z.B. einen Aufruf an generate_reply() mit einem speziellen Prompt beinhalten
    
    # Vorläufig als Fallback zur heuristischen Methode
    summary: str = create_simple_summary(messages, response)
    keyfacts: List[str] = extract_key_points(response)
    
    return {
        "summary": summary,
        "keyfacts": keyfacts
    }