#!/usr/bin/env python
"""
Migriert eval-21-40_fantasy (ehem. demo) auf neues Schema (prompt -> messages, must_include -> checks.must_include)
"""
import json
import os
import sys
from typing import Any, Dict, List

def migrate_demo_dataset():
    """Migriert das Fantasy-Dataset (ehem. Demo) auf das neue Schema."""
    path = os.path.join("eval", "datasets", "eval-21-40_fantasy_v1.0.json")
    
    if not os.path.exists(path):
        print(f"Datei nicht gefunden: {path}")
        return False
    
    # Prüfe, ob Datei leer ist
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            print(f"Datei ist leer: {path}")
            return False
    
    try:
        # Lade Einträge (sowohl JSON-Array als auch JSONL-Format unterstützen)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            entries: List[Dict[str, Any]] = []
            if content.startswith('['):
                # JSON-Array Format
                try:
                    raw = json.loads(content)
                    if isinstance(raw, list):
                        from typing import cast
                        entries = cast(List[Dict[str, Any]], raw)
                except Exception:
                    entries = []
            else:
                # JSONL Format
                for line in content.split('\n'):
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        if isinstance(obj, dict):
                            from typing import cast
                            entries.append(cast(Dict[str, Any], obj))
                    except Exception:
                        continue

        if not entries:
            print(f"Keine Einträge gefunden in: {path}")
            return False

        print(f"Gefunden: {len(entries)} Einträge in {path}")

        migrated: List[Dict[str, Any]] = []
        changes_made = False

        for i, e in enumerate(entries):
            # original_e wurde nicht verwendet; entfernt
            
            # Migration 1: prompt -> messages
            if "prompt" in e and "messages" not in e:
                e["messages"] = [{"role": "user", "content": e.pop("prompt")}]
                changes_made = True
                print(f"  Eintrag {i+1}: prompt -> messages migriert")
            
            # Migration 2: must_include -> checks.must_include
            if "must_include" in e and "checks" not in e:
                e["checks"] = {"must_include": e.pop("must_include")}
                changes_made = True
                print(f"  Eintrag {i+1}: must_include -> checks.must_include migriert")
            elif "must_include" in e and "checks" in e:
                # must_include ist noch außerhalb von checks
                if "must_include" not in e["checks"]:
                    e["checks"]["must_include"] = e.pop("must_include")
                    changes_made = True
                    print(f"  Eintrag {i+1}: must_include in checks verschoben")
                else:
                    # Beide existieren, entferne das äußere
                    e.pop("must_include")
                    changes_made = True
                    print(f"  Eintrag {i+1}: doppeltes must_include entfernt")
            
            migrated.append(e)
        
        if not changes_made:
            print("Keine Migrationen nötig - alle Einträge bereits im neuen Format")
            return True
        
        # Backup erstellen
        backup_path = path + ".backup"
        with open(backup_path, "w", encoding="utf-8") as f:
            if content.startswith('['):
                json.dump(entries, f, ensure_ascii=False, indent=2)
            else:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"Backup erstellt: {backup_path}")
        
        # Neue Datei schreiben (JSONL Format)
        with open(path, "w", encoding="utf-8") as f:
            for e in migrated:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        
        print(f"✅ Migration abgeschlossen: {len(migrated)} Einträge in {path}")
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Migration: {e}")
        return False

def main():
    """Hauptfunktion für CLI-Nutzung."""
    print("Dataset-Schema Migration")
    print("=" * 40)
    
    # Wechsle in das Projektverzeichnis
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    success = migrate_demo_dataset()
    
    if success:
        print("\n✅ Migration erfolgreich abgeschlossen")
        sys.exit(0)
    else:
        print("\n❌ Migration fehlgeschlagen")
        sys.exit(1)

if __name__ == "__main__":
    main()
