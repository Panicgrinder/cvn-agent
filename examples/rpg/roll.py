import random
import re
from fastapi import APIRouter, HTTPException

from .models import RollRequest, RollResponse

router = APIRouter(prefix="/roll")


@router.post("", response_model=RollResponse)
async def roll_dice(request: RollRequest) -> RollResponse:
    try:
        expression = request.dice_expression
        pattern = r'^(\d*)d(\d+)([+-]\d+)?$'
        match = re.match(pattern, expression)

        if not match:
            raise HTTPException(status_code=400, detail="Ungültiger Würfelausdruck")

        num_dice = int(match.group(1)) if match.group(1) else 1
        dice_type = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0

        if num_dice < 1 or num_dice > 100 or dice_type < 2 or dice_type > 100:
            raise HTTPException(
                status_code=400,
                detail="Würfelanzahl und -typ müssen zwischen 1-100 bzw. 2-100 liegen",
            )

        dice_results = [random.randint(1, dice_type) for _ in range(num_dice)]
        total = sum(dice_results) + modifier

        return RollResponse(
            expression=expression,
            result=total,
            details=dice_results,
            reason=request.reason,
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Fehler beim Würfeln: {str(e)}")
