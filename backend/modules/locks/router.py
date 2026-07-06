from fastapi import APIRouter, Depends

from common.enums import UserRole
from gateway.deps import get_bus, get_current_user, require_roles
from modules.locks import service

router = APIRouter(prefix="/tickets", tags=["locks"])

TECHNICIAN_OR_ADMIN = [UserRole.TECHNICIAN_HUMAN.value, UserRole.TECHNICIAN_VIRTUAL.value, UserRole.ADMIN.value]


@router.post("/{ticket_id}/lock", dependencies=[Depends(require_roles(*TECHNICIAN_OR_ADMIN))])
async def acquire(ticket_id: str, user: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.acquire_lock(bus, ticket_id, user)


@router.post("/{ticket_id}/lock/refresh", dependencies=[Depends(require_roles(*TECHNICIAN_OR_ADMIN))])
async def refresh(ticket_id: str, user: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.refresh_lock(bus, ticket_id, user)


@router.delete("/{ticket_id}/lock", dependencies=[Depends(require_roles(*TECHNICIAN_OR_ADMIN))])
async def release(ticket_id: str, user: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.release_lock(bus, ticket_id, user, force=False)


@router.post("/{ticket_id}/lock/force-release", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def force_release(ticket_id: str, user: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.release_lock(bus, ticket_id, user, force=True)
