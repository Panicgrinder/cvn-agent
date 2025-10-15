"""
API-Router für die Anwendung
"""
from fastapi import APIRouter

# Hinweis: Endpunkte werden derzeit in app.main direkt registriert.

api_router = APIRouter()

# Chat-Endpunkt einbinden
# Hinweis: Endpunkte werden derzeit in app.main direkt registriert.
# Dieser Router bleibt für mögliche künftige Modularisierung bestehen.