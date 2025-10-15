"""
Hilfsprogramm zum Bearbeiten und Personalisieren der System-Prompts für CVN Agent.
Verwenden Sie dieses Tool, um den Prompt nach Ihren Vorstellungen anzupassen.
"""

import os
import json
import argparse
import sys
from typing import List

# Pfad zum Projektverzeichnis
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Pfad zur Prompts-Datei
PROMPTS_FILE = os.path.join(project_root, "app", "core", "prompts.py")

def read_prompts() -> str:
    """Liest die aktuelle prompts.py Datei"""
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        return f.read()

def write_prompts(content: str):
    """Schreibt den neuen Inhalt in die prompts.py Datei"""
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def customize_unrestricted_prompt():
    """Ermöglicht die Anpassung des uneingeschränkten Systemprompts"""
    print("========== UNRESTRICTED PROMPT CUSTOMIZATION ==========")
    print("Sie können hier Ihren eigenen uneingeschränkten Systemprompt definieren.")
    print("Dieser wird verwendet, wenn der Parameter 'unrestricted_mode=True' gesetzt ist.")
    print("HINWEIS: Als Entwickler des CVN Agents haben Sie die volle Kontrolle über den Inhalt.")
    print("GitHub Copilot selbst kann keine expliziten oder anstößigen Inhalte erstellen,")
    print("aber Sie können Ihren eigenen Prompt nach Ihren Vorstellungen gestalten.")
    print("=======================================================\n")
    
    current_content = read_prompts()
    
    # Extrahiere den aktuellen UNRESTRICTED_SYSTEM_PROMPT
    import re
    unrestricted_match = re.search(r'UNRESTRICTED_SYSTEM_PROMPT\s*=\s*"""(.*?)"""', current_content, re.DOTALL)
    
    if unrestricted_match:
        current_prompt = unrestricted_match.group(1).strip()
        print(f"Aktueller uneingeschränkter Prompt:\n{current_prompt}\n")
    else:
        print("Konnte den aktuellen uneingeschränkten Prompt nicht finden.")
        return
    
    print("Bitte geben Sie Ihren neuen uneingeschränkten Prompt ein.")
    print("Drücken Sie Strg+D (Unix) oder Strg+Z (Windows), gefolgt von Enter, um die Eingabe abzuschließen.")
    print("--- EINGABE BEGINNEN ---")
    
    lines: List[str] = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    except KeyboardInterrupt:
        print("\nAbgebrochen.")
        return
    
    new_prompt = "\n".join(lines)
    
    if not new_prompt.strip():
        print("Keine Änderungen vorgenommen.")
        return
    
    # Ersetze den alten Prompt mit dem neuen
    new_content = current_content.replace(
        f'UNRESTRICTED_SYSTEM_PROMPT = """{current_prompt}"""',
        f'UNRESTRICTED_SYSTEM_PROMPT = """{new_prompt}"""'
    )
    
    write_prompts(new_content)
    print("\nUneingeschränkter Prompt wurde aktualisiert!")

def create_content_rules():
    """Erstellt eigene Regeln für die Inhaltsfilterung"""
    print("========== CONTENT RULES CUSTOMIZATION ==========")
    print("Sie können hier eigene Regeln für die Inhaltsfilterung definieren.")
    print("Diese werden in der Datei content_rules.json gespeichert.")
    print("=================================================\n")
    
    rules_file = os.path.join(project_root, "app", "core", "content_rules.json")
    
    # Lade bestehende Regeln, falls vorhanden
    rules = {}
    if os.path.exists(rules_file):
        try:
            with open(rules_file, "r", encoding="utf-8") as f:
                rules = json.load(f)
            print("Bestehende Regeln geladen.")
        except Exception as e:
            print(f"Fehler beim Laden der bestehenden Regeln: {e}")
    
    print("\nGeben Sie Ihre eigenen Regeln ein (Format: 'Kategorie: erlaubt/verboten').")
    print("Beispiel: 'Gewalt: erlaubt' oder 'Beleidigungen: verboten'")
    print("Geben Sie 'fertig' ein, um abzuschließen.\n")
    
    while True:
        rule_input = input("Regel (oder 'fertig'): ").strip()
        if rule_input.lower() == 'fertig':
            break
        
        try:
            category, value = rule_input.split(":", 1)
            category = category.strip()
            value_str = value.strip().lower()
            
            if value_str in ['erlaubt', 'ja', 'true', '1']:
                rules[category] = True
            elif value_str in ['verboten', 'nein', 'false', '0']:
                rules[category] = False
            else:
                print(f"Ungültiger Wert: {value_str}. Verwenden Sie 'erlaubt' oder 'verboten'.")
                continue
            
            print(f"Regel hinzugefügt: {category} -> {'erlaubt' if rules[category] else 'verboten'}")
        except ValueError:
            print("Ungültiges Format. Verwenden Sie 'Kategorie: erlaubt/verboten'.")
    
    # Speichere die Regeln
    os.makedirs(os.path.dirname(rules_file), exist_ok=True)
    with open(rules_file, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=4, ensure_ascii=False)
    
    print(f"\nInhaltsregeln wurden in {rules_file} gespeichert!")

def main():
    parser = argparse.ArgumentParser(description="CVN Agent Prompt-Anpassungstool")
    parser.add_argument("--customize-unrestricted", action="store_true", help="Den uneingeschränkten Prompt anpassen")
    parser.add_argument("--create-rules", action="store_true", help="Eigene Regeln für die Inhaltsfilterung erstellen")
    
    args = parser.parse_args()
    
    if args.customize_unrestricted:
        customize_unrestricted_prompt()
    elif args.create_rules:
        create_content_rules()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()