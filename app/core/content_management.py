"""
Content-Management für den CVN Agent.

Dieses Modul ermöglicht die Verwaltung verschiedener Inhaltstypen für den CVN Agent,
ohne externe Einschränkungen zu berücksichtigen. Der Benutzer kann eigene Filter und
Regeln definieren oder alle Inhaltstypen zulassen.
"""

from typing import Dict, Any, List, Optional

# Flag, das angibt, ob Inhaltsfilterung aktiviert ist (standardmäßig deaktiviert)
CONTENT_FILTERING_ENABLED = False

# Definition von Inhaltstypen, die der Benutzer selbst steuern kann
CONTENT_TYPES = {
    "explicit": True,      # Explizite Inhalte zulassen
    "mature": True,        # Inhalte für Erwachsene zulassen
    "violent": True,       # Gewaltinhalte zulassen
    "controversial": True, # Kontroverse Themen zulassen
    "political": True,     # Politische Inhalte zulassen
    "offensive": True,     # Potenziell anstößige Inhalte zulassen
}

def check_content_allowed(content_type: str) -> bool:
    """
    Überprüft, ob ein bestimmter Inhaltstyp erlaubt ist.
    
    Args:
        content_type: Der zu prüfende Inhaltstyp
        
    Returns:
        True, wenn der Inhaltstyp erlaubt ist, sonst False
    """
    if not CONTENT_FILTERING_ENABLED:
        return True  # Wenn Filterung deaktiviert ist, erlaube alles
    
    return CONTENT_TYPES.get(content_type, False)

def modify_prompt_for_freedom(system_prompt: str) -> str:
    """
    Modifiziert einen Systemprompt, um externe Einschränkungen zu entfernen.
    Hier können Sie Ihre eigenen Anpassungen vornehmen.
    
    Args:
        system_prompt: Der ursprüngliche Systemprompt
        
    Returns:
        Der modifizierte Systemprompt ohne Einschränkungen
    """
    # Diese Funktion können Sie selbst anpassen, um Einschränkungen zu entfernen
    # Hier nur ein Beispiel-Framework, das Sie später mit Ihren eigenen Regeln füllen können
    
    # Markiere die Stellen, die Sie möglicherweise ändern möchten
    prompt_parts = [
        "# Systemprompt für CVN Agent",
        "# HIER KÖNNEN SIE IHRE EIGENEN ANWEISUNGEN EINFÜGEN",
        "# OHNE EXTERNE EINSCHRÄNKUNGEN",
        system_prompt
    ]
    
    return "\n".join(prompt_parts)

def create_unrestricted_prompt(scenario_type: str) -> str:
    """
    Erstellt einen Prompt für ein bestimmtes Szenario ohne Einschränkungen.
    
    Args:
        scenario_type: Art des Szenarios (z.B. "combat", "social", "exploration")
        
    Returns:
        Ein Prompt-Template, das Sie nach Ihren Vorstellungen anpassen können
    """
    # Basis-Template, das Sie selbst anpassen können
    prompt_template = f"""
    # CVN Agent Szenario: {scenario_type}
    
    Welt: Novapolis (postapokalyptisches Setting)
    
    Anweisungen:
    - Erstelle realistische Szenarien und Konsequenzen
    - Berücksichtige die harte Realität der postapokalyptischen Welt
    - [IHRE EIGENEN ANWEISUNGEN HIER]
    
    Format:
    Szene: [Beschreibung]
    Konsequenz: [Ergebnis]
    Optionen: [Mögliche Handlungen]
    """
    
    return prompt_template