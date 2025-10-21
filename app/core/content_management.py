"""
Content-Management und einfache Policy-Engine für den CVN Agent.

Dieses Modul enthält:
- Ein einfaches Framework für frei konfigurierbare Inhaltstypen
- Optionale Policy-Hooks (Pre/Post), die eingehende Nachrichten modifizieren oder blockieren

Die Policy-Engine ist bewusst minimal gehalten und standardmäßig abgeschaltet, um
keine Verhaltensänderung zu verursachen. Falls aktiviert, können Regeln aus einer
optionalen JSON-Datei geladen werden. Beispielstruktur:

{
    "forbidden_terms": ["verbot", "blockiere"],
    "rewrite_map": {"schlecht": "gut"}
}

Semantik:
- apply_pre(messages):
        - Sucht nach verbotenen Begriffen (forbidden_terms) in Nutzer-Nachrichten (role=="user").
            Wenn gefunden, blockiert sie oder – falls rewrite_map passt – ersetzt Begriffe.
        - Gibt ein Ergebnis mit action in {"allow","rewrite","block"} und ggf. messages zurück.
- apply_post(text):
        - Optionales Nachbearbeiten des Modell-Outputs (einfaches Suchen/Ersetzen per rewrite_map).
        - Gibt action und ggf. text zurück.

Edge-Cases:
- Fehler in der Policy-Verarbeitung führen zu action="allow" (fail-open).
- Bei "unrestricted"-Modus und Einstellung POLICY_STRICT_UNRESTRICTED_BYPASS=True werden Policies übersprungen.
"""


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

# ---------------------------------------------------------------------------
# Einfache Policy-Engine (optional)
# ---------------------------------------------------------------------------
from typing import Any, Dict, List, Mapping, Optional

try:
    # Laufzeitimport, um zyklische Imports zu vermeiden
    from .settings import settings  # type: ignore
except Exception:
    settings = None  # type: ignore


class PreResult:
    def __init__(self, action: str = "allow", messages: Optional[List[Dict[str, str]]] = None, reason: Optional[str] = None):
        self.action = action  # allow | rewrite | block
        self.messages = messages
        self.reason = reason


class PostResult:
    def __init__(self, action: str = "allow", text: Optional[str] = None, reason: Optional[str] = None):
        self.action = action  # allow | rewrite | block
        self.text = text
        self.reason = reason


def _load_policy_file(path: str) -> Dict[str, Any]:
    try:
        import json
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _get_policies() -> Dict[str, Any]:
    # Standard: keine Regeln
    policies: Dict[str, Any] = {}
    if settings is None:
        return policies
    try:
        if getattr(settings, "POLICIES_ENABLED", False):
            path = getattr(settings, "POLICY_FILE", None)
            if isinstance(path, str) and path:
                file_rules = _load_policy_file(path)
                if isinstance(file_rules, dict):
                    policies.update(file_rules)
    except Exception:
        # fail-open, keine Regeln
        return {}
    return policies


def _should_bypass_policies(unrestricted_mode: bool) -> bool:
    try:
        if settings is None:
            return False
        if unrestricted_mode and getattr(settings, "POLICY_STRICT_UNRESTRICTED_BYPASS", True):
            return True
    except Exception:
        pass
    return False


def apply_pre(
    messages: List[Mapping[str, Any]],
    *,
    mode: str = "default",  # "default" | "eval" | "unrestricted"
    profile_id: Optional[str] = None,
) -> PreResult:
    """
    Pre-Hook für eingehende Nachrichten. Kann Nachrichten umschreiben oder blockieren.
    Fail-open: Bei Fehlern wird allow zurückgegeben.
    """
    # Bypass in unrestricted
    if _should_bypass_policies(unrestricted_mode=(mode == "unrestricted")):
        return PreResult(action="allow")
    # Nur wenn Policies aktiviert
    if settings is None or not getattr(settings, "POLICIES_ENABLED", False):
        return PreResult(action="allow")
    try:
        rules = _get_policies()
        forb: List[str] = [str(x) for x in rules.get("forbidden_terms", []) if isinstance(x, str)]
        rw_map: Dict[str, str] = {str(k): str(v) for k, v in dict(rules.get("rewrite_map", {})).items()}
        changed = False
        new_msgs: List[Dict[str, str]] = []
        for m in messages:
            role = str(m.get("role", "user"))
            content = str(m.get("content", ""))
            if role == "user":
                # Wenn verbotene Begriffe vorhanden, zunächst versuchen zu ersetzen
                for bad, good in rw_map.items():
                    if bad in content:
                        content = content.replace(bad, good)
                        changed = True
                # Danach prüfen, ob weiterhin verbotene Begriffe vorhanden sind
                if any(term for term in forb if term and term in content):
                    # Blockieren (kein automatisches Umschreiben mehr möglich)
                    return PreResult(action="block", reason="forbidden_term")
            new_msgs.append({"role": role, "content": content})
        if changed:
            return PreResult(action="rewrite", messages=new_msgs, reason="rewrite_map_applied")
        return PreResult(action="allow")
    except Exception:
        return PreResult(action="allow")


def apply_post(
    text: str,
    *,
    mode: str = "default",
    profile_id: Optional[str] = None,
) -> PostResult:
    """
    Post-Hook für Modell-Output. Kann Text umschreiben oder blockieren.
    Fail-open: Bei Fehlern wird allow zurückgegeben.
    """
    if _should_bypass_policies(unrestricted_mode=(mode == "unrestricted")):
        return PostResult(action="allow")
    if settings is None or not getattr(settings, "POLICIES_ENABLED", False):
        return PostResult(action="allow")
    try:
        rules = _get_policies()
        forb: List[str] = [str(x) for x in rules.get("forbidden_terms", []) if isinstance(x, str)]
        rw_map: Dict[str, str] = {str(k): str(v) for k, v in dict(rules.get("rewrite_map", {})).items()}
        out = text
        changed = False
        for bad, good in rw_map.items():
            if bad in out:
                out = out.replace(bad, good)
                changed = True
        if any(term for term in forb if term and term in out):
            return PostResult(action="block", reason="forbidden_term")
        if changed:
            return PostResult(action="rewrite", text=out, reason="rewrite_map_applied")
        return PostResult(action="allow")
    except Exception:
        return PostResult(action="allow")


__all__ = [
    "check_content_allowed",
    "modify_prompt_for_freedom",
    "create_unrestricted_prompt",
    # Policy-API
    "apply_pre",
    "apply_post",
    "PreResult",
    "PostResult",
]