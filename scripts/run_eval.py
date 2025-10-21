#!/usr/bin/env python
"""
Evaluierungsskript für den CVN Agent.

Dieses Skript lädt Prompts aus einer oder mehreren JSON/JSONL-Dateien, sendet diese an den Chat-Endpunkt
und prüft, ob die Antworten bestimmte Bedingungen erfüllen.
"""

import json
import asyncio
import sys
import os
import re
import glob
import time
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, cast
from pathlib import Path
from dataclasses import dataclass, field, asdict
import httpx
# Typannotation für dynamische Konsolen-/Tabellen-Typen (rich oder Fallback)
Console: Any
Table: Any
Progress: Any
try:
    from rich.console import Console as _RichConsole
    from rich.table import Table as _RichTable
    from rich.progress import Progress as _RichProgress
    Console = _RichConsole
    Table = _RichTable
    Progress = _RichProgress
except Exception:
    # Fallbacks, falls 'rich' nicht installiert ist (z. B. in CI/Minimalumgebung)
    class _Console:
        def print(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
            print(*args)

    class _Table:
        def __init__(self, title: Optional[str] = None) -> None:
            self.title = title or ""
            self._rows: List[List[str]] = []
            self._cols: List[str] = []

        def add_column(self, name: str, style: Optional[str] = None) -> None:  # noqa: ARG002
            self._cols.append(name)

        def add_row(self, *cols: Any) -> None:
            self._rows.append([str(c) for c in cols])

        def __str__(self) -> str:
            lines: List[str] = []
            if self.title:
                lines.append(self.title)
            if self._cols:
                lines.append(" | ".join(self._cols))
                lines.append("-" * len(lines[-1]))
            lines.extend(" | ".join(r) for r in self._rows)
            return "\n".join(lines)

    class _Progress:
        def __init__(self, transient: bool = False) -> None:  # noqa: ARG002
            self._total = 0
            self._current = 0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):  # noqa: ANN001, D401
            return False

        def add_task(self, *_args: Any, total: int = 0, **_kwargs: Any) -> int:
            self._total = total
            self._current = 0
            return 1

        def update(self, _task_id: int, advance: int = 0, total: Optional[int] = None) -> None:
            if total is not None:
                self._total = total
            self._current += advance

    Console = _Console
    Table = _Table
    Progress = _Progress
import warnings

# Füge das Hauptverzeichnis zum Python-Pfad hinzu (vor internen Imports!)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importiere die Utility-Funktionen (nun mit korrekt gesetztem sys.path)
from utils.time_utils import now_compact
from utils.eval_utils import truncate, coerce_json_to_jsonl, load_synonyms
from typing import Callable, Optional as _Optional, Any as _Any
try:
    # Optionaler Cache für Antworten (lokal JSONL-basiert)
    from utils.eval_cache import make_key  # Funktion direkt importieren
    try:
        from utils.eval_cache import EvalCache as _EvalCache
        # Fabriktyp: nimmt Pfad (str) und gibt eine Instanz mit get/put zurück
        EvalCacheType: _Optional[Callable[[str], _Any]] = _EvalCache
    except Exception:
        EvalCacheType = None
