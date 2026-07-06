from fastapi import APIRouter, Depends

from gateway.deps import get_current_user
from modules.filters import service

router = APIRouter(prefix="/filters", tags=["filters"])


@router.get("/tickets")
async def ticket_filter_options(user: dict = Depends(get_current_user)):
    return await service.get_ticket_filter_options()
