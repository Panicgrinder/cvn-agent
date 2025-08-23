#!/usr/bin/env python
"""
Test-Skript für die Anwendungseinstellungen.
"""

from app.core.settings import settings

def main():
    """Hauptfunktion zum Testen der Einstellungen."""
    
    print("Projekt-Einstellungen:")
    print(f"  Name: {settings.PROJECT_NAME}")
    print(f"  Beschreibung: {settings.PROJECT_DESCRIPTION}")
    print(f"  Version: {settings.PROJECT_VERSION}")
    print()
    
    print("CORS-Einstellungen:")
    print(f"  BACKEND_CORS_ORIGINS: {settings.BACKEND_CORS_ORIGINS}")
    
    # Prüfe, ob ALLOW_ORIGIN_REGEX existiert, bevor darauf zugegriffen wird
    if hasattr(settings, 'ALLOW_ORIGIN_REGEX'):
        print(f"  ALLOW_ORIGIN_REGEX: {settings.ALLOW_ORIGIN_REGEX}")
    else:
        print("  ALLOW_ORIGIN_REGEX: Nicht definiert")
    print()
    
    print("Ollama-Einstellungen:")
    print(f"  OLLAMA_HOST: {settings.OLLAMA_HOST}")
    print(f"  MODEL_NAME: {settings.MODEL_NAME}")
    print()
    
    print("Evaluierungseinstellungen:")
    print(f"  EVAL_DIRECTORY: {settings.EVAL_DIRECTORY}")
    print(f"  EVAL_FILE_PATTERN: {settings.EVAL_FILE_PATTERN}")
    print()

if __name__ == "__main__":
    main()