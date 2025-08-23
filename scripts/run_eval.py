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
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
import warnings

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Importiere die Utility-Funktionen
from utils.eval_utils import truncate, coerce_json_to_jsonl, load_synonyms

# Versuche, die Anwendungseinstellungen zu importieren
try:
    # Importiere die Einstellungen
    from app.core.settings import settings
    
    # Verwende die Einstellungen für Standardwerte (neue Unterordner-Struktur)
    DEFAULT_EVAL_DIR = os.path.join(project_root, settings.EVAL_DATASET_DIR)
    DEFAULT_RESULTS_DIR = os.path.join(project_root, settings.EVAL_RESULTS_DIR)
    DEFAULT_CONFIG_DIR = os.path.join(project_root, settings.EVAL_CONFIG_DIR)
    DEFAULT_FILE_PATTERN = settings.EVAL_FILE_PATTERN
    DEFAULT_API_URL = f"http://localhost:8000/chat"
except ImportError:
    # Fallback-Werte, wenn die Anwendungseinstellungen nicht verfügbar sind
    base_eval = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval")
    DEFAULT_EVAL_DIR = os.path.join(base_eval, "datasets")
    DEFAULT_RESULTS_DIR = os.path.join(base_eval, "results")
    DEFAULT_CONFIG_DIR = os.path.join(base_eval, "config")
    DEFAULT_FILE_PATTERN = "eval-*.json"
    DEFAULT_API_URL = "http://localhost:8000/chat"

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
        # Synonyme liegen nun in config/
        synonyms_path = os.path.join(DEFAULT_CONFIG_DIR, "synonyms.json")
        logging.info(f"Lade Synonyme aus: {synonyms_path}")
        _synonyms_cache = load_synonyms(synonyms_path)
        logging.info(f"Anzahl der Synonym-Einträge: {len(_synonyms_cache)}")
    
    # Suche nach dem Begriff und seinen Varianten
    synonyms: List[str] = []
    
    for key, values in _synonyms_cache.items():
        if term in key or key in term:
            synonyms.extend(values)
        else:
            for value in values:
                if term in value or value in term:
                    synonyms.extend([key] + [v for v in values if v != value])
    
    return list(set(synonyms))  # Entferne Duplikate


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
        patterns = [os.path.join(DEFAULT_EVAL_DIR, DEFAULT_FILE_PATTERN)]
    
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
                    data_array = coerce_json_to_jsonl(file_content)
                    
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
                
                item = EvaluationItem(
                    id=data["id"],
                    messages=data["messages"],  # type: ignore
                    checks=data["checks"],  # type: ignore
                    source_file=source_file,
                    source_package=source_package
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


async def evaluate_item(
    item: EvaluationItem,
    api_url: str = "http://localhost:8000/chat",
    eval_mode: bool = False,
    client: Optional[httpx.AsyncClient] = None,
    enabled_checks: Optional[List[str]] = None,
    model_override: Optional[str] = None,
    temperature_override: Optional[float] = None,
    host_override: Optional[str] = None,
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
        messages: List[Dict[str, str]] = list(item.messages)  # Kopie erstellen
        
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
        if options:
            payload["options"] = options
        
        logger = logging.getLogger("eval")
        logger.debug(f"Evaluiere Item {item.id}")
        
        # Entweder übergebenen Client verwenden (ASGI-Modus) oder einen temporären erstellen (HTTP-Modus)
        if client is None:
            async with httpx.AsyncClient(timeout=60.0) as temp_client:  # Erhöhtes Timeout für komplexere Anfragen
                response = await temp_client.post(api_url, json=payload)
        else:
            response = await client.post(api_url, json=payload)

        response.raise_for_status()
        data = response.json()
        content = data.get("content", "")

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
        enabled = set(enabled_checks or ["must_include", "keywords_any", "keywords_at_least", "not_include", "regex"])

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
                    count_val = keywords_at_least.get("count")  # type: ignore
                    items_val = keywords_at_least.get("items")  # type: ignore
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

        # Prüfe, ob alle Bedingungen erfüllt sind
        success = all(checks_passed.values())

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
            duration_ms=duration_ms
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
    base_url: str = api_url.split("/")[0] + "//" + api_url.split("/")[2]
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
    quiet: bool = False,
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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    os.makedirs(DEFAULT_RESULTS_DIR, exist_ok=True)
    results_file = os.path.join(DEFAULT_RESULTS_DIR, f"results_{timestamp}.jsonl")
    
    # Optional: ASGI-Client vorbereiten
    asgi_client: Optional[httpx.AsyncClient] = None
    if asgi:
        # FastAPI-App importieren und In-Process-Client erstellen
        from app.main import app as fastapi_app  # type: ignore
        transport = httpx.ASGITransport(app=fastapi_app)
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
            meta_header: Dict[str, Any] = {
                "_meta": True,
                "timestamp": timestamp,
                "patterns": patterns,
                "api_url": api_url,
                "eval_mode": eval_mode,
                "asgi": asgi,
                "enabled_checks": enabled_checks or ["must_include", "keywords_any", "keywords_at_least", "not_include", "regex"],
                "model": __import__('app.core.settings', fromlist=['settings']).settings.MODEL_NAME,
                "temperature": __import__('app.core.settings', fromlist=['settings']).settings.TEMPERATURE,
                "host": __import__('app.core.settings', fromlist=['settings']).settings.OLLAMA_HOST,
                "overrides": {"model": model_override, "temperature": temperature_override, "host": host_override},
            }
            with open(results_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(meta_header, ensure_ascii=False) + "\n")

            for item in items:
                result = await evaluate_item(
                    item,
                    api_url,
                    eval_mode=eval_mode,
                    client=asgi_client,
                    enabled_checks=enabled_checks,
                    model_override=model_override,
                    temperature_override=temperature_override,
                    host_override=host_override,
                )
                results.append(result)
                
                # Speichere Ergebnis sofort in JSONL-Datei
                with open(results_file, "a", encoding="utf-8") as f:
                    # Konvertiere Result in Dictionary und kürze die Antwort
                    result_dict = asdict(result)
                    result_dict["response"] = truncate(result_dict["response"], 500)
                    f.write(json.dumps(result_dict, ensure_ascii=False) + "\n")
                
                progress.update(task, advance=1)
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
        error = truncate(result.error or "", 40)
        duration = str(result.duration_ms)
        package_name = result.source_package or "-"
        
        # Prüfe, ob die Antwort im RPG-Modus erfolgt ist
        is_rpg_mode = check_rpg_mode(result.response)
        rpg_status = "✓" if is_rpg_mode else ""
        if is_rpg_mode:
            rpg_mode_count += 1
        
        # Verwende die bereits berechneten fehlgeschlagenen Checks
        failed_checks_str = ", ".join(result.failed_checks)
        if len(failed_checks_str) > 50:
            failed_checks_str = truncate(failed_checks_str, 50)
        
        table.add_row(result.item_id, success, package_name, duration, rpg_status, failed_checks_str, error)
    
    console.print(table)
    
    # Ausgabe der Statistiken
    successful = sum(1 for r in results if r.success)
    total = len(results)
    success_rate = (successful / total) * 100 if total > 0 else 0
    
    console.print(f"\n[bold]Zusammenfassung:[/bold]")
    console.print(f"Erfolgreiche Tests: {successful}/{total} ({success_rate:.1f}%)")
    console.print(f"Antworten im RPG-Modus: {rpg_mode_count}/{total} ({rpg_mode_count/total*100:.1f}%)")
    console.print(f"Durchschnittliche Dauer: {sum(r.duration_ms for r in results) / total:.0f} ms")
    
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
    eval_dir = DEFAULT_EVAL_DIR  # datasets
    results_dir = DEFAULT_RESULTS_DIR
    config_dir = DEFAULT_CONFIG_DIR
    default_pattern = os.path.join(eval_dir, DEFAULT_FILE_PATTERN)
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
    parser.add_argument("--checks", nargs="*", help="Aktiviere nur diese Check-Typen (must_include, keywords_any, keywords_at_least, not_include, regex)")
    parser.add_argument("--quiet", action="store_true", help="Unterdrückt Logausgaben lauter Logger während der Progress-Anzeige")
    parser.add_argument("--no-quiet", action="store_true", help="Quiet-Mode deaktivieren (setzt sich gegen --quiet durch)")
    
    # Kommandos
    parser.add_argument("--create-example", action="store_true", help="Beispiel-Eval-Paket erstellen")
    parser.add_argument("--create-synonyms", action="store_true", help="Synonymdatei erstellen")
    parser.add_argument("--show-prompts", action="store_true", help="Zeigt die geladenen Prompts an, ohne sie zu evaluieren")
    
    args = parser.parse_args()
    
    # Konfiguriere Logging
    log_level = logging.DEBUG if args.debug else logging.INFO
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
        example_file = os.path.join(eval_dir, "eval-21-40_demo_v1.0.jsonl")
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
    
    # Bestimme die zu ladenden Dateien
    patterns = args.packages if args.packages else [default_pattern]
    
    # Prüfe, ob Eval-Dateien existieren
    if not any(glob.glob(pattern) for pattern in patterns):
        logging.warning("Keine Eval-Dateien gefunden. Erstelle ein Beispiel-Eval-Paket...")
        example_file = os.path.join(eval_dir, "eval-21-40_demo_v1.0.jsonl")
        create_example_eval_file(example_file, 21, 20)
        patterns = [os.path.join(eval_dir, DEFAULT_FILE_PATTERN)]
    
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
    results = asyncio.run(run_evaluation(patterns, api_url, args.limit, args.eval_mode, args.skip_preflight, args.asgi, args.checks, None, None, None, quiet_final))
    
    if results:
        print_results(results)
    else:
        console.print("[bold red]Keine Ergebnisse. Die Evaluierung wurde abgebrochen oder keine Einträge gefunden.[/bold red]")