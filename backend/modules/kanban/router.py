from fastapi import APIRouter, Depends

from common.enums import UserRole
from gateway.deps import require_roles
from modules.kanban import service

router = APIRouter(prefix="/kanban", tags=["kanban"], dependencies=[Depends(require_roles(UserRole.ADMIN.value))])


@router.get("/board")
async def board():
    return await service.get_board()
