# Docker-Setup für CVN Agent

Dieses Dokument zeigt, wie du die App und Ollama lokal mit Docker startest.

## Voraussetzungen

- Docker Desktop (Windows/macOS) oder Docker Engine (Linux)
- Optional: `docker compose` CLI (bei Desktop enthalten)

## Inhalte

- `Dockerfile`: Image für die FastAPI-App (uvicorn auf Port 8000)
- `docker-compose.yml`: Startet zwei Services
  - `ollama`: LLM-Backend (Port 11434)
  - `app`: CVN Agent (Port 8000) – verbindet sich mit `ollama`
- `.dockerignore`: Verkleinert den Build-Kontext

## Schnellstart (Windows PowerShell)

1) Container starten

```powershell
# Im Repo-Verzeichnis
docker compose up -d --build
```

1) Modell für Ollama laden (einmalig)

```powershell
docker exec -it cvn-ollama ollama pull llama3.1:8b
```

1) App prüfen

```powershell
# Swagger
Start-Process http://localhost:8000/docs

# Health
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

## Konfiguration

- Die App liest Einstellungen über Umgebungsvariablen (siehe `app/core/settings.py`).
- Standardmäßig zeigt `docker-compose.yml` `OLLAMA_HOST` auf `http://ollama:11434`.
- Eigene Werte kannst du über `environment:` oder eine `.env`-Datei setzen.

Beispiele (`docker-compose.yml`, Service `app`):

```yaml
services:
  app:
    environment:
      OLLAMA_HOST: http://ollama:11434
      BACKEND_CORS_ORIGINS: "[\"http://localhost:3000\"]"
```

## Nützliche Befehle

```powershell
# Logs ansehen
docker compose logs -f app

# Container neu bauen
docker compose build --no-cache app

# Modelle auflisten
docker exec -it cvn-ollama ollama list
```

## Hinweise & Troubleshooting

- Warte nach `docker compose up` wenige Sekunden, bis `ollama` erreichbar ist.
- Wenn `ollama pull` zu groß/langsam ist, verwende ein kleineres Modell (z. B. `llama3.1:8b` oder Tiny‑Modelle).
- Ports können geändert werden; passe ggf. Firewall/Sicherheitssoftware an.
- Bei Bedarf kannst du `ollama`-Daten persistent halten (Volume `ollama-data`).

## Stoppen & Entfernen

```powershell
# Stoppen
docker compose down

# Stoppen + Volumes löschen (auch ollama-Modelle)
docker compose down -v
```
