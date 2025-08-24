from __future__ import annotations

import os
from typing import List, Any, cast
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Anwendungseinstellungen"""
    # Pydantic Settings v2 Konfiguration (.env wird automatisch berücksichtigt)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # API-Einstellungen
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CVN Agent"
    PROJECT_DESCRIPTION: str = "Conversational Agent mit Ollama"
    PROJECT_VERSION: str = "0.1.1"
    
    # Ollama-Einstellungen
    OLLAMA_HOST: str = "http://localhost:11434"
    MODEL_NAME: str = "llama3.1:8b"
    TEMPERATURE: float = 0.7
    
    # Evaluierungseinstellungen
    EVAL_DIRECTORY: str = "eval"
    # Unterordner für bessere Übersicht
    EVAL_DATASET_DIR: str = os.path.join("eval", "datasets")
    EVAL_RESULTS_DIR: str = os.path.join("eval", "results")
    EVAL_CONFIG_DIR: str = os.path.join("eval", "config")
    EVAL_FILE_PATTERN: str = "eval-*.json"
    
    # CORS-Einstellungen
    BACKEND_CORS_ORIGINS: List[str] = []

    # Sicherheits-/Request-Limits
    REQUEST_TIMEOUT: float = 60.0
    REQUEST_MAX_INPUT_CHARS: int = 16000
    REQUEST_MAX_TOKENS: int = 512

    # Rate Limiting (optional)
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 30
    RATE_LIMIT_WINDOW_SEC: float = 60.0
    RATE_LIMIT_TRUSTED_IPS: List[str] = ["127.0.0.1", "::1"]
    RATE_LIMIT_EXEMPT_PATHS: List[str] = ["/health", "/docs", "/openapi.json"]

    # Logging / Observability
    LOG_JSON: bool = False
    LOG_TRUNCATE_CHARS: int = 200
    REQUEST_ID_HEADER: str = "X-Request-ID"

    # Kontext-Notizen (lokal, optional)
    CONTEXT_NOTES_ENABLED: bool = False
    # Mehrere mögliche Standardpfade; erster vorhandener wird verwendet, oder Inhalte werden zusammengeführt
    CONTEXT_NOTES_PATHS: List[str] = [
        os.path.join("eval", "config", "context.local.md"),
        os.path.join("eval", "config", "context.local.jsonl"),
        os.path.join("eval", "config", "context.local.json"),
        os.path.join("data", "context.local.md"),
    ]
    CONTEXT_NOTES_MAX_CHARS: int = 4000

    @staticmethod
    def _to_nonempty_str(obj: Any) -> Optional[str]:
        s = str(obj).strip()
        return s if s else None

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _coerce_cors(cls, v: Any) -> List[str]:
        """Erlaubt Komma-separierte Liste oder JSON-Liste in der ENV."""
        if v is None or v == "":
            return []
        if isinstance(v, list):
            seq: List[Any] = list(cast(List[Any], v))
            result: List[str] = []
            for x in seq:
                s = cls._to_nonempty_str(x)
                if s is not None:
                    result.append(s)
            return result
        if isinstance(v, str):
            # Versuche JSON-Liste
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    seq2: List[Any] = list(cast(List[Any], parsed))
                    result2: List[str] = []
                    for x in seq2:
                        s = cls._to_nonempty_str(x)
                        if s is not None:
                            result2.append(s)
                    return result2
            except Exception:
                pass
            # Fallback: Komma-separiert
            return [s.strip() for s in v.split(',') if s.strip()]
        return []

# Exportiere die Settings-Instanz (lädt automatisch aus ENV/.env)
settings = Settings()

# Definiere, welche Symbole exportiert werden
__all__ = ["settings", "Settings"]
