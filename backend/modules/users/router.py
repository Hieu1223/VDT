from fastapi import APIRouter, Depends, Query

from common.enums import UserRole
from common.ws.manager import manager as ws_manager
from gateway.deps import get_bus, get_current_user, require_roles
from modules.users import service
from modules.users.schemas import AdminCreateUserRequest, ChangePasswordRequest, UpdateProfileRequest, UpdateUserStatusRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me")
async def update_my_profile(payload: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    return await service.update_profile(user, payload)


@router.post("/me/change-password")
async def change_my_password(payload: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    await service.change_password(user, payload)
    return {"detail": "password updated"}


@router.post("/me/heartbeat")
async def heartbeat(user: dict = Depends(get_current_user)):
    became_online = await service.heartbeat(user["id"])
    if became_online:
        await ws_manager.broadcast_to_roles(
            ["admin"], {"kind": "presence", "data": {"user_id": user["id"], "username": user["username"], "online": True}}
        )
    return {"online": True}


@router.get("/technicians")
async def technicians(user: dict = Depends(get_current_user)):
    return await service.list_technicians()


@router.get("", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def admin_list_users(
    role: str | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    online: bool | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
):
    return await service.list_users(role=role, status=status, search=search, online=online, date_from=date_from, date_to=date_to, page=page, page_size=page_size)


@router.post("", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def admin_create_user(payload: AdminCreateUserRequest, admin: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.admin_create_user(bus, admin, payload)


@router.patch("/{user_id}/status", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def admin_update_user_status(user_id: str, payload: UpdateUserStatusRequest, admin: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.update_user_status(bus, admin, user_id, payload.status)
