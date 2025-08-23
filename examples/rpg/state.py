from fastapi import APIRouter
from .models import StateApplyRequest, StateResponse

router = APIRouter(prefix="/state")

# In-Memory-Speicher für den Zustand
world_state: dict[str, object] = {}


@router.get("", response_model=StateResponse)
async def get_state() -> StateResponse:
    return StateResponse(state=world_state)


@router.post("/apply", response_model=StateResponse)
async def apply_state_changes(request: StateApplyRequest) -> StateResponse:
    world_state.update(request.changes)
    return StateResponse(state=world_state)
