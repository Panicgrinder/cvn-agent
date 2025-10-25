from __future__ import annotations

import os
from typing import List, Any, cast
from typing import Literal
from pathlib import Path
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
    # Sampling-Defaults (wirken als Basis, wenn vom Request nicht überschrieben)
    TOP_P: float = 0.9
    TOP_K: int = 40
    MIN_P: float = 0.0           # 0.0 deaktiviert min_p; Werte 0..1
    TYPICAL_P: float = 1.0       # 1.0 entspricht deaktiviert
    TFS_Z: float = 1.0           # 1.0 entspricht deaktiviert
    MIROSTAT: int = 0            # 0=aus, 1/2=an (Algorithmusvariante)
    MIROSTAT_TAU: float = 5.0
    MIROSTAT_ETA: float = 0.1
    PENALIZE_NEWLINE: bool = False
    REPEAT_PENALTY: float = 1.1
    REPEAT_LAST_N: int = 64
    NUM_CTX_DEFAULT: Optional[int] = None  # Wenn gesetzt, als Default an Modell übergeben
    
    # Evaluierungseinstellungen
    EVAL_DIRECTORY: str = "eval"
    # Unterordner für bessere Übersicht
    EVAL_DATASET_DIR: str = os.path.join("eval", "datasets")
    EVAL_RESULTS_DIR: str = os.path.join("eval", "results")
    EVAL_CONFIG_DIR: str = os.path.join("eval", "config")
    # Unterstütze sowohl .json als auch .jsonl (z.B. eval-*.jsonl)
    EVAL_FILE_PATTERN: str = "eval-*.json*"
    
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
    # Standardpfade (Priorität: lokale Dateien zuerst, dann angeheftete Referenzen)
    # Begründung: Tests und erwartetes Verhalten priorisieren explizite lokale Notizen vor Sammel-Refs.
    CONTEXT_NOTES_PATHS: List[str] = [
        os.path.join("eval", "config", "context.local.md"),
        os.path.join("eval", "config", "context.local.jsonl"),
        os.path.join("eval", "config", "context.local.json"),
        os.path.join("eval", "config", "context.notes"),  # pinned refs (ORDER/README ignoriert)
        os.path.join("data", "context.local.md"),
    ]
    CONTEXT_NOTES_MAX_CHARS: int = 12000

    # Inhalts-Policy/Regeln (optional)
    # Wenn aktiviert, werden optionale Hooks aus content_management verwendet (z.B. für "unrestricted mode").
    CONTENT_POLICY_ENABLED: bool = False
    # Neue, feinere Policy-Flags
    # Globaler Schalter für Richtlinien-Anwendung (Pre/Post). Standard: deaktiviert -> kein Verhaltensänderung.
    POLICIES_ENABLED: bool = False
    # Optionaler Pfad zu einer Policy-Datei (JSON) mit einfachen Regeln, z. B. {"forbidden_terms": [...], "rewrite_map": {"bad":"good"}}
    POLICY_FILE: Optional[str] = None
    # Wenn True, umgeht der "unrestricted"-Modus strikt alle Policies (Pre/Post)
    POLICY_STRICT_UNRESTRICTED_BYPASS: bool = True

    # Eval-Post-Rewrite (stilistische Neutralisierung im Post-Hook)
    EVAL_POST_REWRITE_ENABLED: bool = True
    EVAL_POST_MAX_SENTENCES: int = 2
    EVAL_POST_MAX_CHARS: int = 240
    # einfache Regel-Flags für die Neutralisierung
    EVAL_POST_RULES: dict[str, bool] = {
        "neutralize_pronouns": True,
        "strip_roleplay": True,
        "no_exclamations": True,
        "no_emojis": True,
        "no_storytelling": True,
        "compact_style": True,
    }

    # Session Memory (optional)
    # Wenn aktiviert und eine session_id in der Anfrage vorhanden ist, wird ein kurzer Verlauf pro Sitzung gespeichert.
    SESSION_MEMORY_ENABLED: bool = False
    SESSION_MEMORY_MAX_MESSAGES: int = 20
    SESSION_MEMORY_MAX_CHARS: int = 12000

    # Neue, konfigurierbare Session Memory (Store + Budgets)
    MEMORY_ENABLED: bool = True
    MEMORY_STORE: Literal["inmemory", "jsonl"] = "inmemory"
    MEMORY_MAX_TURNS: int = 20
    MEMORY_MAX_CHARS: int = 8000
    MEMORY_DIR: Path = Path(".data/memory")

    # Tool-Use (Basis, optional)
    TOOLS_ENABLED: bool = False
    TOOLS_WHITELIST: List[str] = []

    # RAG (lokal, optional)
    RAG_ENABLED: bool = False
    RAG_INDEX_PATH: str = str(Path("eval/results/rag/index.json"))
    RAG_TOP_K: int = 3

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
