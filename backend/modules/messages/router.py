from fastapi import APIRouter, Depends, File, UploadFile

from gateway.deps import get_bus, get_current_user
from modules.messages import service
from modules.messages.schemas import EditMessageRequest, SendMessageRequest

router = APIRouter(prefix="/tickets/{ticket_id}/messages", tags=["messages"])


@router.get("")
async def list_messages(ticket_id: str, user: dict = Depends(get_current_user)):
    return await service.list_messages(user, ticket_id)


@router.post("")
async def send_message(ticket_id: str, payload: SendMessageRequest, user: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.send_message(bus, user, ticket_id, payload)


@router.post("/upload")
async def upload_attachment(ticket_id: str, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    return await service.save_upload(ticket_id, file)


@router.patch("/{message_id}")
async def edit_message(ticket_id: str, message_id: str, payload: EditMessageRequest, user: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.edit_message(bus, user, ticket_id, message_id, payload.content)


@router.delete("/{message_id}")
async def delete_message(ticket_id: str, message_id: str, user: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.delete_message(bus, user, ticket_id, message_id)
