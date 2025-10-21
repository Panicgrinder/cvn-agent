# syntax=docker/dockerfile:1.7
# CVN Agent application image (FastAPI + Uvicorn)

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install minimal OS deps
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (better cache)
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app ./app
COPY run_server.py ./run_server.py
COPY pyrightconfig.json ./pyrightconfig.json
COPY pytest.ini ./pytest.ini

# Create non-root user
RUN useradd -m -u 10001 cvn
USER cvn

EXPOSE 8000

# Default environment (override via compose/env)
# OLLAMA_HOST should point to the Ollama service URL, e.g. http://ollama:11434
ENV OLLAMA_HOST="http://localhost:11434" \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000

# Start the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
