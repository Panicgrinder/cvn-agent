from fastapi import APIRouter

router = APIRouter(prefix="/health")


@router.get("")
async def health_check():
    """
    Einfacher Health-Check-Endpoint für Monitoring und Statusabfragen.
    """
    return {"status": "ok"}
