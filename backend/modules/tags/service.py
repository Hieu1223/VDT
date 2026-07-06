from datetime import datetime, timezone

from common.enums import EventDomain, EventType
from common.errors import ConflictError, NotFoundError
from common.events import emit_event
from modules.tickets.service import get_ticket_or_404
from persistence.db import db, new_id, serialize_doc


async def list_tags() -> list[dict]:
    cursor = db.tags.find({}).sort("name", 1)
    return [serialize_doc(t) async for t in cursor]


async def create_tag(payload) -> dict:
    existing = await db.tags.find_one({"name": payload.name.lower()})
    if existing:
        raise ConflictError("Tag already exists")
    tag = {"id": new_id(), "name": payload.name.lower(), "color": payload.color, "created_at": datetime.now(timezone.utc)}
    doc = dict(tag)
    doc["_id"] = tag["id"]
    await db.tags.insert_one(doc)
    return tag


async def delete_tag(tag_id: str) -> None:
    tag = await db.tags.find_one({"id": tag_id})
    if not tag:
        raise NotFoundError("Tag not found")
    await db.tags.delete_one({"id": tag_id})
    await db.tickets.update_many({}, {"$pull": {"tags": tag["name"]}})


async def attach_tag(bus, user: dict, ticket_id: str, tag_name: str) -> dict:
    await get_ticket_or_404(ticket_id)
    tag_name = tag_name.lower()
    if not await db.tags.find_one({"name": tag_name}):
        tag = {"id": new_id(), "name": tag_name, "color": "#52525B", "created_at": datetime.now(timezone.utc)}
        doc = dict(tag)
        doc["_id"] = tag["id"]
        await db.tags.insert_one(doc)
    await db.tickets.update_one({"id": ticket_id}, {"$addToSet": {"tags": tag_name}, "$set": {"updated_at": datetime.now(timezone.utc)}})
    await emit_event(
        bus, EventDomain.TAG.value, EventType.TAG_ADDED.value,
        {"ticket_id": ticket_id, "tag": tag_name}, actor_id=user["id"], ticket_id=ticket_id,
    )
    return await get_ticket_or_404(ticket_id)


async def remove_tag(bus, user: dict, ticket_id: str, tag_name: str) -> dict:
    await get_ticket_or_404(ticket_id)
    tag_name = tag_name.lower()
    await db.tickets.update_one({"id": ticket_id}, {"$pull": {"tags": tag_name}, "$set": {"updated_at": datetime.now(timezone.utc)}})
    await emit_event(
        bus, EventDomain.TAG.value, EventType.TAG_REMOVED.value,
        {"ticket_id": ticket_id, "tag": tag_name}, actor_id=user["id"], ticket_id=ticket_id,
    )
    return await get_ticket_or_404(ticket_id)
