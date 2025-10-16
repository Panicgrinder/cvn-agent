import json
import re
import os
from typing import List, Dict, Any, Union

def strip_eval_prefix(s: str) -> str:
    """
    Entfernt das führende "eval-" Präfix von einer ID, falls vorhanden.

    Beispiel: "eval-123" -> "123", "item-1" -> "item-1"
    """
    try:
        return s[5:] if isinstance(s, str) and s.startswith("eval-") else s
    except Exception:
        return s

def ensure_eval_prefix(s: str) -> str:
    """
    Stellt sicher, dass eine ID mit "eval-" beginnt.

    Beispiel: "123" -> "eval-123", "eval-123" -> "eval-123"
    """
    try:
        s_str = str(s)
        return s_str if s_str.startswith("eval-") else f"eval-{s_str}"
    except Exception:
        return str(s)

def truncate(text: str, n: int = 200) -> str:
    """
    Kürzt einen Text auf eine maximale Länge.
    
    Args:
        text: Der zu kürzende Text
        n: Maximale Länge
        
    Returns:
        Gekürzter Text, ggf. mit "..." am Ende
    """
    if len(text) <= n:
        return text
    return text[:n-3] + "..."

def normalize_text(text: str) -> str:
    """
    Normalisiert einen Text für Vergleiche:
    - Kleinschreibung
    - Ersetzt Umlaute
    - Entfernt Satzzeichen
    
    Args:
        text: Der zu normalisierende Text
        
    Returns:
        Normalisierter Text
    """
    # Kleinschreibung
    text = text.lower()
    
    # Ersetze Umlaute
    text = (text.replace("ä", "ae")
                .replace("ö", "oe")
                .replace("ü", "ue")
                .replace("ß", "ss"))
    
    # Entferne Satzzeichen außer Leerzeichen und Bindestriche
    text = re.sub(r'[^\w\s-]', ' ', text)
    
    # Reduziere mehrfache Leerzeichen auf eines
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def coerce_json_to_jsonl(text: str) -> List[Dict[str, Any]]:
    """
    Konvertiert einen JSON-Text zu einer Liste von Dictionaries.
    Unterstützt sowohl JSON-Arrays als auch JSONL-Format.
    
    Args:
        text: Der zu konvertierende JSON-Text
        
    Returns:
        Liste von Dictionaries
    """
    # Entferne Kommentare (falls vorhanden)
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    
    # Prüfe, ob es ein JSON-Array ist
    if text.strip().startswith('[') and text.strip().endswith(']'):
        try:
            # Versuche als JSON-Array zu parsen
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
    # Versuche als JSONL zu parsen (eine JSON-Zeile pro Zeile)
    results: List[Dict[str, Any]] = []
    errors = 0
    
    for line in text.strip().split('\n'):
        if not line.strip():
            continue
            
        try:
            obj = json.loads(line)
            results.append(obj)
        except json.JSONDecodeError:
            errors += 1
    
    if errors == 0 and results:
        return results
        
    # Wenn beides fehlschlägt, versuche Reparaturmaßnahmen
    # Stelle sicher, dass Kommas zwischen Objekten sind
    fixed_text = re.sub(r'}\s*{', '},{', text)
    
    # Umschließe mit Klammern, falls nicht vorhanden
    if not fixed_text.strip().startswith('['):
        fixed_text = '[' + fixed_text
    if not fixed_text.strip().endswith(']'):
        fixed_text = fixed_text + ']'
    
    try:
        return json.loads(fixed_text)
    except json.JSONDecodeError:
        # Letzer Versuch: Jede Zeile einzeln parsen und zu Liste hinzufügen
        results = []  # type: List[Dict[str, Any]]
        for line in text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Ersetze einzelne Anführungszeichen durch doppelte
            line = line.replace("'", '"')
            
            try:
                # Wenn es ein vollständiges JSON-Objekt ist
                obj = json.loads(line)
                results.append(obj)
            except json.JSONDecodeError:
                # Wenn es kein vollständiges JSON-Objekt ist, versuche es zu reparieren
                if line.startswith('{') and not line.endswith('}'):
                    line += '}'
                elif not line.startswith('{') and line.endswith('}'):
                    line = '{' + line
                
                try:
                    obj = json.loads(line)
                    results.append(obj)
                except json.JSONDecodeError:
                    # Ignoriere Zeilen, die nicht repariert werden können
                    pass
    
    return results

def load_synonyms(path: Union[str, List[str]] = "eval/config/synonyms.json") -> Dict[str, List[str]]:
    """
    Lädt Synonyme aus einer oder mehreren JSON-Dateien und merged sie.

    Args:
        path: Pfad oder Liste von Pfaden zu JSON-Dateien mit Synonymen

    Returns:
        Zusammengeführtes Dictionary mit Schlüsselwörtern und deren Synonymen
    """
    paths: List[str] = [path] if isinstance(path, str) else list(path)

    merged: Dict[str, List[str]] = {}

    for p in paths:
        if not os.path.exists(p):
            # Still und leise überspringen, wenn eine optionale Datei fehlt
            continue
        try:
            with open(p, 'r', encoding='utf-8') as f:
                raw = json.load(f)
                if isinstance(raw, dict):
                    from typing import cast as _cast, List as _List
                    data = _cast(Dict[str, Any], raw)
                    for key, values in data.items():
                        if not isinstance(key, str):
                            continue
                        if isinstance(values, list):
                            values_list = _cast(_List[Any], values)
                            acc = merged.setdefault(key, [])
                            # Anhängen mit Duplikatentfernung bei Beibehaltung der Reihenfolge
                            for v in values_list:
                                if isinstance(v, str) and v not in acc:
                                    acc.append(v)
        except Exception as e:
            print(f"Fehler beim Laden der Synonymdatei '{p}': {str(e)}")

    return merged