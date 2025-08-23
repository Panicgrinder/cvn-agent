#!/usr/bin/env python
"""
Startet den CVN Agent Server ohne Inhaltsfilterung.
Das System ist für ein privates postapokalyptisches Rollenspiel konzipiert,
in dem auch Szenarien mit expliziten Inhalten, Gewalt und anderen
normalerweise eingeschränkten Themen dargestellt werden können.
"""

import uvicorn
from app.core.settings import settings
import logging
import warnings

if __name__ == "__main__":
    # Basis-Logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=ResourceWarning)
    print(f"Starte CVN Agent Server auf http://localhost:8000")
    print(f"API Dokumentation: http://localhost:8000/docs")
    print(f"Verwende Modell: {settings.MODEL_NAME}")
    print(f"HINWEIS: Dieser Server läuft ohne Inhaltsfilterung für private Rollenspielzwecke.")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )