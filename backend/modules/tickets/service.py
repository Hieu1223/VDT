from datetime import datetime, timedelta, timezone

from common.enums import EventDomain, EventType, TicketStatus, UserRole
from common.errors import ForbiddenError, NotFoundError, ConflictError
from common.events import emit_event
from modules.tickets.sla_seed import get_sla_policy, resolve_priority
from persistence.db import db, new_id, serialize_doc

TECHNICIAN_OR_ADMIN = {UserRole.TECHNICIAN_HUMAN.value, UserRole.TECHNICIAN_VIRTUAL.value, UserRole.ADMIN.value}


def strip_sla_if_unauthorized(ticket: dict, viewer_role: str) -> dict:
    if viewer_role not in TECHNICIAN_OR_ADMIN:
        ticket = dict(ticket)
        ticket["sla"] = None
    return ticket


def can_view_ticket(user: dict, ticket: dict) -> bool:
    if user["role"] == UserRole.EMPLOYEE.value:
        return ticket["requester_id"] == user["id"]
    return True


async def create_ticket(bus, requester: dict, payload) -> dict:
    priority = resolve_priority(payload.impact, payload.urgency)
    policy = await get_sla_policy(priority)
    now = datetime.now(timezone.utc)

    ticket = {
        "id": new_id(),
        "subject": payload.subject,
        "description": payload.description,
        "category": payload.category,
        "impact": payload.impact,
        "urgency": payload.urgency,
        "priority": priority,
        "status": TicketStatus.NEW.value,
        "requester_id": requester["id"],
        "requester_username": requester["username"],
        "assignee_id": None,
        "assignee_username": None,
        "tags": [],
        "previous_status": None,
        "escalation_pending": False,
        "sla": {
            "first_response_due_at": now + timedelta(minutes=policy["first_response_minutes"]),
            "resolve_due_at": now + timedelta(minutes=policy["resolve_minutes"]),
            "first_responded_at": None,
            "resolved_at": None,
            "first_response_breached": False,
            "resolve_breached": False,
            "first_response_near_breach": False,
            "resolve_near_breach": False,
        },
        "lock": {"locked_by": None, "locked_by_username": None, "locked_at": None, "expires_at": None},
        "resolution_note": None,
        "rejection_reason": None,
        "created_at": now,
        "updated_at": now,
    }
    doc = dict(ticket)
    doc["_id"] = ticket["id"]
    await db.tickets.insert_one(doc)

    await emit_event(
        bus, EventDomain.TICKET.value, EventType.TICKET_CREATED.value,
        {"ticket_id": ticket["id"], "subject": ticket["subject"], "priority": priority, "requester_id": requester["id"]},
        actor_id=requester["id"], ticket_id=ticket["id"],
    )
    return ticket


async def get_ticket_or_404(ticket_id: str) -> dict:
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise NotFoundError("Ticket not found")
    return serialize_doc(ticket)


async def get_ticket_for_viewer(user: dict, ticket_id: str) -> dict:
    ticket = await get_ticket_or_404(ticket_id)
    if not can_view_ticket(user, ticket):
        raise ForbiddenError("You cannot view this ticket")
    return strip_sla_if_unauthorized(ticket, user["role"])


async def list_my_tickets(user: dict) -> list[dict]:
    cursor = db.tickets.find({"requester_id": user["id"]}).sort("created_at", -1)
    return [strip_sla_if_unauthorized(serialize_doc(t), user["role"]) async for t in cursor]


async def list_all_tickets(status: str | None = None, priority: str | None = None, assignee_id: str | None = None, search: str | None = None) -> list[dict]:
    query = {}
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if assignee_id:
        query["assignee_id"] = assignee_id
    if search:
        query["subject"] = {"$regex": search, "$options": "i"}
    cursor = db.tickets.find(query).sort("created_at", -1)
    return [serialize_doc(t) async for t in cursor]


async def list_queue(technician: dict) -> list[dict]:
    """Actionable tickets: assigned to me, or unassigned & open, excluding resolved/rejected/closed."""
    cursor = db.tickets.find({
        "status": {"$in": [TicketStatus.NEW.value, TicketStatus.ASSIGNED.value, TicketStatus.IN_PROGRESS.value, TicketStatus.ESCALATED.value]},
        "$or": [{"assignee_id": technician["id"]}, {"assignee_id": None}],
    }).sort("created_at", 1)
    return [serialize_doc(t) async for t in cursor]


async def set_assignee(bus, ticket_id: str, assignee: dict, actor_id: str | None = None) -> dict:
    now = datetime.now(timezone.utc)
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"assignee_id": assignee["id"], "assignee_username": assignee["username"], "status": TicketStatus.ASSIGNED.value, "updated_at": now}},
    )
    ticket = await get_ticket_or_404(ticket_id)
    await emit_event(
        bus, EventDomain.TICKET.value, EventType.TICKET_ASSIGNED.value,
        {"ticket_id": ticket_id, "assignee_id": assignee["id"], "assignee_username": assignee["username"]},
        actor_id=actor_id, ticket_id=ticket_id,
    )
    return ticket


async def record_first_response(bus, ticket_id: str) -> None:
    ticket = await get_ticket_or_404(ticket_id)
    if ticket["sla"]["first_responded_at"]:
        return
    now = datetime.now(timezone.utc)
    updates = {"sla.first_responded_at": now, "updated_at": now}
    if ticket["status"] == TicketStatus.ASSIGNED.value:
        updates["status"] = TicketStatus.IN_PROGRESS.value
    await db.tickets.update_one({"id": ticket_id}, {"$set": updates})


async def resolve_ticket(bus, technician: dict, ticket_id: str, resolution_note: str) -> dict:
    ticket = await get_ticket_or_404(ticket_id)
    if ticket["lock"]["locked_by"] and ticket["lock"]["locked_by"] != technician["id"]:
        raise ConflictError("Ticket is locked by another technician")
    if ticket["status"] in (TicketStatus.RESOLVED.value, TicketStatus.REJECTED.value, TicketStatus.CLOSED.value):
        raise ConflictError("Ticket is already closed")

    now = datetime.now(timezone.utc)
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"status": TicketStatus.RESOLVED.value, "resolution_note": resolution_note, "sla.resolved_at": now, "updated_at": now}},
    )
    await emit_event(
        bus, EventDomain.TICKET.value, EventType.TICKET_RESOLVED.value,
        {"ticket_id": ticket_id, "resolution_note": resolution_note, "requester_id": ticket["requester_id"], "assignee_id": technician["id"]},
        actor_id=technician["id"], ticket_id=ticket_id,
    )
    return await get_ticket_or_404(ticket_id)


async def reject_ticket(bus, technician: dict, ticket_id: str, rejection_reason: str) -> dict:
    ticket = await get_ticket_or_404(ticket_id)
    if ticket["lock"]["locked_by"] and ticket["lock"]["locked_by"] != technician["id"]:
        raise ConflictError("Ticket is locked by another technician")
    if ticket["status"] in (TicketStatus.RESOLVED.value, TicketStatus.REJECTED.value, TicketStatus.CLOSED.value):
        raise ConflictError("Ticket is already closed")

    now = datetime.now(timezone.utc)
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"status": TicketStatus.REJECTED.value, "rejection_reason": rejection_reason, "updated_at": now}},
    )
    await emit_event(
        bus, EventDomain.TICKET.value, EventType.TICKET_REJECTED.value,
        {"ticket_id": ticket_id, "rejection_reason": rejection_reason, "requester_id": ticket["requester_id"]},
        actor_id=technician["id"], ticket_id=ticket_id,
    )
    return await get_ticket_or_404(ticket_id)
