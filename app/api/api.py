"""
API-Router für die Anwendung
"""
from fastapi import APIRouter

from .endpoints import chat

api_router = APIRouter()

# Chat-Endpunkt einbinden
api_router.include_router(chat.router, tags=["chat"])