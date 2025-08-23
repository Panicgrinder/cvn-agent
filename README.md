# CVN Agent

Ein FastAPI-Backend für einen Conversational Agent, der Ollama als LLM verwendet.

## Repository-Info

- Standard-Branch: `main`

## Einrichtung

1. Python 3.12 installieren
2. Virtuelle Umgebung erstellen und aktivieren:
   ```
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```
3. Abhängigkeiten installieren:
   ```
   pip install -r requirements.txt
   ```
   Oder manuell:
   ```
   pip install fastapi uvicorn httpx python-dotenv
   ```
4. Ollama installieren und starten:
   ```
   # Windows-Installer von https://ollama.com/download/windows
   # Nach der Installation:
   ollama serve
   ```
5. LLM-Modell herunterladen:
   ```
   ollama pull llama3.1:8b
   ```

## Anwendung starten

```
uvicorn app.main:app --reload
```

## API-Endpunkte

- `GET /`: Basis-Endpunkt für Gesundheitsprüfung
- `POST /chat`: Chat-Endpunkt zum Senden von Nachrichten an das LLM

### Chat-Endpunkt verwenden

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Du bist die Chronistin. Stell dich kurz vor.\"}]}"
```

Oder mit PowerShell:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method Post -Body '{"messages":[{"role":"user","content":"Du bist die Chronistin. Stell dich kurz vor."}]}' -ContentType "application/json"
```

## Swagger-Dokumentation

Zugriff auf die API-Dokumentation unter:
```
http://127.0.0.1:8000/docs
```