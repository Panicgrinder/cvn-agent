from fastapi import APIRouter
from app.schemas import StateApplyRequest, StateResponse

router = APIRouter(prefix="/state")

# In-Memory-Speicher für den Zustand
world_state = {}


@router.get("", response_model=StateResponse)
async def get_state() -> StateResponse:
    """
    Gibt den aktuellen Weltzustand zurück.
    """
    return StateResponse(state=world_state)


@router.post("/apply", response_model=StateResponse)
async def apply_state_changes(request: StateApplyRequest) -> StateResponse:
    """
    Wendet Änderungen auf den Weltzustand an und gibt den neuen Zustand zurück.
    """
    # Einfaches Update ohne tiefe Verschmelzung
    world_state.update(request.changes)
    return StateResponse(state=world_state)
