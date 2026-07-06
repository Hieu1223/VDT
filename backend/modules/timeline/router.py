from fastapi import APIRouter, Depends, Query

from common.enums import UserRole
from gateway.deps import require_roles
from modules.timeline import service

router = APIRouter(prefix="/timeline", tags=["timeline"], dependencies=[Depends(require_roles(UserRole.ADMIN.value))])


@router.get("")
async def timeline(ticket_id: str | None = Query(default=None), limit: int = Query(default=200, le=500)):
    return await service.list_events(ticket_id=ticket_id, limit=limit)
