from __future__ import annotations

import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel

# Lade Umgebungsvariablen aus .env-Datei
load_dotenv()

class Settings(BaseModel):
    """Anwendungseinstellungen"""
    
    # API-Einstellungen
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CVN Agent"
    PROJECT_DESCRIPTION: str = "Conversational Agent mit Ollama"
    PROJECT_VERSION: str = "0.1.0"
    
    # Ollama-Einstellungen
    OLLAMA_HOST: str = "http://localhost:11434"
    MODEL_NAME: str = "llama3.1:8b"
    TEMPERATURE: float = 0.7
    
    # Evaluierungseinstellungen
    EVAL_DIRECTORY: str = "eval"
    EVAL_FILE_PATTERN: str = "eval-*.json"
    
    # CORS-Einstellungen
    BACKEND_CORS_ORIGINS: List[str] = []
    
    class Config:
        case_sensitive = True
    
    @classmethod
    def from_env(cls) -> "Settings":
        """
        Erstellt eine Settings-Instanz aus Umgebungsvariablen.
        Verarbeitet BACKEND_CORS_ORIGINS und andere spezielle Felder.
        """
        # Standard-Werte für Settings
        values: Dict[str, Any] = {
            "API_V1_STR": os.getenv("API_V1_STR", "/api/v1"),
            "PROJECT_NAME": os.getenv("PROJECT_NAME", "CVN Agent"),
            "PROJECT_DESCRIPTION": os.getenv("PROJECT_DESCRIPTION", "Conversational Agent mit Ollama"),
            "PROJECT_VERSION": os.getenv("PROJECT_VERSION", "0.1.0"),
            "OLLAMA_HOST": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            "MODEL_NAME": os.getenv("MODEL_NAME", "llama3.1:8b"),
            "TEMPERATURE": float(os.getenv("TEMPERATURE", "0.7")),
            "EVAL_DIRECTORY": os.getenv("EVAL_DIRECTORY", "eval"),
            "EVAL_FILE_PATTERN": os.getenv("EVAL_FILE_PATTERN", "eval-*.json"),
        }
        
        # Verarbeite BACKEND_CORS_ORIGINS als kommagetrennte Liste
        cors_origins = os.getenv("BACKEND_CORS_ORIGINS", "")
        if cors_origins:
            # Splitte die Liste und entferne Leerzeichen
            origins = [origin.strip() for origin in cors_origins.split(",")]
            # Filtere leere Strings
            values["BACKEND_CORS_ORIGINS"] = [origin for origin in origins if origin]
        
        return cls(**values)

# Exportiere die Settings-Instanz
settings = Settings.from_env()

# Definiere, welche Symbole exportiert werden
__all__ = ["settings", "Settings"]
