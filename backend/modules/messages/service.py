import mimetypes
import os
from datetime import datetime, timezone

from fastapi import UploadFile

from common.config import ROOT_DIR, settings
from common.enums import EventDomain, EventType, UserRole
from common.errors import ForbiddenError, NotFoundError
from common.events import emit_event
from modules.tickets.service import can_view_ticket, get_ticket_or_404, record_first_response
from persistence.db import db, new_id, serialize_doc

UPLOAD_ROOT = ROOT_DIR / settings.upload_dir


async def list_messages(user: dict, ticket_id: str) -> list[dict]:
    ticket = await get_ticket_or_404(ticket_id)
    if not can_view_ticket(user, ticket):
        raise ForbiddenError("You cannot view this ticket's chat room")
    cursor = db.messages.find({"ticket_id": ticket_id}).sort("created_at", 1)
    return [serialize_doc(m) async for m in cursor]


async def send_message(bus, user: dict, ticket_id: str, payload) -> dict:
    ticket = await get_ticket_or_404(ticket_id)
    if not can_view_ticket(user, ticket):
        raise ForbiddenError("You cannot post in this ticket's chat room")

    reply_preview = None
    if payload.reply_to_message_id:
        original = await db.messages.find_one({"id": payload.reply_to_message_id})
        if original:
            reply_preview = {
                "id": original["id"],
                "sender_username": original["sender_username"],
                "content": original["content"][:140],
            }

    now = datetime.now(timezone.utc)
    message = {
        "id": new_id(),
        "ticket_id": ticket_id,
        "sender_id": user["id"],
        "sender_username": user["username"],
        "sender_role": user["role"],
        "content": payload.content,
        "attachments": [a.model_dump() for a in payload.attachments],
        "reply_to_message_id": payload.reply_to_message_id,
        "reply_preview": reply_preview,
        "edited_at": None,
        "deleted_at": None,
        "created_at": now,
    }
    doc = dict(message)
    doc["_id"] = message["id"]
    await db.messages.insert_one(doc)

    if user["role"] in (UserRole.TECHNICIAN_HUMAN.value, UserRole.TECHNICIAN_VIRTUAL.value):
        await record_first_response(bus, ticket_id)

    await emit_event(
        bus, EventDomain.MESSAGE.value, EventType.MESSAGE_SENT.value,
        {
            "ticket_id": ticket_id, "message_id": message["id"], "sender_id": user["id"],
            "sender_username": user["username"], "content": payload.content,
            "requester_id": ticket["requester_id"], "assignee_id": ticket.get("assignee_id"),
        },
        actor_id=user["id"], ticket_id=ticket_id,
    )
    return message


async def save_upload(ticket_id: str, file: UploadFile) -> dict:
    await get_ticket_or_404(ticket_id)
    room_dir = UPLOAD_ROOT / ticket_id
    room_dir.mkdir(parents=True, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1]
    safe_name = f"{new_id()}{ext}"
    dest_path = room_dir / safe_name

    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    return {
        "filename": file.filename,
        "url": f"/uploads/rooms/{ticket_id}/{safe_name}",
        "content_type": file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream",
        "size": len(content),
    }


async def edit_message(bus, user: dict, ticket_id: str, message_id: str, content: str) -> dict:
    message = await db.messages.find_one({"id": message_id, "ticket_id": ticket_id})
    if not message:
        raise NotFoundError("Message not found")
    if message["sender_id"] != user["id"]:
        raise ForbiddenError("You can only edit your own messages")
    if message.get("deleted_at"):
        raise ForbiddenError("Cannot edit a deleted message")

    now = datetime.now(timezone.utc)
    await db.messages.update_one({"id": message_id}, {"$set": {"content": content, "edited_at": now}})
    await emit_event(
        bus, EventDomain.MESSAGE.value, EventType.MESSAGE_EDITED.value,
        {"ticket_id": ticket_id, "message_id": message_id}, actor_id=user["id"], ticket_id=ticket_id,
    )
    return serialize_doc(await db.messages.find_one({"id": message_id}))


async def delete_message(bus, user: dict, ticket_id: str, message_id: str) -> dict:
    message = await db.messages.find_one({"id": message_id, "ticket_id": ticket_id})
    if not message:
        raise NotFoundError("Message not found")
    if message["sender_id"] != user["id"] and user["role"] != UserRole.ADMIN.value:
        raise ForbiddenError("You can only delete your own messages")

    now = datetime.now(timezone.utc)
    await db.messages.update_one({"id": message_id}, {"$set": {"deleted_at": now, "content": "[deleted]", "attachments": []}})
    await emit_event(
        bus, EventDomain.MESSAGE.value, EventType.MESSAGE_DELETED.value,
        {"ticket_id": ticket_id, "message_id": message_id}, actor_id=user["id"], ticket_id=ticket_id,
    )
    return serialize_doc(await db.messages.find_one({"id": message_id}))
