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
from typing import Any, Dict, List, Mapping, Optional, Iterable, cast
import re

# Laufzeitimport, um zyklische Imports zu vermeiden
settings: Any
try:
    from .settings import settings
except Exception:
    settings = None


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


# ---------------------- Eval-Post Normalizer (heuristics) ----------------------
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.\?\!])\s+")


def split_sentences(text: str) -> List[str]:
    try:
        parts = [p.strip() for p in _SENTENCE_SPLIT_RE.split(text) if p and p.strip()]
        return parts
    except Exception:
        return [text]


def trim_length(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip()


def limit_sentences(text: str, max_sentences: int) -> str:
    if max_sentences <= 0:
        return ""
    parts = split_sentences(text)
    return " ".join(parts[:max_sentences])


_ROLEPLAY_MARKERS = (
    "ich:", "du:", "wir:", "narrator:", "erzähler:", "spieler:", "gm:", "*", "[", "]"
)
_FILLERS = ("gern", "gerne", "natürlich", "klar", "sicher", "also", "übrigens", "ähm")


def _strip_roleplay_markers(t: str) -> str:
    # Entferne einfache Marker/Emotes/Aktionen, Klammerinhalte grob
    t = re.sub(r"\*[^*]*\*", " ", t)
    t = re.sub(r"\[[^\]]*\]", " ", t)
    # Markerpräfixe am Satzanfang
    t = re.sub(r"^(ich|du|wir|narrator|erzähler|spieler|gm)\s*:\s*", "", t, flags=re.IGNORECASE)
    return t


def _neutralize_pronouns(t: str) -> str:
    # Heuristische Neutralisierung: ich/du/wir -> neutraler Stil
    repls = [
        (r"\bich\b", ""),
        (r"\bdu\b", ""),
        (r"\bwir\b", ""),
        (r"\bdein(e|en|er|em)?\b", ""),
        (r"\bmein(e|en|er|em)?\b", ""),
        (r"\bunser(e|en|er|em)?\b", ""),
    ]
    for pat, rep in repls:
        t = re.sub(pat, rep, t, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", t).strip()


def _remove_exclamations_emojis(t: str) -> str:
    t = re.sub(r"[!]+", ".", t)
    # einfache Emoji/Emoticon-Entfernung
    t = re.sub(r"[:;]-?[\)\(DP]", "", t)
    t = re.sub(r"[\u2600-\u26FF\u2700-\u27BF\U0001F300-\U0001FAFF]", "", t)
    return t


def _strip_fillers(t: str) -> str:
    return re.sub(rf"^({'|'.join(_FILLERS)})[,!\.:]?\s+", "", t, flags=re.IGNORECASE)


def _compact_style(t: str) -> str:
    # Doppelungen/Leerzeichen reduzieren, Satzzeichen normalisieren
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\s*([,;:\.])\s*", r"\1 ", t)
    t = re.sub(r"\s+\.", ".", t)
    return t.strip()


def neutralize(text: str) -> str:
    t = text.strip()
    t = _strip_roleplay_markers(t)
    t = _remove_exclamations_emojis(t)
    # Füllfloskeln am Satzanfang entfernen (pro Satz)
    sentences = split_sentences(t)
    sentences = [_strip_fillers(s).strip() for s in sentences]
    t = " ".join(sentences)
    t = _neutralize_pronouns(t)
    return t


def compact(text: str) -> str:
    return _compact_style(text)


def _load_policy_file(path: str) -> Dict[str, Any]:
    try:
        import json
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _merge_terms(base: Iterable[str], overlay: Iterable[str]) -> List[str]:
    seen: Dict[str, None] = {}
    out: List[str] = []
    for term in list(base) + list(overlay):
        try:
            t = str(term)
        except Exception:
            continue
        if t and t not in seen:
            seen[t] = None
            out.append(t)
    return out


def _merge_rewrite_map(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {str(k): str(v) for k, v in dict(base).items()}
    for k, v in dict(overlay).items():
        out[str(k)] = str(v)
    return out


def _get_policies(*, mode: str = "default", profile_id: Optional[str] = None) -> Dict[str, Any]:
    # Standard: keine Regeln
    policies: Dict[str, Any] = {}
    if settings is None:
        return policies
    try:
        if getattr(settings, "POLICIES_ENABLED", False):
            path = getattr(settings, "POLICY_FILE", None)
            if isinstance(path, str) and path:
                file_rules = _load_policy_file(path)
                if not isinstance(file_rules, dict):
                    return {}
                # Unterstützt zwei Formen:
                # 1) Flach: { forbidden_terms, rewrite_map }
                # 2) Mit Profilen: { default: {...}, profiles: {<id>: {...}} }
                if "default" in file_rules or "profiles" in file_rules:
                    base_raw = file_rules.get("default")
                    profiles_raw = file_rules.get("profiles")
                    base: Dict[str, Any] = cast(Dict[str, Any], base_raw) if isinstance(base_raw, dict) else {}
                    profiles: Dict[str, Any] = cast(Dict[str, Any], profiles_raw) if isinstance(profiles_raw, dict) else {}
                    # Profilauflösung: explizite profile_id vorrangig, sonst Mapping aus mode (eval->eval)
                    pid: Optional[str] = profile_id or ("eval" if mode == "eval" else None)
                    ov_raw: Any = profiles.get(pid) if (pid and isinstance(profiles, dict)) else {}
                    overlay: Dict[str, Any] = cast(Dict[str, Any], ov_raw) if isinstance(ov_raw, dict) else {}
                    # Merge-Regeln: forbidden_terms vereinigen, rewrite_map overlay überschreibt
                    fb_raw = base.get("forbidden_terms")
                    fo_raw = overlay.get("forbidden_terms")
                    fb_list: List[Any] = cast(List[Any], fb_raw) if isinstance(fb_raw, list) else []
                    fo_list: List[Any] = cast(List[Any], fo_raw) if isinstance(fo_raw, list) else []
                    forb_base: List[str] = [str(x) for x in fb_list]
                    forb_overlay: List[str] = [str(x) for x in fo_list]
                    rb_raw = base.get("rewrite_map")
                    ro_raw = overlay.get("rewrite_map")
                    rw_base: Dict[str, Any] = cast(Dict[str, Any], rb_raw) if isinstance(rb_raw, dict) else {}
                    rw_overlay: Dict[str, Any] = cast(Dict[str, Any], ro_raw) if isinstance(ro_raw, dict) else {}
                    policies["forbidden_terms"] = _merge_terms(forb_base, forb_overlay)
                    policies["rewrite_map"] = _merge_rewrite_map(rw_base, rw_overlay)
                else:
                    # Flaches Schema
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
        rules = _get_policies(mode=mode, profile_id=profile_id)
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
        # Eval-spezifische Neutralisierung (schärferer Post-Hook)
        try:
            if mode == "eval" and getattr(settings, "EVAL_POST_REWRITE_ENABLED", True) and not _should_bypass_policies(unrestricted_mode=False):
                t0 = text
                t = neutralize(t0)
                try:
                    max_s = int(getattr(settings, "EVAL_POST_MAX_SENTENCES", 2))
                except Exception:
                    max_s = 2
                try:
                    max_c = int(getattr(settings, "EVAL_POST_MAX_CHARS", 240))
                except Exception:
                    max_c = 240
                t = limit_sentences(t, max_s)
                t = trim_length(t, max_c)
                t = compact(t)
                if t != t0:
                    return PostResult(action="rewrite", text=t, reason="eval_post")
                else:
                    return PostResult(action="allow")
        except Exception:
            # fail-open
            pass

        # Standard-Policy (Rewrite-Map/Forbidden Terms)
        rules = _get_policies(mode=mode, profile_id=profile_id)
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
    # Eval helpers
    "split_sentences",
    "trim_length",
    "limit_sentences",
    "neutralize",
    "compact",
    "PreResult",
    "PostResult",
]