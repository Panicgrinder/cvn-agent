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
    
    print()
    
    print("Ollama-Einstellungen:")
    print(f"  OLLAMA_HOST: {settings.OLLAMA_HOST}")
    print(f"  MODEL_NAME: {settings.MODEL_NAME}")
    print()
    
    print("Evaluierungseinstellungen:")
    print(f"  EVAL_DIRECTORY: {settings.EVAL_DIRECTORY}")
    print(f"  EVAL_DATASET_DIR: {settings.EVAL_DATASET_DIR}")
    print(f"  EVAL_RESULTS_DIR: {settings.EVAL_RESULTS_DIR}")
    print(f"  EVAL_CONFIG_DIR: {settings.EVAL_CONFIG_DIR}")
    print(f"  EVAL_FILE_PATTERN: {settings.EVAL_FILE_PATTERN}")
    print()

if __name__ == "__main__":
    main()