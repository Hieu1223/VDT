from fastapi import APIRouter, Depends

from gateway.deps import get_current_user
from modules.notifications import service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def my_notifications(user: dict = Depends(get_current_user)):
    return await service.list_my_notifications(user["id"])


@router.post("/{notification_id}/read")
async def read_one(notification_id: str, user: dict = Depends(get_current_user)):
    await service.mark_read(user["id"], notification_id)
    return {"detail": "marked read"}


@router.post("/read-all")
async def read_all(user: dict = Depends(get_current_user)):
    await service.mark_all_read(user["id"])
    return {"detail": "all marked read"}
