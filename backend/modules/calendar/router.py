"""Admin-configurable global business calendar, used for business-hours SLA math."""
from fastapi import APIRouter, Depends

from common.enums import UserRole
from gateway.deps import require_roles
from modules.calendar import service
from modules.calendar.schemas import UpdateBusinessCalendarRequest

router = APIRouter(prefix="/calendar", tags=["calendar"], dependencies=[Depends(require_roles(UserRole.ADMIN.value))])


@router.get("")
async def get_calendar():
    return await service.get_calendar()


@router.put("")
async def update_calendar(payload: UpdateBusinessCalendarRequest):
    return await service.update_calendar(payload.model_dump())
