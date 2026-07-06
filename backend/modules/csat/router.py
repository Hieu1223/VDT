from fastapi import APIRouter, Depends

from gateway.deps import get_bus, get_current_user
from modules.csat import service
from modules.csat.schemas import SubmitCsatRequest

router = APIRouter(prefix="/csat", tags=["csat"])


@router.get("/{ticket_id}")
async def get_survey(ticket_id: str, user: dict = Depends(get_current_user)):
    return await service.get_survey(ticket_id)


@router.post("/{ticket_id}")
async def submit(ticket_id: str, payload: SubmitCsatRequest, user: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.submit_csat(bus, user, ticket_id, payload.rating, payload.comment)
