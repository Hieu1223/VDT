from common.enums import TicketStatus
from persistence.db import db, serialize_doc


async def get_board() -> dict:
    columns = {status.value: [] for status in TicketStatus}
    cursor = db.tickets.find({}).sort("updated_at", -1)
    async for ticket in cursor:
        ticket = serialize_doc(ticket)
        columns[ticket["status"]].append({
            "id": ticket["id"],
            "subject": ticket["subject"],
            "priority": ticket["priority"],
            "assignee_username": ticket.get("assignee_username"),
            "requester_username": ticket["requester_username"],
            "tags": ticket.get("tags", []),
            "updated_at": ticket["updated_at"],
        })
    return columns