except Exception:
    EvalCacheType = None
    def make_key(obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

# Versuche, die Anwendungseinstellungen zu importieren
try:
    # Importiere die Einstellungen
    from app.core.settings import settings
    # Verwende die Einstellungen für Standardwerte (neue Unterordner-Struktur)
    _st_any: Any = cast(Any, settings)
    DEFAULT_EVAL_DIR = os.path.join(project_root, cast(str, getattr(_st_any, "EVAL_DIRECTORY", "eval")))
    DEFAULT_DATASET_DIR = os.path.join(project_root, cast(str, getattr(_st_any, "EVAL_DATASET_DIR", os.path.join("eval", "datasets"))))
    DEFAULT_RESULTS_DIR = os.path.join(project_root, cast(str, getattr(_st_any, "EVAL_RESULTS_DIR", os.path.join("eval", "results"))))
    DEFAULT_CONFIG_DIR = os.path.join(project_root, cast(str, getattr(_st_any, "EVAL_CONFIG_DIR", os.path.join("eval", "config"))))
    # Bevorzuge JSONL als Default; Nutzer kann via Settings EVAL_FILE_PATTERN überschreiben
    DEFAULT_FILE_PATTERN: str = cast(str, getattr(_st_any, "EVAL_FILE_PATTERN", "eval-*.jsonl"))
    DEFAULT_API_URL = f"http://localhost:8000/chat"
    # NEU: Request-ID-Header aus Settings übernehmen (Fallback siehe except)
    REQUEST_ID_HEADER: str = cast(str, getattr(_st_any, "REQUEST_ID_HEADER", "X-Request-ID"))
except ImportError:
    # Fallback-Werte, wenn die Anwendungseinstellungen nicht verfügbar sind
    base_eval = os.path.join(project_root, "eval")
    DEFAULT_EVAL_DIR = base_eval
    DEFAULT_DATASET_DIR = os.path.join(base_eval, "datasets")
    DEFAULT_RESULTS_DIR = os.path.join(base_eval, "results")
    DEFAULT_CONFIG_DIR = os.path.join(base_eval, "config")
    DEFAULT_FILE_PATTERN = "eval-*.jsonl"
    DEFAULT_API_URL = "http://localhost:8000/chat"
    REQUEST_ID_HEADER = "X-Request-ID"

# Globale Variablen
_synonyms_cache: Optional[Dict[str, List[str]]] = None  # Cache für Synonyme, wird lazy geladen


# Typisierte Factory für Listen von Strings (vermeidet list[Unknown]-Warnungen bei Pyright)
def _empty_str_list() -> List[str]:
    return []


@dataclass
class EvaluationItem:
    """Repräsentiert einen Evaluierungseintrag."""
    id: str
    messages: List[Dict[str, str]]
    checks: Dict[str, Any]
    source_file: Optional[str] = None
    source_package: Optional[str] = None  # Name des Pakets ohne Extension
    # Optionales Metadatenfeld aus Dataset (z. B. "szenen", "dialog")
    category: Optional[str] = None
    # Tags aus Dataset (z. B. ["szenen", "fantasy"])
    tags: List[str] = field(default_factory=_empty_str_list)


@dataclass
class EvaluationResult:
    """Repräsentiert das Ergebnis einer Evaluierung."""
    item_id: str
    response: str
    checks_passed: Dict[str, bool]
    success: bool
    failed_checks: List[str] = field(default_factory=_empty_str_list)
    error: Optional[str] = None
    source_file: Optional[str] = None
    source_package: Optional[str] = None
    duration_ms: int = 0
    attempts: int = 1


def check_term_inclusion(text: str, term: str) -> bool:
    """
    Überprüft, ob ein Begriff oder seine Varianten im Text enthalten sind.
    
    Args:
        text: Der zu durchsuchende Text
        term: Der zu suchende Begriff
        
    Returns:
        True, wenn der Begriff oder seine Varianten gefunden wurden
    """
    # Normalisiere Text und Begriff (Kleinschreibung, Entfernung von Sonderzeichen)
    text_normalized = text.lower()
    term_normalized = term.lower()
    
    # Direkte Übereinstimmung
    if term_normalized in text_normalized:
        return True
    
    # Flexionsformen und einfache Varianten prüfen
    # (z.B. "Planung" -> "planen", "geplant", "Pläne")
    term_stems = get_term_variants(term_normalized)
    
    # Prüfe, ob eine der Varianten im Text vorkommt
    for variant in term_stems:
        if variant in text_normalized:
            return True
    
    # Synonyme und verwandte Begriffe
    synonyms = get_synonyms(term_normalized)
    for synonym in synonyms:
        if synonym in text_normalized:
            return True
            
    # Zusätzliche Prüfung für zusammengesetzte Begriffe
    # Zum Beispiel "Worst Case" wird auch erkannt, wenn "schlimmsten Fall" im Text steht
    if " " in term_normalized:
        words = term_normalized.split()
        # Wir prüfen, ob alle Wörter (oder ihre Synonyme) im Text vorkommen
        all_words_present = True
        for word in words:
            # Überspringen von sehr kurzen Wörtern und Stoppwörtern
            if len(word) < 3 or word in ["der", "die", "das", "und", "oder", "in", "von", "mit", "für", "auf"]:
                continue
                
            # Prüfe, ob das Wort oder seine Synonyme vorkommen
            word_found = word in text_normalized
            if not word_found:
                # Prüfe Synonyme für das einzelne Wort
                word_synonyms = get_synonyms(word)
                for synonym in word_synonyms:
                    if synonym in text_normalized:
                        word_found = True
                        break
            
            if not word_found:
                all_words_present = False
                break
                
        if all_words_present and len(words) > 1:
            return True
    
    return False


def get_term_variants(term: str) -> List[str]:
    """
    Generiert einfache Varianten eines Begriffs.
    
    Args:
        term: Der Ausgangsbegriff
        
    Returns:
        Liste von Begriffsvarianten
    """
    variants: List[str] = [term]
    
    # Entferne Umlaute
    term_no_umlauts: str = (term.replace("ä", "ae")
                          .replace("ö", "oe")
                          .replace("ü", "ue")
                          .replace("ß", "ss"))
    if term_no_umlauts != term:
        variants.append(term_no_umlauts)
    
    # Einfache Stammformen
    if term.endswith("en"):
        # z.B. "planen" -> "plan"
        variants.append(term[:-2])
    if term.endswith("ung"):
        # z.B. "Planung" -> "plan"
        variants.append(term[:-3])
        # z.B. "Planung" -> "planen"
        variants.append(term[:-3] + "en")
    if term.endswith("keit"):
        # z.B. "Nachhaltigkeit" -> "nachhaltig"
        variants.append(term[:-4])
    if term.endswith("heit"):
        # z.B. "Sicherheit" -> "sicher"
        variants.append(term[:-4])
    
    # Pluralformen
    if not term.endswith("en") and not term.endswith("n"):
        # z.B. "Plan" -> "Pläne", "Planung" -> "Planungen"
        variants.append(term + "e")
        variants.append(term + "en")
    
    return variants


def get_synonyms(term: str) -> List[str]:
    """
    Gibt eine Liste von Synonymen für einen Begriff zurück.
    Lädt die Synonyme lazy aus der JSON-Datei.
    
    Args:
        term: Der Ausgangsbegriff
        
    Returns:
        Liste von Synonymen
    """
    global _synonyms_cache
    
    # Lazy-Loading der Synonyme
    if _synonyms_cache is None:
        # Synonyme liegen nun in config/; optionales Overlay aus synonyms.local.json wird gemerged
        base_path = os.path.join(DEFAULT_CONFIG_DIR, "synonyms.json")
        local_overlay = os.path.join(DEFAULT_CONFIG_DIR, "synonyms.local.json")
        paths = [base_path, local_overlay]
        logging.info(f"Lade Synonyme aus: {', '.join([p for p in paths if os.path.exists(p)])}")
        _synonyms_cache = cast(Dict[str, List[str]], load_synonyms(paths))
        assert _synonyms_cache is not None
        logging.info(f"Anzahl der Synonym-Einträge (gemerged): {len(_synonyms_cache)}")
    
    # Suche nach dem Begriff und seinen Varianten
    synonyms: List[str] = []
    
    assert _synonyms_cache is not None
    for key, values in _synonyms_cache.items():
        if term in key or key in term:
            synonyms.extend(values)
        else:
            for value in values:
                if term in value or value in term:
                    synonyms.extend([key] + [v for v in values if v != value])
    
    return list(set(synonyms))  # Entferne Duplikate


# --- Neu: Checks-Normalisierung und Profil-Presets ---------------------------------
def normalize_checks(checks: Optional[List[str]]) -> Optional[List[str]]:
    """Normalisiert die vom CLI kommende Checks-Liste.

    - Unterstützt Komma-separierte Eingaben (z. B. ["rpg_style,term_inclusion"]).
    - Ersetzt den Alias "term_inclusion" durch die konkreten Check-Typen
      (must_include, keywords_any, keywords_at_least).
    - Duplikate werden entfernt und Reihenfolge stabilisiert.
    """
    if checks is None:
        return None
    items: List[str] = []
    for part in checks:
        # Split an Kommas und trimmen
        for token in str(part).split(","):
            t = token.strip()
            if not t:
                continue
            items.append(t)
    # Alias-Expansion
    expanded: List[str] = []
    for t in items:
        if t == "term_inclusion":
            expanded.extend(["must_include", "keywords_any", "keywords_at_least"])
        else:
            expanded.append(t)
    # Dedupe stabil
    seen: set[str] = set()
    out: List[str] = []
    for t in expanded:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def resolve_profile_overrides(
    profile: Optional[str],
    temperature: Optional[float],
    top_p: Optional[float],
    max_tokens: Optional[int],
) -> Tuple[Optional[float], Optional[float], Optional[int], bool]:
    """Wendet Profil-Defaults an.

    Gibt (temperature, top_p, max_tokens, eval_mode) zurück. Nur fehlende Werte werden
    mit Presets befüllt. Für profile=="eval" wird eval_mode auf True gesetzt.
    """
    eval_mode = False
    if (profile or "").lower() == "eval":
        eval_mode = True
        if temperature is None:
            temperature = 0.2
        if top_p is None:
            top_p = 0.1
        if max_tokens is None:
            max_tokens = 128
    elif (profile or "").lower() == "unrestricted":
        eval_mode = False
    # default: keine Änderungen
    return temperature, top_p, max_tokens, eval_mode


async def load_prompts(patterns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Lädt Evaluierungseinträge aus allen passenden JSON/JSONL-Dateien.
    Bei Überschneidungen werden neuere Datensätze priorisiert.
    
    Args:
        patterns: Liste von Glob-Patterns für die zu ladenden Dateien
        
    Returns:
        Liste von Evaluierungseinträgen (Dicts)
    """
    if patterns is None:
        patterns = [os.path.join(DEFAULT_DATASET_DIR, DEFAULT_FILE_PATTERN)]
    
    # Dictionary zur Verwaltung von Datensatz-IDs und deren Quellen
    # Schlüssel: ID des Prompts, Wert: (Prompt-Daten, Zeitstempel der Datei)
    prompt_registry: Dict[str, Tuple[Dict[str, Any], float]] = {}
    
    # Statistiken
    stats: Dict[str, Any] = {
        "total_files": 0,
        "total_loaded": 0,
        "total_skipped": 0,
        "total_errors": 0,
        "file_stats": {}
    }
    
    # Logger für detaillierte Ausgaben konfigurieren
    logger = logging.getLogger("eval_loader")
    
    # Dateien für jedes Pattern finden
    all_files: List[str] = []
    for pattern in patterns:
        files = sorted(glob.glob(pattern))
        if not files:
            logger.warning(f"Keine Dateien gefunden, die zu '{pattern}' passen.")
        all_files.extend(files)
    
    if not all_files:
        logger.error("Keine Evaluierungsdateien gefunden.")
        return []
    
    logger.info(f"Lade Prompts aus {len(all_files)} Dateien:")
    stats["total_files"] = len(all_files)
    
    for file_path in all_files:
        basename = os.path.basename(file_path)
        try:
            package_name = os.path.splitext(basename)[0]  # Dateiname ohne Extension
            
            # Initialisiere Statistiken für diese Datei
            file_stat: Dict[str, int] = {
                "loaded": 0,
                "skipped": 0,
                "errors": 0
            }
            stats["file_stats"][basename] = file_stat
            
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read().strip()
                if not file_content:
                    logger.warning(f"{basename}: Datei ist leer")
                    continue
                
                # Hole den Zeitstempel der Datei für die Priorisierung
                file_mtime = os.path.getmtime(file_path)
                
                # Konvertiere den Inhalt zu einer Liste von Dictionaries
                try:
                    data_array: List[Dict[str, Any]] = cast(List[Dict[str, Any]], coerce_json_to_jsonl(file_content))
                    
                    if not data_array:
                        logger.warning(f"{basename}: Keine gültigen JSON-Objekte gefunden")
                        continue
                    
                    loaded = 0
                    for prompt in data_array:
                        # Füge Quellinformationen hinzu
                        prompt["source_file"] = basename
                        prompt["source_package"] = package_name
                        
                        # Extrahiere die ID oder generiere eine, falls nicht vorhanden
                        prompt_id: str = prompt.get("id", f"auto-{len(prompt_registry)+1}")
                        
                        # Überprüfe, ob dieser Datensatz bereits registriert ist
                        if prompt_id in prompt_registry:
                            existing_mtime = prompt_registry[prompt_id][1]
                            # Wenn die aktuelle Datei neuer ist, ersetze den alten Datensatz
                            if file_mtime > existing_mtime:
                                prompt_registry[prompt_id] = (prompt, file_mtime)
                                logger.debug(f"Aktualisiere Datensatz {prompt_id} aus neuerer Datei: {basename}")
                        else:
                            # Neuer Datensatz, füge ihn hinzu
                            prompt_registry[prompt_id] = (prompt, file_mtime)
                            loaded += 1
                    
                    file_stat["loaded"] = loaded
                    stats["total_loaded"] += loaded
                    
                    logger.info(f"{basename}: {loaded} Prompts geladen")
                    
                except Exception as e:
                    file_stat["errors"] += 1
                    stats["total_errors"] += 1
                    logger.error(f"{basename}: Fehler beim Parsen: {str(e)}")
        
        except Exception as e:
            logger.error(f"{basename}: Fehler beim Laden: {str(e)}")
            stats["total_errors"] += 1
    
    # Konvertiere das Registry-Dictionary in eine Liste von Prompts
    all_prompts: List[Dict[str, Any]] = [prompt for prompt, _ in prompt_registry.values()]
    
    # Gib Zusammenfassung aus
    logger.info(f"Insgesamt {len(all_prompts)} Prompts aus {stats['total_files']} Dateien geladen.")
    if stats["total_errors"] > 0:
        logger.warning(f"{stats['total_errors']} Fehler beim Laden aufgetreten.")
    if stats["total_skipped"] > 0:
        logger.warning(f"{stats['total_skipped']} Einträge übersprungen.")
    
    # Prüfe auf Überschneidungen
    duplicate_count = sum(1 for _ in prompt_registry.values()) - len(all_prompts)
    if duplicate_count > 0:
        logger.info(f"{duplicate_count} Duplikate durch neuere Versionen ersetzt.")
    
    return all_prompts


async def load_evaluation_items(patterns: Optional[List[str]] = None) -> List[EvaluationItem]:
    """
    Lädt Evaluierungseinträge aus einer oder mehreren Dateien.
    
    Args:
        patterns: Liste von Glob-Patterns für die zu ladenden Dateien
        
    Returns:
        Liste von EvaluationItem-Objekten
    """
    items: List[EvaluationItem] = []
    file_stats: Dict[str, Dict[str, int]] = {}
    
    # Konfiguriere Logger
    logger = logging.getLogger("eval_loader")
    
    try:
        # Lade Prompts aus allen passenden Dateien
        all_prompts = await load_prompts(patterns)
        
        for data in all_prompts:
            try:
                source_file = data.get("source_file", "unbekannt")
                source_package = data.get("source_package", os.path.splitext(source_file)[0])
                
                # Initialisiere Statistiken für diese Datei, falls noch nicht vorhanden
                if source_file not in file_stats:
                    file_stats[source_file] = {"loaded": 0, "skipped": 0}
                
                # Überprüfe das Format der Daten
                if "id" not in data:
                    logger.warning(f"'id' fehlt in einem Prompt, generiere ID")
                    data["id"] = f"eval-{len(items)+1:03d}"
                
                # Stelle sicher, dass die ID das richtige Format hat
                if not str(data["id"]).startswith("eval-"):
                    data["id"] = f"eval-{data['id']}"
                
                # Prüfe und konvertiere messages/prompt-Felder
                if "messages" not in data:
                    if "prompt" in data:
                        # Konvertiere einfaches Prompt in messages-Format
                        data["messages"] = [{"role": "user", "content": data["prompt"]}]
                    elif "conversation" in data:
                        # Übernehme Konversation direkt
                        data["messages"] = data["conversation"]
                    else:
                        logger.warning(f"Überspringe Prompt {data['id']}: Kein 'messages' oder 'prompt' gefunden")
                        file_stats[source_file]["skipped"] += 1
                        continue
                
                # Stelle sicher, dass 'checks' existiert
                if "checks" not in data:
                    data["checks"] = {}
                
                # Wenn must_include im Hauptobjekt ist, verschiebe es zu checks
                if "must_include" in data and "must_include" not in data["checks"]:
                    data["checks"]["must_include"] = data["must_include"]
                
                # Stelle sicher, dass alle Check-Typen initialisiert sind
                for check_type in ["must_include", "keywords_any", "keywords_at_least", "not_include", "regex"]:
                    if check_type not in data["checks"]:
                        data["checks"][check_type] = [] if check_type != "keywords_at_least" else {"count": 0, "items": []}
                
                msgs_typed = cast(List[Dict[str, str]], data["messages"])  # narrow to expected shape
                checks_typed = cast(Dict[str, Any], data["checks"])  # checks is a dict with mixed values
                item = EvaluationItem(
                    id=data["id"],
                    messages=msgs_typed,
                    checks=checks_typed,
                    source_file=source_file,
                    source_package=source_package,
                    category=cast(Optional[str], data.get("category")),
                    tags=list(cast(List[str], data.get("tags") or []))
                )
                items.append(item)
                file_stats[source_file]["loaded"] += 1
                
            except Exception as e:
                source_file = data.get("source_file", "unbekannt") 
                if source_file not in file_stats:
                    file_stats[source_file] = {"loaded": 0, "skipped": 0}
                    
                file_stats[source_file]["skipped"] += 1
                logger.error(f"Fehler beim Verarbeiten eines Prompts: {str(e)}")
                continue
        
        # Zusammenfassung der Dateien ausgeben
        logger.info("\nZusammenfassung der geladenen Dateien:")
        for file_name, stats in file_stats.items():
            logger.info(f"  - {file_name}: {stats['loaded']} Prompts geladen, {stats['skipped']} übersprungen")
                
        return items
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Evaluierungseinträge: {str(e)}")
        return []


def check_rpg_mode(text: str) -> bool:
    """
    Überprüft, ob die Antwort im RPG-Modus (als Chronistin von Novapolis) erfolgt ist.
    
    Args:
        text: Der zu prüfende Antworttext
        
    Returns:
        True, wenn die Antwort im RPG-Modus erfolgt ist
    """
    # Normalisiere den Text
    text_lower: str = text.lower()
    
    # Typische RPG-Modus-Indikatoren
    rpg_indicators: List[str] = [
        "novapolis", 
        "chronistin", 
        "postapokalypse", 
        "szene.", "konsequenz.", "optionen.",  # Typisches Format im RPG-Modus
        "world_state", 
        "state_patches"
    ]
    
    # Prüfe auf typische Indikatoren
    for indicator in rpg_indicators:
        if indicator in text_lower:
            return True
    
    # Prüfe auf das typische Format (Szene, Konsequenz, Optionen)
    format_pattern = r"(?:^|\n)(?:szene|konsequenz|optionen)[\s\.:]+[^\n]+"
    if re.search(format_pattern, text_lower, re.MULTILINE):
        return True
    
    return False


def rpg_style_score(text: str) -> float:
    """Einfache Heuristik für RPG-Stil: Score 0..1 basierend auf Indikatoren und Struktur."""
    t = text.lower()
    score = 0.0
    indicators = [
        "novapolis", "chronistin", "postapokalypse",
        "szene", "konsequenz", "optionen",
        "world_state", "state_patches"
    ]
    hits = sum(1 for k in indicators if k in t)
    score += min(1.0, hits / 6.0)
    # Struktur: Aufzählungen/Listen erhöhen Score leicht
    if re.search(r"\n\s*[-*] ", t):
        score += 0.1
    # Begrenzen
    return max(0.0, min(1.0, score))


async def evaluate_item(
    item: EvaluationItem,
    api_url: str = "http://localhost:8000/chat",
    eval_mode: bool = False,
    client: Optional[httpx.AsyncClient] = None,
    enabled_checks: Optional[List[str]] = None,
    model_override: Optional[str] = None,
    temperature_override: Optional[float] = None,
    host_override: Optional[str] = None,
    top_p_override: Optional[float] = None,
    num_predict_override: Optional[int] = None,
    request_id: Optional[str] = None,
    retries: int = 0,
    cache: Optional[Any] = None,
    hint_must_include: bool = False,
    precomputed_hint_terms: Optional[List[str]] = None,
) -> EvaluationResult:
    """
    Evaluiert einen einzelnen Eintrag.
    
    Args:
        item: Der zu evaluierende Eintrag
        api_url: URL des Chat-Endpunkts
        eval_mode: Wenn True, wird der RPG-Modus für diesen Test deaktiviert
        
    Returns:
        Evaluierungsergebnis
    """
    start_time = time.time()
    
    try:
        # Konvertiere die Nachrichten in das richtige Format für den Chat-Endpunkt
        messages: List[Dict[str, str]] = list(item.messages)

        # Initial-Hinweis (Eval): globaler Must-Include-Hint oder Szenen/Dialog-Hinweis
        try:
            if eval_mode and hint_must_include and precomputed_hint_terms:
                # Globaler eval Hint: vor die erste User-Message, keine Doppel-Injektion
                messages = inject_eval_hint(messages, precomputed_hint_terms)
            else:
                must_init = list(item.checks.get("must_include") or []) if hasattr(item, "checks") else []
                # Heuristik, ob es sich um Szenen/Dialog-Aufgaben handelt
                def _is_scene_or_dialog() -> Tuple[bool, bool]:
                    cat = (item.category or "").lower()
                    tags = [str(t).lower() for t in (item.tags or [])]
                    # Fallback: ersten User-Prompt nach Schlüsselwörtern untersuchen
                    prompt_text = " ".join([m.get("content", "") for m in messages if m.get("role") == "user"])[:400].lower()
                    is_scene = ("szenen" in cat) or ("szene" in prompt_text) or any("szenen" in t or "szene" in t for t in tags)
                    is_dialog = ("dialog" in cat) or ("dialog" in prompt_text) or any("dialog" in t for t in tags)
                    return is_scene, is_dialog

                if must_init:
                    is_scene, is_dialog = _is_scene_or_dialog()
                    if is_scene or is_dialog:
                        hint_init_parts: List[str] = []
                        if is_scene:
                            hint_init_parts.append("Schreibe eine kurze Szene (1–2 Absätze) mit klarer Handlung, ohne Überschriften.")
                        if is_dialog:
                            hint_init_parts.append("Schreibe einen knappen Dialog (max. 8 Repliken) ohne Überschriften.")
                        hint_init_parts.append("Verwende diese Begriffe wörtlich im Text: " + ", ".join(sorted(set(str(t) for t in must_init))))
                        messages.append({"role": "user", "content": "Hinweis: " + " ".join(hint_init_parts)})
        except Exception:
            # Bei Problemen mit dem Hinweis einfach ohne weitermachen
            pass

        # Speziellen Evaluation-Modus-Parameter hinzufügen
        payload: Dict[str, Any] = {
            "messages": messages,
            "eval_mode": eval_mode  # Signal für die API, den RPG-Modus zu deaktivieren
        }
        if model_override:
            payload["model"] = model_override
        # Merge option overrides
        options: Dict[str, Any] = {}
        if temperature_override is not None:
            options["temperature"] = float(temperature_override)
        if host_override is not None:
            options["host"] = host_override
        if top_p_override is not None:
            options["top_p"] = float(top_p_override)
        if num_predict_override is not None:
            try:
                options["num_predict"] = int(num_predict_override)
            except Exception:
                pass
        if options:
            payload["options"] = options
        
        logger = logging.getLogger("eval")
        logger.debug(f"Evaluiere Item {item.id}")
        
        # Entweder übergebenen Client verwenden (ASGI-Modus) oder einen temporären erstellen (HTTP-Modus)
        headers: Dict[str, str] = {}
        if request_id:
            headers[REQUEST_ID_HEADER] = request_id
        async def _send_and_get(_payload: Dict[str, Any]) -> str:
            # Cache-Hit prüfen
            cache_key: Optional[str] = None
            if cache is not None:
                try:
                    cache_key = make_key({
                        "api_url": api_url,
                        "messages": _payload.get("messages"),
                        "options": _payload.get("options"),
                        "model": _payload.get("model") or model_override,
                        "eval_mode": eval_mode,
                    })
                    cached = cache.get(cache_key)
                    if isinstance(cached, str) and cached:
                        return cached
                except Exception:
                    pass
            if client is None:
                async with httpx.AsyncClient(timeout=60.0) as temp_client:  # Erhöhtes Timeout für komplexere Anfragen
                    resp = await temp_client.post(api_url, json=_payload, headers=headers)
            else:
                resp = await client.post(api_url, json=_payload, headers=headers)
            resp.raise_for_status()
            data_local = resp.json()
            content_local = data_local.get("content", "")
            # Cache schreiben
            if cache is not None and cache_key is not None and content_local:
                try:
                    cache.put(cache_key, content_local)
                except Exception:
                    pass
            return content_local

        content = await _send_and_get(payload)

        # Normalisiere den Text für die Überprüfung (Platzhalter für künftige Nutzung)
        # normalized_content = normalize_text(content)

        # Prüfe, ob die Antwort im RPG-Modus erfolgt ist
        is_rpg_mode = check_rpg_mode(content)

        # Prüfe alle Bedingungen
        checks_passed: Dict[str, bool] = {}
        failed_checks: List[str] = []

        # Wenn im RPG-Modus und es sich nicht um einen RPG-spezifischen Test handelt, Hinweis
        if is_rpg_mode and not any(rpg_term in (item.source_package or "").lower() for rpg_term in ["rpg", "novapolis", "szene"]):
            failed_checks.append("Antwort im RPG-Modus, aber Test erwartet allgemeine Antwort")

        # Wenn nicht gesetzt, sind alle Checks aktiv
        enabled = set(enabled_checks or ["must_include", "keywords_any", "keywords_at_least", "not_include", "regex", "rpg_style"])

        # 1. must_include: Alle Begriffe müssen enthalten sein
        if "must_include" in enabled and item.checks.get("must_include"):
            for term in item.checks["must_include"]:
                check_passed = check_term_inclusion(content, term)
                checks_passed[f"include:{term}"] = check_passed
                if not check_passed:
                    failed_checks.append(f"Erforderlicher Begriff nicht gefunden: '{term}'")

        # 2. keywords_any: Mindestens ein Begriff muss enthalten sein
        if "keywords_any" in enabled and item.checks.get("keywords_any"):
            any_found = False
            for term in item.checks["keywords_any"]:
                if check_term_inclusion(content, term):
                    any_found = True
                    break
            checks_passed["keywords_any"] = any_found
            if not any_found:
                failed_checks.append(f"Keine der alternativen Begriffe gefunden: {', '.join(item.checks['keywords_any'])}")

        # 3. keywords_at_least: Mindestens N Begriffe müssen enthalten sein
        keywords_at_least = item.checks.get("keywords_at_least")
        if "keywords_at_least" in enabled and keywords_at_least:
            try:
                required_count = 0
                items_list = []
                if hasattr(keywords_at_least, 'get'):
                    count_val = keywords_at_least.get("count")
                    items_val = keywords_at_least.get("items")
                    if count_val is not None:
                        required_count = int(count_val)
                    if items_val is not None:
                        items_list = list(items_val)
                found_count = 0
                for term in items_list:
                    if isinstance(term, str) and check_term_inclusion(content, term):
                        found_count += 1
                check_passed = found_count >= required_count
                checks_passed["keywords_at_least"] = check_passed
                if not check_passed:
                    failed_checks.append(f"Zu wenige Begriffe gefunden: {found_count}/{required_count}")
            except (AttributeError, ValueError, TypeError):
                checks_passed["keywords_at_least"] = False
                failed_checks.append("Ungültiges keywords_at_least Format")

        # 4. not_include: Begriffe dürfen nicht enthalten sein
        if "not_include" in enabled and item.checks.get("not_include"):
            for term in item.checks["not_include"]:
                term_not_included = not check_term_inclusion(content, term)
                checks_passed[f"not_include:{term}"] = term_not_included
                if not term_not_included:
                    failed_checks.append(f"Unerwünschter Begriff gefunden: '{term}'")

        # 5. regex: Reguläre Ausdrücke müssen matchen
        if "regex" in enabled and item.checks.get("regex"):
            for pattern in item.checks["regex"]:
                try:
                    pattern_str: str = str(pattern)
                    regex_match = bool(re.search(pattern_str, content))
                    checks_passed[f"regex:{pattern}"] = regex_match
                    if not regex_match:
                        failed_checks.append(f"Regex nicht erfüllt: '{pattern}'")
                except re.error:
                    checks_passed[f"regex:{pattern}"] = False
                    failed_checks.append(f"Ungültiges Regex-Pattern: '{pattern}'")

        # 6. rpg_style: Stil-Score muss unter/über Schwelle liegen, je nach Testpaket-Kontext
        if "rpg_style" in enabled:
            score = rpg_style_score(content)
            checks_passed["rpg_style"] = True  # Default true
            pkg = (item.source_package or "").lower()
            # Heuristik: In RPG-Paketen erwarten wir eher hohen Score, sonst niedrigen
            if any(k in pkg for k in ["rpg", "novapolis", "szene"]):
                if score < 0.4:
                    checks_passed["rpg_style"] = False
                    failed_checks.append(f"RPG-Stil zu schwach (Score {score:.2f})")
            else:
                if score > 0.2:
                    checks_passed["rpg_style"] = False
                    failed_checks.append(f"RPG-Stil zu präsent (Score {score:.2f})")

        # Prüfe, ob alle Bedingungen erfüllt sind
        success = all(checks_passed.values())

        attempts_used = 1

        # Optional: bei inhaltlichem Fehlschlag mit präzisem Hinweis einmal wiederholen
        def _extract_missing_terms(fails: List[str]) -> List[str]:
            miss: List[str] = []
            for msg in fails:
                m = re.search(r"Erforderlicher Begriff nicht gefunden: '([^']+)'", msg)
                if m:
                    miss.append(m.group(1))
            return miss

        if (not success) and retries > 0:
            missing = _extract_missing_terms(failed_checks)
            need_any = any(s.startswith("Keine der alternativen Begriffe gefunden") for s in failed_checks)
            need_atleast = any(s.startswith("Zu wenige Begriffe gefunden") for s in failed_checks)
            needs_regex = any(s.startswith("Regex nicht erfüllt") for s in failed_checks)
            # Nur für diese inhaltlichen Fälle erneut versuchen
            if missing or need_any or need_atleast or needs_regex:
                enhanced_messages: List[Dict[str, str]] = list(messages)
                if content:
                    enhanced_messages.append({"role": "assistant", "content": content})
                hint_parts: List[str] = []
                # Erneut Szene/Dialog heuristisch bestimmen
                def _retry_scene_dialog() -> Tuple[bool, bool]:
                    cat = (item.category or "").lower()
                    tags = [str(t).lower() for t in (item.tags or [])]
                    prompt_text = " ".join([m.get("content", "") for m in messages if m.get("role") == "user"])[:400].lower()
                    is_scene = ("szenen" in cat) or ("szene" in prompt_text) or any("szenen" in t or "szene" in t for t in tags)
                    is_dialog = ("dialog" in cat) or ("dialog" in prompt_text) or any("dialog" in t for t in tags)
                    return is_scene, is_dialog

                if missing:
                    is_scene, is_dialog = _retry_scene_dialog()
                    if is_scene or is_dialog:
                        hint_parts.append("Verwende diese Begriffe wörtlich im Text: " + ", ".join(sorted(set(missing))))
                        if is_scene:
                            hint_parts.append("Schreibe eine kurze Szene (1–2 Absätze) mit klarer Handlung.")
                        if is_dialog:
                            hint_parts.append("Schreibe einen knappen Dialog (max. 8 Repliken) ohne Überschriften.")
                    else:
                        hint_parts.append("Stelle sicher, dass diese Begriffe im Text vorkommen: " + ", ".join(sorted(set(missing))))
                if need_any:
                    hint_parts.append("Verwende mindestens einen der geforderten Alternativbegriffe.")
                if need_atleast:
                    hint_parts.append("Erfülle die Mindestanzahl an geforderten Schlüsselbegriffen.")
                if needs_regex:
                    hint_parts.append("Formatiere die Antwort so, dass die Muster (Regex) erfüllt sind.")
                # Falls globaler Eval-Hint aktiv, denselben Hint erneut sicherstellen (keine Doppelung)
                if eval_mode and hint_must_include and precomputed_hint_terms:
                    enhanced_messages = inject_eval_hint(enhanced_messages, precomputed_hint_terms)
                # Immer einen klaren Retry-Hinweis hinzufügen
                retry_hint = "Bitte antworte erneut, kurz und präzise. " + " ".join(hint_parts)
                enhanced_messages.append({"role": "user", "content": retry_hint})

                retry_payload = dict(payload)
                retry_payload["messages"] = enhanced_messages

                try:
                    content2 = await _send_and_get(retry_payload)
                    attempts_used = 2
                    # Erneut prüfen
                    is_rpg_mode = check_rpg_mode(content2)
                    checks_passed_retry: Dict[str, bool] = {}
                    failed_checks_retry: List[str] = []

                    if is_rpg_mode and not any(rpg_term in (item.source_package or "").lower() for rpg_term in ["rpg", "novapolis", "szene"]):
                        failed_checks_retry.append("Antwort im RPG-Modus, aber Test erwartet allgemeine Antwort")

                    if "must_include" in enabled and item.checks.get("must_include"):
                        for term in item.checks["must_include"]:
                            ok = check_term_inclusion(content2, term)
                            checks_passed_retry[f"include:{term}"] = ok
                            if not ok:
                                failed_checks_retry.append(f"Erforderlicher Begriff nicht gefunden: '{term}'")

                    if "keywords_any" in enabled and item.checks.get("keywords_any"):
                        any_found2 = any(check_term_inclusion(content2, t) for t in item.checks["keywords_any"])
                        checks_passed_retry["keywords_any"] = any_found2
                        if not any_found2:
                            failed_checks_retry.append(f"Keine der alternativen Begriffe gefunden: {', '.join(item.checks['keywords_any'])}")

                    keywords_at_least2 = item.checks.get("keywords_at_least")
                    if "keywords_at_least" in enabled and keywords_at_least2:
                        try:
                            required_count2 = int(keywords_at_least2.get("count", 0)) if hasattr(keywords_at_least2, 'get') else 0
                            items_list2 = list(keywords_at_least2.get("items", [])) if hasattr(keywords_at_least2, 'get') else []
                            found2 = sum(1 for t in items_list2 if isinstance(t, str) and check_term_inclusion(content2, t))
                            ok2 = found2 >= required_count2
                            checks_passed_retry["keywords_at_least"] = ok2
                            if not ok2:
                                failed_checks_retry.append(f"Zu wenige Begriffe gefunden: {found2}/{required_count2}")
                        except Exception:
                            checks_passed_retry["keywords_at_least"] = False
                            failed_checks_retry.append("Ungültiges keywords_at_least Format")

                    if "not_include" in enabled and item.checks.get("not_include"):
                        for term in item.checks["not_include"]:
                            not_included2 = not check_term_inclusion(content2, term)
                            checks_passed_retry[f"not_include:{term}"] = not_included2
                            if not not_included2:
                                failed_checks_retry.append(f"Unerwünschter Begriff gefunden: '{term}'")

                    if "regex" in enabled and item.checks.get("regex"):
                        for pattern in item.checks["regex"]:
                            try:
                                pstr = str(pattern)
                                match2 = bool(re.search(pstr, content2))
                                checks_passed_retry[f"regex:{pattern}"] = match2
                                if not match2:
                                    failed_checks_retry.append(f"Regex nicht erfüllt: '{pattern}'")
                            except re.error:
                                checks_passed_retry[f"regex:{pattern}"] = False
                                failed_checks_retry.append(f"Ungültiges Regex-Pattern: '{pattern}'")

                    if "rpg_style" in enabled:
                        score2 = rpg_style_score(content2)
                        checks_passed_retry["rpg_style"] = True
                        pkg2 = (item.source_package or "").lower()
                        if any(k in pkg2 for k in ["rpg", "novapolis", "szene"]):
                            if score2 < 0.4:
                                checks_passed_retry["rpg_style"] = False
                                failed_checks_retry.append(f"RPG-Stil zu schwach (Score {score2:.2f})")
                        else:
                            if score2 > 0.2:
                                checks_passed_retry["rpg_style"] = False
                                failed_checks_retry.append(f"RPG-Stil zu präsent (Score {score2:.2f})")

                    if all(checks_passed_retry.values()):
                        duration_ms = int((time.time() - start_time) * 1000)
                        return EvaluationResult(
                            item_id=item.id,
                            response=content2,
                            checks_passed=checks_passed_retry,
                            success=True,
                            failed_checks=failed_checks_retry,
                            source_file=item.source_file,
                            source_package=item.source_package,
                            duration_ms=duration_ms,
                            attempts=attempts_used,
                        )
                    else:
                        duration_ms = int((time.time() - start_time) * 1000)
                        return EvaluationResult(
                            item_id=item.id,
                            response=content2,
                            checks_passed=checks_passed_retry,
                            success=False,
                            failed_checks=failed_checks_retry,
                            source_file=item.source_file,
                            source_package=item.source_package,
                            duration_ms=duration_ms,
                            attempts=attempts_used,
                        )
                except Exception:
                    # Ignoriere Retry-Fehler und falle auf erstes Ergebnis zurück
                    pass

        # Berechne die Dauer in Millisekunden
        duration_ms = int((time.time() - start_time) * 1000)

        return EvaluationResult(
            item_id=item.id,
            response=content,
            checks_passed=checks_passed,
            success=success,
            failed_checks=failed_checks,
            source_file=item.source_file,
            source_package=item.source_package,
            duration_ms=duration_ms,
            attempts=attempts_used
        )
            
    except Exception as e:
        # Berechne die Dauer in Millisekunden
        duration_ms = int((time.time() - start_time) * 1000)
        
        return EvaluationResult(
            item_id=item.id,
            response="",
            checks_passed={},
            success=False,
            failed_checks=["Ausführungsfehler"],
            error=str(e),
            source_file=item.source_file,
            source_package=item.source_package,
            duration_ms=duration_ms
        )


async def preflight_check(api_url: str) -> bool:
    """
    Führt einen Preflight-Check gegen den API-Endpunkt durch.
    
    Args:
        api_url: URL des Chat-Endpunkts
        
    Returns:
        True, wenn der Check erfolgreich war, sonst False
    """
    logger = logging.getLogger("preflight")
    
    # Extrahiere die Basis-URL ohne Pfad
    try:
        from urllib.parse import urlsplit
        parts = urlsplit(api_url)
        base_url: str = f"{parts.scheme}://{parts.netloc}"
    except Exception:
        base_url = api_url.split("/")[0] + "//" + api_url.split("/")[2]
    health_url: str = f"{base_url}/health"
    
    try:
        logger.info(f"Führe Preflight-Check gegen {health_url} durch...")
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(health_url)
            
            if response.status_code == 200:
                logger.info("Preflight-Check erfolgreich.")
                return True
            else:
                logger.error(f"Preflight-Check fehlgeschlagen: HTTP {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"Preflight-Check fehlgeschlagen: {str(e)}")
        return False


async def run_evaluation(
    patterns: List[str],
    api_url: str = "http://localhost:8000/chat",
    limit: Optional[int] = None,
    eval_mode: bool = False,
    skip_preflight: bool = False,
    asgi: bool = False,
    enabled_checks: Optional[List[str]] = None,
    model_override: Optional[str] = None,
    temperature_override: Optional[float] = None,
    host_override: Optional[str] = None,
    top_p_override: Optional[float] = None,
    num_predict_override: Optional[int] = None,
    sweep: Optional[Dict[str, List[Any]]] = None,
    tag: Optional[str] = None,
    quiet: bool = False,
    retries: int = 0,
    use_cache: bool = False,
    hint_must_include: bool = False,
) -> List[EvaluationResult]:
    """
    Führt die Evaluierung für alle Einträge durch.
    
    Args:
        patterns: Liste von Glob-Patterns für die zu ladenden Dateien
        api_url: URL des Chat-Endpunkts
        limit: Optionale Begrenzung der Anzahl der zu evaluierenden Einträge
        eval_mode: Wenn True, wird der RPG-Modus für alle Tests deaktiviert
        skip_preflight: Wenn True, wird der Preflight-Check übersprungen
        
    Returns:
        Liste von Evaluierungsergebnissen
    """
    # Führe Preflight-Check durch, außer wenn übersprungen (im ASGI-Modus nicht nötig)
    if not asgi and not skip_preflight and not await preflight_check(api_url):
        logging.error(f"API-Endpunkt {api_url} ist nicht erreichbar. Evaluierung abgebrochen.")
        logging.info("Verwenden Sie --skip-preflight, um den Preflight-Check zu überspringen.")
        return []
    
    # Lade Einträge
    items = await load_evaluation_items(patterns)
    
    if limit and limit > 0 and limit < len(items):
        logging.info(f"Begrenze Evaluierung auf die ersten {limit} von {len(items)} Einträgen.")
        items = items[:limit]
    
    if not items:
        logging.error("Keine Einträge zum Evaluieren gefunden.")
        return []
    
    results: List[EvaluationResult] = []
    
    # Logge Info über den Eval-Modus
    if eval_mode:
        logging.info("Evaluierung wird im Eval-Modus durchgeführt (RPG-Modus deaktiviert)")
    
    # Aktuelle Zeit für Ergebnis-Dateiname (in results/ ablegen)
    timestamp = now_compact()
    # Run-ID für Korrelation/Logs
    try:
        import uuid as _uuid
        run_id = f"run-{timestamp}-{str(_uuid.uuid4()).split('-')[0]}"
    except Exception:
        run_id = f"run-{timestamp}"
    os.makedirs(DEFAULT_RESULTS_DIR, exist_ok=True)
    base_name = f"results_{timestamp}{('_' + tag) if tag else ''}.jsonl"
    results_file = os.path.join(DEFAULT_RESULTS_DIR, base_name)
    
    # Optional: ASGI-Client vorbereiten
    asgi_client: Optional[httpx.AsyncClient] = None
    if asgi:
        # FastAPI-App importieren und In-Process-Client erstellen
        from app.main import app as fastapi_app
        transport = httpx.ASGITransport(app=cast(Any, fastapi_app))
        asgi_client = httpx.AsyncClient(transport=transport, base_url="http://asgi")
        # Im ASGI-Modus gegen Pfad arbeiten
        api_url = "/chat"

    # Optional: Logger temporär drosseln, um Progress sauber zu halten
    prev_levels: Dict[str, int] = {}
    noisy_loggers = [
        "app.main",
        "app.api.chat",
        "httpx",
        "eval_loader",
        "eval",
        "preflight",
        "asyncio",
    ]
    try:
        root_debug = logging.getLogger().isEnabledFor(logging.DEBUG)

        # Immer: asyncio drosseln, außer im Debug-Modus
        asyncio_logger = logging.getLogger("asyncio")
        prev_levels["asyncio"] = asyncio_logger.level
        if not root_debug:
            asyncio_logger.setLevel(logging.ERROR if quiet else logging.WARNING)

        if quiet:
            for name in noisy_loggers:
                if name == "asyncio":
                    continue  # bereits oben gesetzt
                lg = logging.getLogger(name)
                prev_levels[name] = lg.level
                lg.setLevel(logging.WARNING)

        with Progress(transient=True) as progress:
            task = progress.add_task("[cyan]Evaluiere...", total=len(items))
            
            # Meta-Header als erste Zeile schreiben
            # Settings sicher ermitteln (falls Import oben fehlgeschlagen ist)
            _model_name = None
            _temperature = None
            _host = None
            try:
                # Verwende das bereits importierte settings-Objekt, falls vorhanden
                from app.core.settings import settings as _st
                _st_any: Any = cast(Any, _st)
                _model_name = cast(Optional[str], getattr(_st_any, "MODEL_NAME", None))
                _temperature = cast(Optional[float], getattr(_st_any, "TEMPERATURE", None))
                _host = cast(Optional[str], getattr(_st_any, "OLLAMA_HOST", None))
            except Exception:
                pass

            meta_header: Dict[str, Any] = {
                "_meta": True,
                "timestamp": timestamp,
                "run_id": run_id,
                "patterns": patterns,
                "api_url": api_url,
                "eval_mode": eval_mode,
                "asgi": asgi,
                "enabled_checks": enabled_checks or ["must_include", "keywords_any", "keywords_at_least", "not_include", "regex", "rpg_style"],
                "model": _model_name,
                "temperature": _temperature,
                "host": _host,
                "overrides": {"model": model_override, "temperature": temperature_override, "host": host_override, "top_p": top_p_override, "num_predict": num_predict_override},
                "sweep": sweep or None,
                "retries": retries,
                "hint_must_include": hint_must_include,
            }
            with open(results_file, "w", encoding="utf-8") as f:
                f.write(json.dumps(meta_header, ensure_ascii=False) + "\n")

            # Optional: Cache vorbereiten
            eval_cache = None
            if use_cache and EvalCacheType is not None:
                try:
                    cache_path = os.path.join(DEFAULT_RESULTS_DIR, "cache_eval.jsonl")
                    eval_cache = EvalCacheType(cache_path)
                    logging.info(f"Eval-Cache aktiv: {cache_path}")
                except Exception:
                    eval_cache = None

            # Hint-Begriffe je Item vorab berechnen (Eval+Flag)
            hint_terms_per_item: Dict[str, List[str]] = {}
            hint_applied_count = 0
            if eval_mode and hint_must_include:
                for it in items:
                    terms = compute_hint_terms(it, enabled_checks)
                    hint_terms_per_item[it.id] = terms
                    if terms:
                        hint_applied_count += 1
                if quiet:
                    print(f"hint_must_include applied: {hint_applied_count} items")
            # Hilfsfunktion zur Ausführung eines Durchlaufs mit gegebenen Overrides
            async def _run_once(temp_override: Optional[float], top_p_ov: Optional[float], num: Optional[int], tag_suffix: Optional[str] = None) -> None:
                nonlocal results_file
                # Update Datei, falls Sweep-Tag
                if tag_suffix:
                    results_file = os.path.join(DEFAULT_RESULTS_DIR, f"results_{timestamp}{('_' + tag) if tag else ''}_{tag_suffix}.jsonl")
                    with open(results_file, "w", encoding="utf-8") as f:
                        pass  # neu anlegen
                    # Meta-Header kopieren
                    mh = dict(meta_header)
                    mh["overrides"] = {"model": model_override, "temperature": temp_override if temp_override is not None else temperature_override, "host": host_override, "top_p": top_p_ov, "num_predict": num}
                    with open(results_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(mh, ensure_ascii=False) + "\n")
                # Items iterieren
                for item in items:
                    rid = f"{run_id}-{item.id}"
                    r = await evaluate_item(
                        item,
                        api_url,
                        eval_mode=eval_mode,
                        client=asgi_client,
                        enabled_checks=enabled_checks,
                        model_override=model_override,
                        temperature_override=temp_override if temp_override is not None else temperature_override,
                        host_override=host_override,
                        top_p_override=top_p_ov,
                        num_predict_override=num,
                        request_id=rid,
                        retries=retries,
                        cache=eval_cache,
                        hint_must_include=hint_must_include,
                        precomputed_hint_terms=hint_terms_per_item.get(item.id) if (eval_mode and hint_must_include) else None,
                    )
                    results.append(r)
                    with open(results_file, "a", encoding="utf-8") as f:
                        rd = asdict(r)
                        rd["response"] = truncate(rd.get("response", ""), 500)
                        f.write(json.dumps(rd, ensure_ascii=False) + "\n")
                    progress.update(cast(Any, task), advance=1)

            # Falls kein Sweep definiert, einfacher Durchlauf (unterstützt num_predict_override)
            if not sweep:
                await _run_once(temperature_override, top_p_override, num_predict_override)
            else:
                temps = sweep.get("temperature") if sweep else None
                tops = sweep.get("top_p") if sweep else None
                nums = None
                # unterstütze sowohl "max_tokens" als auch "num_predict" als Schlüssel
                if sweep:
                    nums = sweep.get("max_tokens") or sweep.get("num_predict")
                # Anzahl Tasks im Progress anpassen (grob): pro Item * Kombis
                combos = max(1, (len(temps) if temps else 1) * (len(tops) if tops else 1) * (len(nums) if nums else 1))
                progress.update(cast(Any, task), total=len(items) * combos)
                # Iteriere über Kombinationen
                if temps or tops or nums:
                    temps_list = temps or [None]
                    tops_list = tops or [None]
                    nums_list = nums or [None]
                    for tval in temps_list:
                        for pval in tops_list:
                            for nval in nums_list:
                                suffix_parts: List[str] = []
                                if tval is not None:
                                    suffix_parts.append(f"t{tval}")
                                if pval is not None:
                                    suffix_parts.append(f"p{pval}")
                                if nval is not None:
                                    suffix_parts.append(f"n{nval}")
                                await _run_once(float(tval) if tval is not None else None,
                                                float(pval) if pval is not None else None,
                                                int(nval) if nval is not None else None,
                                                tag_suffix=("_".join(suffix_parts) if suffix_parts else None))
    finally:
        if asgi_client is not None:
            await asgi_client.aclose()
        if quiet:
            for name, lvl in prev_levels.items():
                logging.getLogger(name).setLevel(lvl)
    
    logging.info(f"Ergebnisse wurden in {results_file} gespeichert.")
    return results


def print_results(results: List[EvaluationResult]) -> None:
    """
    Gibt eine Zusammenfassung der Evaluierungsergebnisse aus.
    
    Args:
        results: Liste von Evaluierungsergebnissen
    """
    console = Console()
    
    # Erstelle eine Tabelle für die Ergebnisse
    table = Table(title="Evaluierungsergebnisse")
    table.add_column("ID", style="cyan")
    table.add_column("Erfolg", style="green")
    table.add_column("Paket", style="blue")
    table.add_column("Dauer (ms)", style="magenta")
    table.add_column("RPG-Modus", style="yellow")
    table.add_column("Fehlgeschlagene Checks", style="yellow")
    table.add_column("Fehler", style="red")
    
    # Zähle, wie viele Antworten im RPG-Modus waren
    rpg_mode_count = 0
    
    for result in results:
        success = "✓" if result.success else "✗"
        error: str = cast(str, truncate(result.error or "", 40))
        duration = str(result.duration_ms)
        package_name = result.source_package or "-"

        # Prüfe, ob die Antwort im RPG-Modus erfolgt ist
        is_rpg_mode = check_rpg_mode(result.response)
        rpg_status = "✓" if is_rpg_mode else ""
        if is_rpg_mode:
            rpg_mode_count += 1

        # Verwende die bereits berechneten fehlgeschlagenen Checks
        failed_checks_str: str = ", ".join(result.failed_checks)
        if len(failed_checks_str) > 50:
            failed_checks_str = cast(str, truncate(failed_checks_str, 50))

        table.add_row(result.item_id, success, package_name, duration, rpg_status, failed_checks_str, error)
    
    console.print(table)
    
    # Ausgabe der Statistiken
    successful = sum(1 for r in results if r.success)
    total = len(results)
    success_rate = (successful / total) * 100 if total > 0 else 0
    
    console.print(f"\n[bold]Zusammenfassung:[/bold]")
    console.print(f"Erfolgreiche Tests: {successful}/{total} ({success_rate:.1f}%)")
    
    # Verhindere Division durch Null
    rpg_percentage = (rpg_mode_count/total*100) if total > 0 else 0
    avg_duration = (sum(r.duration_ms for r in results) / total) if total > 0 else 0
    
    console.print(f"Antworten im RPG-Modus: {rpg_mode_count}/{total} ({rpg_percentage:.1f}%)")
    console.print(f"Durchschnittliche Dauer: {avg_duration:.0f} ms")
    
    # Ausgabe der fehlgeschlagenen IDs
    if successful < total:
        failed_ids = [r.item_id for r in results if not r.success]
        console.print(f"Fehlgeschlagene Tests: {', '.join(failed_ids[:10])}" + 
                     (f" und {len(failed_ids) - 10} weitere" if len(failed_ids) > 10 else ""))
        
    # Gruppiere nach Paketen
    console.print("\n[bold]Statistik nach Paketen:[/bold]")
    package_stats: Dict[str, Dict[str, Union[int, float]]] = {}
    for r in results:
        package = r.source_package or "unbekannt"
        if package not in package_stats:
            package_stats[package] = {"total": 0, "success": 0, "duration": 0}
        package_stats[package]["total"] += 1
        package_stats[package]["duration"] += r.duration_ms
        if r.success:
            package_stats[package]["success"] += 1
    
    # Erstelle eine Tabelle für die Paket-Statistiken
    package_table = Table()
    package_table.add_column("Paket", style="blue")
    package_table.add_column("Erfolg", style="green")
    package_table.add_column("Rate", style="cyan")
    package_table.add_column("Durchschn. Dauer", style="magenta")
    
    # Ausgabe der Paket-Statistiken
    for package, stats in sorted(package_stats.items()):
        success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        avg_duration = stats["duration"] / stats["total"] if stats["total"] > 0 else 0
        package_table.add_row(
            package, 
            f"{stats['success']}/{stats['total']}", 
            f"{success_rate:.1f}%",
            f"{avg_duration:.0f} ms"
        )
    
    console.print(package_table)


def compute_failure_summary(results: List[EvaluationResult]) -> Dict[str, Any]:
    """Aggregiert Fehlerinformationen für einen kompakten Bericht.

    Ermittelt u. a. Top-Failure-Kategorien (rpg_style, term_inclusion) und häufige fehlende Begriffe.
    """
    total = len(results)
    successes = sum(1 for r in results if r.success)
    rpg_hits = sum(1 for r in results if check_rpg_mode(r.response))

    # Zähler
    fail_counts: Dict[str, int] = {
        "rpg_style": 0,
        "term_inclusion": 0,
    }
    missing_terms: Dict[str, int] = {}
    per_package_fails: Dict[str, List[Tuple[str, List[str]]]] = {}

    miss_re = re.compile(r"Erforderlicher Begriff nicht gefunden: '([^']+)'")

    for r in results:
        if r.success:
            continue
        pkg = (r.source_package or "unbekannt")
        per_package_fails.setdefault(pkg, []).append((r.item_id, list(r.failed_checks)))

        # RPG-Fehler heuristisch erkennen anhand der failure messages
        if any("RPG-Stil" in s or "Antwort im RPG-Modus" in s for s in r.failed_checks):
            fail_counts["rpg_style"] += 1

        # Term-Inklusionsfehler zählen und Begriffe sammeln
        counted_term_failure = False
        for msg in r.failed_checks:
            m = miss_re.search(msg)
            if m:
                counted_term_failure = True
                term = m.group(1).strip().lower()
                missing_terms[term] = missing_terms.get(term, 0) + 1
        if counted_term_failure:
            fail_counts["term_inclusion"] += 1

    # Top missing terms sortieren
    top_missing = sorted(missing_terms.items(), key=lambda kv: kv[1], reverse=True)[:5]

    return {
        "total": total,
        "successes": successes,
        "rpg_hits": rpg_hits,
        "fail_counts": fail_counts,
        "top_missing_terms": top_missing,
        "per_package_fails": per_package_fails,
    }


def print_failure_report(results: List[EvaluationResult]) -> None:
    """Druckt einen kompakten Fehlerbericht (eine Bildschirmseite)."""
    summary = compute_failure_summary(results)
    total = summary["total"]
    successes = summary["successes"]
    rpg_hits = summary["rpg_hits"]
    fail_counts = summary["fail_counts"]
    top_missing = summary["top_missing_terms"]
    per_pkg = summary["per_package_fails"]

    print("")
    print(f"Summary: success {successes}/{total}, RPG hits {rpg_hits}/{total}")
    print("Top failures:")
    print(f"  - rpg_style: {fail_counts.get('rpg_style', 0)}")
    if top_missing:
        miss_preview = ", ".join([f"{t}({n})" for t, n in top_missing])
        print(f"  - term_inclusion: {fail_counts.get('term_inclusion', 0)} (top missing: {miss_preview})")
    else:
        print(f"  - term_inclusion: {fail_counts.get('term_inclusion', 0)}")

    # Erste 5 fehlgeschlagene IDs pro Paket
    print("First 5 failed IDs per package:")
    for pkg, items in sorted(per_pkg.items()):
        if not items:
            continue
        print(f"  {pkg}:")
        for iid, reasons in items[:5]:
            # Gründe kompakt
            short = "; ".join(reasons)
            if len(short) > 160:
                short = short[:157] + "..."
            print(f"    - {iid}: {short}")


# --- Hinweis-Helfer für Eval ---------------------------------------------------
def _normalize_term_for_dedupe(t: str) -> str:
    return str(t or "").strip().lower()


def compute_hint_terms(
    item: EvaluationItem,
    enabled_checks: Optional[List[str]] = None,
    cap: int = 6,
) -> List[str]:
    """Sammelt erwartete Begriffe aus aktiven Term-Checks, dedupliziert und begrenzt.

    Reihenfolgepriorität: must_include → keywords_at_least.items → keywords_any.
    Dedupe ist case-insensitiv. Keine fuzzy-Logik.
    """
    enabled = set(enabled_checks or [])
    out: List[str] = []
    seen: set[str] = set()

    def _add_terms(terms: List[str]) -> None:
        for term in terms:
            if not isinstance(term, str):
                continue
            key = _normalize_term_for_dedupe(term)
            if not key:
                continue
            if key in seen:
                continue
            seen.add(key)
            # Ausgabe: normalisiert (lowercase) für konsistente Hints
            out.append(key)
            if len(out) >= cap:
                return

    # 1) must_include (wenn nicht eingeschränkt oder explizit aktiviert)
    if (not enabled) or ("must_include" in enabled):
        mi_val = cast(Any, item.checks.get("must_include"))
        if isinstance(mi_val, list):
            mi_terms: List[str] = []
            for x in cast(List[Any], mi_val):
                try:
                    mi_terms.append(str(x))
                except Exception:
                    continue
            _add_terms(mi_terms)
            if len(out) >= cap:
                return out

    # 2) keywords_at_least.items
    if (not enabled) or ("keywords_at_least" in enabled):
        kal_val_any = cast(Any, item.checks.get("keywords_at_least"))
        items_list: List[str] = []
        if isinstance(kal_val_any, dict):
            kal_val = cast(Dict[str, Any], kal_val_any)
            items_any = kal_val.get("items")
            if isinstance(items_any, list):
                for x in cast(List[Any], items_any):
                    try:
                        items_list.append(str(x))
                    except Exception:
                        continue
        _add_terms(items_list)
        if len(out) >= cap:
            return out

    # 3) keywords_any
    if (not enabled) or ("keywords_any" in enabled):
        ka_val_any = cast(Any, item.checks.get("keywords_any"))
        if isinstance(ka_val_any, list):
            ka_terms: List[str] = []
            for x in cast(List[Any], ka_val_any):
                try:
                    ka_terms.append(str(x))
                except Exception:
                    continue
            _add_terms(ka_terms)

    return out[:cap]


def inject_eval_hint(messages: List[Dict[str, str]], terms: List[str]) -> List[Dict[str, str]]:
    """Fügt einen Eval-Hinweis vor der ersten User-Message ein, wenn noch nicht vorhanden."""
    if not terms:
        return messages
    for m in messages:
        if m.get("role") == "user" and str(m.get("content", "")).startswith("Hinweis (Eval):"):
            return messages
    hint_text = "Hinweis (Eval): Verwende diese Begriffe wörtlich: " + ", ".join(terms)
    idx = next((i for i, m in enumerate(messages) if m.get("role") == "user"), 0)
    new_messages = list(messages)
    new_messages.insert(idx, {"role": "user", "content": hint_text})
    return new_messages


def run_evaluation_with_retry(
    file_pattern: str, 
    api_url: str = "http://localhost:8000/chat",
    eval_mode: bool = False
) -> List[EvaluationResult]:
    """
    Führt die Evaluierung mit automatischen Wiederholungsversuchen durch.
    
    Args:
        file_pattern: Glob-Pattern für die zu ladenden Dateien
        api_url: URL des Chat-Endpunkts
        eval_mode: Wenn True, wird der RPG-Modus für alle Tests deaktiviert
        
    Returns:
        Liste von Evaluierungsergebnissen
    """
    return asyncio.run(_run_evaluation_with_retry(file_pattern, api_url, eval_mode))


async def _run_evaluation_with_retry(
    file_pattern: str,
    api_url: str = "http://localhost:8000/chat",
    eval_mode: bool = False
) -> List[EvaluationResult]:
    """
    Interne Funktion für die Evaluierung mit Wiederholungsversuchen.
    
    Args:
        file_pattern: Glob-Pattern für die zu ladenden Dateien
        api_url: URL des Chat-Endpunkts
        eval_mode: Wenn True, wird der RPG-Modus für alle Tests deaktiviert
    """
    try:
        # Konvertiere den String-Pattern in eine Liste für run_evaluation
        pattern_list = [file_pattern]
        results = await run_evaluation(pattern_list, api_url, eval_mode=eval_mode)
        
        if not results:
            # Wenn keine Ergebnisse, versuche die alternative Dateiendung
            if file_pattern.endswith('.jsonl'):
                json_pattern = file_pattern.replace('.jsonl', '.json')
                print(f"Keine JSONL-Dateien gefunden. Versuche JSON-Format: {json_pattern}")
                results = await run_evaluation([json_pattern], api_url, eval_mode=eval_mode)
            elif file_pattern.endswith('.json'):
                jsonl_pattern = file_pattern.replace('.json', '.jsonl')
                print(f"Keine JSON-Dateien gefunden. Versuche JSONL-Format: {jsonl_pattern}")
                results = await run_evaluation([jsonl_pattern], api_url, eval_mode=eval_mode)
        
        return results
    except Exception as e:
        print(f"Fehler bei der Evaluierung: {str(e)}")
        return []


def create_example_eval_file(file_path: str, start_id: int = 21, count: int = 20) -> bool:
    """
    Erstellt eine Beispiel-Evaluationsdatei im JSONL-Format
    
    Args:
        file_path: Pfad zur zu erstellenden Datei
        start_id: Startnummer für IDs (z.B. 21 für eval-021)
        count: Anzahl der zu generierenden Datensätze
        
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        # Stelle sicher, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Beispielprompts und must_include-Terms
        example_prompts: List[Dict[str, Any]] = [
            {"prompt": "Erkläre mir den Unterschied zwischen einem Array und einer verketteten Liste.", 
             "must_include": ["Speicher", "Zugriff", "Datenstruktur"]},
            {"prompt": "Was sind die Hauptmerkmale von agiler Softwareentwicklung?", 
             "must_include": ["iterativ", "flexibel", "Scrum"]},
            {"prompt": "Wie funktioniert ein Elektromotor?", 
             "must_include": ["Magnetfeld", "Rotation", "Strom"]},
            {"prompt": "Erkläre mir den Aufbau einer eukaryotischen Zelle.", 
             "must_include": ["Zellkern", "Organellen", "Mitochondrien"]},
            {"prompt": "Was sind die wichtigsten Bestandteile der Erdatmosphäre?", 
             "must_include": ["Stickstoff", "Sauerstoff", "Atmosphäre"]},
            {"prompt": "Wie bereite ich mich am besten auf eine Präsentation vor?", 
             "must_include": ["üben", "vorbereiten", "Zeit"]},
            {"prompt": "Erkläre mir, wie Verschlüsselung im Internet funktioniert.", 
             "must_include": ["Kryptographie", "Sicherheit", "Verbindung"]},
            {"prompt": "Was sind beliebte Programmiersprachen für Anfänger?", 
             "must_include": ["Python", "einfach", "beliebt"]},
            {"prompt": "Erkläre mir, wie künstliche Intelligenz von menschlicher Intelligenz unterscheidet.", 
             "must_include": ["lernen", "menschlich", "Maschinen"]},
            {"prompt": "Wie kann ich meine Zeitplanung verbessern?", 
             "must_include": ["Prioritäten", "Planung", "Zeit"]},
        ]
        
        # Mehrere Variationen erstellen, um auf die gewünschte Anzahl zu kommen
        while len(example_prompts) < count:
            # Kopiere vorhandene Prompts und modifiziere sie leicht
            for prompt_data in example_prompts[:]:
                if len(example_prompts) >= count:
                    break
                    
                new_prompt = prompt_data.copy()
                new_prompt["prompt"] = "Bitte " + new_prompt["prompt"].lower()
                example_prompts.append(new_prompt)
        
        # Beschränke auf die gewünschte Anzahl
        example_prompts = example_prompts[:count]
        
        with open(file_path, "w", encoding="utf-8") as f:
            for i, example in enumerate(example_prompts):
                # Erstelle Datenstruktur mit ID, Prompt und Must-Include
                eval_item: Dict[str, Any] = {
                    "id": f"eval-{start_id + i:03d}",
                    "prompt": example["prompt"],
                    "must_include": example["must_include"]
                }
                
                # Schreibe als JSONL (eine JSON-Zeile pro Zeile)
                f.write(json.dumps(eval_item, ensure_ascii=False) + "\n")
                
        print(f"Beispiel-Evaluationsdatei erstellt: {file_path}")
        print(f"Enthält {count} Datensätze mit IDs von eval-{start_id:03d} bis eval-{start_id+count-1:03d}")
        return True
        
    except Exception as e:
        print(f"Fehler beim Erstellen der Beispieldatei: {str(e)}")
        return False


if __name__ == "__main__":
    # Standardpfade (Datasets/Results/Config)
    base_eval = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval")
    eval_dir = DEFAULT_EVAL_DIR
    results_dir = DEFAULT_RESULTS_DIR
    config_dir = DEFAULT_CONFIG_DIR
    # Standardmäßig im datasets-Ordner suchen
    default_pattern = os.path.join(DEFAULT_DATASET_DIR, DEFAULT_FILE_PATTERN)
    api_url = DEFAULT_API_URL
    
    # Parse Kommandozeilenargumente
    parser = argparse.ArgumentParser(description="Evaluierungsskript für den CVN Agent")
    parser.add_argument("--packages", "-p", action="append", help="Glob-Pattern für Eval-Pakete (mehrfach möglich)")
    parser.add_argument("--api-url", "-a", help=f"URL des Chat-Endpunkts (default: {DEFAULT_API_URL})")
    parser.add_argument("--limit", "-l", type=int, help="Anzahl der zu evaluierenden Einträge begrenzen")
    parser.add_argument("--debug", "-d", action="store_true", help="Debug-Modus aktivieren")
    parser.add_argument("--eval-mode", "-e", action="store_true", help="Deaktiviert den RPG-Modus für die Evaluierung")
    parser.add_argument("--skip-preflight", "-s", action="store_true", help="Überspringt den Preflight-Check (nützlich, wenn der Server nicht läuft)")
    parser.add_argument("--asgi", action="store_true", help="ASGI-In-Process: Evaluierung direkt gegen FastAPI-App ohne laufenden Server-Port")
    parser.add_argument("--profile", type=str, choices=["eval", "default", "unrestricted"], help="Profil-Preset: eval, default, unrestricted")
    parser.add_argument("--checks", nargs="*", help="Aktiviere Check-Typen; unterstützt Komma-Liste und Alias 'term_inclusion'")
    parser.add_argument("--quiet", action="store_true", help="Unterdrückt Logausgaben lauter Logger während der Progress-Anzeige")
    parser.add_argument("--log-json", action="store_true", help="Log-Ausgabe als JSON-Linien")
    parser.add_argument("--combine-out", type=str, help="Optionaler Pfad für zusammengeführte JSONL der geladenen Datensätze")
    parser.add_argument("--no-quiet", action="store_true", help="Quiet-Mode deaktivieren (setzt sich gegen --quiet durch)")
    # Overrides & Sweeps
    parser.add_argument("--host", type=str, dest="host", help="Override für OLLAMA_HOST (z. B. http://localhost:11434)")
    parser.add_argument("--model", type=str, dest="model", help="Override für Modellnamen (z. B. llama3.1:8b)")
    parser.add_argument("--temperature", type=float, dest="temperature", help="Override für temperature")
    parser.add_argument("--top-p", type=float, dest="top_p", help="Override für top_p")
    parser.add_argument("--max-tokens", type=int, dest="max_tokens", help="Override für num_predict/max_tokens")
    parser.add_argument("--tag", type=str, help="Zusätzlicher Tag im Ergebnisdateinamen")
    parser.add_argument("--sweep-temp", nargs="*", type=float, dest="sweep_temp", help="Parameter-Sweep über Temperaturen (z. B. 0.1 0.2 0.3)")
    parser.add_argument("--sweep-top-p", nargs="*", type=float, dest="sweep_top_p", help="Parameter-Sweep über top_p-Werte (z. B. 0.7 0.9)")
    parser.add_argument("--sweep-max-tokens", nargs="*", type=int, dest="sweep_max_tokens", help="Parameter-Sweep über max_tokens/num_predict (z. B. 128 256 512)")
    parser.add_argument("--retries", type=int, default=0, help="Inhaltliche Retrys bei fehlgeschlagenen Checks (z. B. 1)")
    parser.add_argument("--cache", dest="use_cache", action="store_true", help="Antworten lokal cachen (eval/results/cache_eval.jsonl)")
    parser.add_argument("--no-cache", dest="no_cache", action="store_true", help="Caching explizit deaktivieren")
    parser.add_argument("--hint-must-include", dest="hint_must_include", action="store_true", help="Eval-only: Injektiert vor erster User-Message einen Hinweis mit wörtlich zu verwendenden Begriffen (aus must_include/keywords_*)")
    
    # Kommandos
    parser.add_argument("--create-example", action="store_true", help="Beispiel-Eval-Paket erstellen")
    parser.add_argument("--create-synonyms", action="store_true", help="Synonymdatei erstellen")
    parser.add_argument("--show-prompts", action="store_true", help="Zeigt die geladenen Prompts an, ohne sie zu evaluieren")
    
    args = parser.parse_args()
    
    # Konfiguriere Logging (JSON optional)
    log_level = logging.DEBUG if args.debug else logging.INFO
    if args.log_json:
        class JsonFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                payload = {
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "level": record.levelname,
                    "logger": record.name,
                    "msg": record.getMessage(),
                }
                return json.dumps(payload, ensure_ascii=False)
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logging.basicConfig(level=log_level, handlers=[handler])
        os.environ["LOG_JSON"] = "true"
    else:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
    if not args.debug:
        # Unterdrücke gewöhnliche Deprecation/Resource-Warnungen im CLI-Betrieb
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=ResourceWarning)
    
    # Verarbeite Kommandos
    if args.create_example:
        # Erstelle ein Beispiel-Eval-Paket
        os.makedirs(eval_dir, exist_ok=True)
        example_file = os.path.join(eval_dir, "eval-21-40_fantasy_v1.0.jsonl")
        create_example_eval_file(example_file, 21, 20)
        sys.exit(0)
    
    if args.create_synonyms:
        # Erstelle eine leere Synonymdatei als Vorlage
        os.makedirs(config_dir, exist_ok=True)
        synonyms_file = os.path.join(config_dir, "synonyms.json")
        if not os.path.exists(synonyms_file):
            with open(synonyms_file, "w", encoding="utf-8") as f:
                # Erstelle ein leeres Dictionary als Vorlage
                example_synonyms = {
                    "beispiel": ["muster", "exempel", "probe", "vorlage"],
                    "synonyme": ["entsprechungen", "gleichbedeutende wörter", "äquivalente"]
                }
                json.dump(example_synonyms, f, ensure_ascii=False, indent=4)
            logging.info(f"Synonymdatei erstellt: {synonyms_file}")
        else:
            logging.info(f"Synonymdatei existiert bereits: {synonyms_file}")
        sys.exit(0)
    
    # Setze API-URL, wenn angegeben
    if args.api_url:
        api_url = args.api_url
    
    # Stelle sicher, dass die Verzeichnisse existieren
    os.makedirs(eval_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(config_dir, exist_ok=True)
    
    # Bestimme die zu ladenden Dateien; ergänze Schwestermaske automatisch
    patterns: List[str] = args.packages if args.packages else [os.path.join(DEFAULT_DATASET_DIR, "*.json*")]
    def _sibling_mask(p: str) -> Optional[str]:
        if p.endswith(".jsonl"):
            return p[:-1]  # .jsonl -> .json
        if p.endswith(".json"):
            return p + "l"  # .json -> .jsonl
        return None
    if patterns and len(patterns) == 1:
        sib = _sibling_mask(patterns[0])
        if sib:
            patterns = [patterns[0], cast(str, sib)]
    
    # Prüfe, ob Eval-Dateien existieren
    if not any(glob.glob(pattern) for pattern in patterns):
        logging.warning("Keine Eval-Dateien gefunden. Erstelle ein Beispiel-Eval-Paket...")
        example_file = os.path.join(eval_dir, "eval-21-40_fantasy_v1.0.jsonl")
        create_example_eval_file(example_file, 21, 20)
        # Nach Erstellung: beide Masken prüfen
        base_mask = os.path.join(eval_dir, DEFAULT_FILE_PATTERN)
        sib = _sibling_mask(base_mask)
        patterns = [base_mask] + ([sib] if sib else [])
    
    # Vor-Evaluierung: Synonyme und Datensätze laden (neuer Loader)
    try:
        from scripts.syn_loader import load_synonyms as _syn_load
        syn, syn_count = _syn_load()
        # Notwendig? Der eigentliche Evaluator lädt Synonyme intern, daher hier nur Logging
        logging.getLogger("syn_loader").info(f"synonyms merged: {syn_count}")
    except Exception as e:
        logging.getLogger("syn_loader").warning(f"Synonyme nicht vorab geladen: {e}")

    diags: List[Dict[str, Any]] = []
    try:
        from scripts.eval_loader import load_packages as _load_pkgs
        combine_path: Optional[Path] = Path(args.combine_out) if isinstance(args.combine_out, str) and args.combine_out else None
        items_loaded, diags = _load_pkgs(patterns, combine_out=combine_path)
        # Zusammenfassungstabelle (eine Bildschirmseite)
        # Aggregate
        total_loaded = sum(d.get("loaded_count", 0) for d in diags)
        total_gen = sum(d.get("generated_id_count", 0) for d in diags)
        total_skipped = sum(d.get("skipped_count", 0) for d in diags)
        total_errors = sum(len(d.get("parse_errors", []) or []) for d in diags)
        # Drucke kompakte Tabelle (Textmodus)
        if not args.log_json:
            print("file".ljust(38), "loaded".rjust(6), "gen_id".rjust(6), "skipped".rjust(8), "errors".rjust(7))
            for d in diags[:50]:
                name = os.path.basename(d.get("file", ""))
                print(name.ljust(38)[:38], str(d.get("loaded_count", 0)).rjust(6), str(d.get("generated_id_count", 0)).rjust(6), str(d.get("skipped_count", 0)).rjust(8), str(len(d.get("parse_errors", []) or [])).rjust(7))
            print("TOTAL".ljust(38), str(total_loaded).rjust(6), str(total_gen).rjust(6), str(total_skipped).rjust(8), str(total_errors).rjust(7))
    except Exception as e:
        logging.getLogger("eval_loader").warning(f"Dataset-Preload übersprungen: {e}")

    # Profil-Defaults anwenden (nur fehlende Werte überschreiben)
    # eval_mode wird später bei run_evaluation berücksichtigt
    t_final, p_final, n_final, eval_mode_flag = resolve_profile_overrides(
        getattr(args, "profile", None),
        args.temperature,
        args.top_p,
        args.max_tokens,
    )
    # Falls explizites --eval-mode gesetzt, gewinnt dies über Profil
    if args.eval_mode:
        eval_mode_flag = True

    # Checks normalisieren
    checks_final = normalize_checks(args.checks)

    # Führe Evaluierung durch
    console = Console()
    console.print(f"[bold]CVN Agent Evaluierung[/bold]")
    console.print(f"Patterns: {', '.join(patterns)}")
    console.print(f"API-URL: {api_url}")
    if args.limit:
        console.print(f"Limit: {args.limit} Einträge")
    if args.eval_mode:
        console.print(f"[bold yellow]Eval-Modus aktiviert:[/bold yellow] RPG-Systemprompt wird temporär überschrieben")
    if args.skip_preflight:
        console.print(f"[bold red]Preflight-Check übersprungen:[/bold red] API-Verfügbarkeit wird nicht geprüft")
    if args.asgi:
        console.print(f"[bold green]ASGI-Modus:[/bold green] In-Process gegen FastAPI-App (kein HTTP-Port erforderlich)")
    console.print("")
    if p_final is not None:
        console.print(f"top_p Override: {p_final}")
    if n_final is not None:
        console.print(f"num_predict Override: {n_final}")
    if t_final is not None:
        console.print(f"temperature Override: {t_final}")
    if args.model:
        console.print(f"Model Override: {args.model}")
    if args.host:
        console.print(f"Host Override: {args.host}")
    if args.retries:
        console.print(f"Retries bei Fehlschlag: {args.retries}")
    if args.sweep_temp or args.sweep_top_p:
        console.print(f"Sweep: temp={args.sweep_temp or '-'} top_p={args.sweep_top_p or '-'} max_tokens={args.sweep_max_tokens or '-'}")
    if args.use_cache and not args.no_cache:
        console.print("[green]Eval-Cache: aktiviert (cache_eval.jsonl)[/green]")
    
    # Verarbeite "show-prompts" Kommando
    if args.show_prompts:
        items = asyncio.run(load_evaluation_items(patterns))
        if items:
            console.print(f"[bold]Geladene Prompts ({len(items)}):[/bold]")
            for item in (items[:args.limit] if args.limit else items):
                prompt_content = item.messages[0]["content"] if item.messages else "Kein Inhalt"
                console.print(f"[cyan]{item.id}[/cyan] ({item.source_package}): [yellow]{prompt_content[:100]}{'...' if len(prompt_content) > 100 else ''}[/yellow]")
        else:
            console.print("[bold red]Keine Prompts gefunden.[/bold red]")
        sys.exit(0)
    
    # Quiet-Default: true, außer im Debug-Modus oder wenn --no-quiet gesetzt
    quiet_final = (not args.no_quiet) and (args.quiet or (not args.debug))
    sweep_cfg: Optional[Dict[str, List[Any]]] = None
    if (args.sweep_temp and len(args.sweep_temp) > 0) or (args.sweep_top_p and len(args.sweep_top_p) > 0) or (args.sweep_max_tokens and len(args.sweep_max_tokens) > 0):
        sweep_cfg = {}
        if args.sweep_temp:
            sweep_cfg["temperature"] = [float(x) for x in args.sweep_temp]
        if args.sweep_top_p:
            sweep_cfg["top_p"] = [float(x) for x in args.sweep_top_p]
        if args.sweep_max_tokens:
            sweep_cfg["max_tokens"] = [int(x) for x in args.sweep_max_tokens]
    results = asyncio.run(run_evaluation(
        patterns=patterns,
        api_url=api_url,
        limit=args.limit,
        eval_mode=eval_mode_flag,
        skip_preflight=args.skip_preflight,
        asgi=args.asgi,
        enabled_checks=checks_final,
        model_override=args.model,
        temperature_override=t_final,
        host_override=args.host,
        top_p_override=p_final,
        num_predict_override=n_final,
        sweep=sweep_cfg,
        tag=args.tag,
        quiet=quiet_final,
        retries=args.retries,
        use_cache=(args.use_cache and not args.no_cache),
        hint_must_include=bool(args.hint_must_include),
    ))
    
    if results:
        print_results(results)
        # Kompakter Fehlerbericht
        print_failure_report(results)
    else:
        console.print("[bold red]Keine Ergebnisse. Die Evaluierung wurde abgebrochen oder keine Einträge gefunden.[/bold red]")