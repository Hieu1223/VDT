from fastapi import APIRouter, Depends

from common.enums import UserRole
from gateway.deps import get_bus, get_current_user, require_roles
from modules.tags import service
from modules.tags.schemas import AttachTagRequest, CreateTagRequest

router = APIRouter(tags=["tags"])

TECHNICIAN_OR_ADMIN = [UserRole.TECHNICIAN_HUMAN.value, UserRole.TECHNICIAN_VIRTUAL.value, UserRole.ADMIN.value]


@router.get("/tags")
async def list_tags(user: dict = Depends(get_current_user)):
    return await service.list_tags()


@router.post("/tags", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def create_tag(payload: CreateTagRequest):
    return await service.create_tag(payload)


@router.delete("/tags/{tag_id}", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def delete_tag(tag_id: str):
    await service.delete_tag(tag_id)
    return {"detail": "deleted"}


@router.post("/tickets/{ticket_id}/tags", dependencies=[Depends(require_roles(*TECHNICIAN_OR_ADMIN))])
async def attach_tag(ticket_id: str, payload: AttachTagRequest, user: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.attach_tag(bus, user, ticket_id, payload.tag)


@router.delete("/tickets/{ticket_id}/tags/{tag_name}", dependencies=[Depends(require_roles(*TECHNICIAN_OR_ADMIN))])
async def remove_tag(ticket_id: str, tag_name: str, user: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.remove_tag(bus, user, ticket_id, tag_name)
