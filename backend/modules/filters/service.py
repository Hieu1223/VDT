from common.enums import Priority, TicketStatus, UserRole
from persistence.db import db


async def get_ticket_filter_options() -> dict:
    tags_cursor = db.tags.find({}, {"_id": 0, "name": 1, "color": 1})
    technicians_cursor = db.users.find(
        {"role": {"$in": [UserRole.TECHNICIAN_HUMAN.value, UserRole.TECHNICIAN_VIRTUAL.value]}},
        {"_id": 0, "id": 1, "username": 1, "full_name": 1},
    )
    return {
        "statuses": [s.value for s in TicketStatus],
        "priorities": [p.value for p in Priority],
        "tags": [t async for t in tags_cursor],
        "technicians": [t async for t in technicians_cursor],
    }
