from fastapi import APIRouter, Depends, Query

from common.enums import UserRole
from gateway.deps import require_roles
from modules.monitor import service

router = APIRouter(prefix="/monitor", tags=["monitor"], dependencies=[Depends(require_roles(UserRole.ADMIN.value))])


@router.get("/users")
async def users(online: bool | None = Query(default=None)):
    return await service.monitor_users(online=online)


@router.get("/tickets")
async def tickets():
    return await service.monitor_tickets()
