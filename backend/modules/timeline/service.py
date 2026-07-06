from persistence.db import db, serialize_doc


async def list_events(ticket_id: str | None = None, limit: int = 200) -> list[dict]:
    query = {}
    if ticket_id:
        query["ticket_id"] = ticket_id
    cursor = db.events.find(query).sort("created_at", -1).limit(limit)
    return [serialize_doc(e) async for e in cursor]
