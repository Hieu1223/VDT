from datetime import datetime, timezone

from common.business_calendar import add_business_minutes, get_business_calendar
from common.enums import EventDomain, EventType, TicketStatus, UserRole
from common.errors import ForbiddenError, NotFoundError, ConflictError
from common.events import emit_event
from modules.locks.service import get_lock
from modules.tickets.sla_seed import get_sla_policy, resolve_priority_from_db
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


def _build_date_query(date_from: str | None, date_to: str | None) -> dict:
    q: dict = {}
    if date_from:
        q["$gte"] = datetime.fromisoformat(date_from)
    if date_to:
        q["$lte"] = datetime.fromisoformat(date_to)
    return q


def _as_aware(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value and value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


def sla_elapsed_pct(ticket: dict) -> float | None:
    """% of the resolve-SLA window elapsed so far (used for the 'SLA at-risk' slider filter)."""
    sla = ticket.get("sla")
    if not sla or not sla.get("resolve_due_at"):
        return None
    due = _as_aware(sla["resolve_due_at"])
    created = _as_aware(ticket["created_at"])
    window = (due - created).total_seconds()
    if window <= 0:
        return None
    elapsed = (datetime.now(timezone.utc) - created).total_seconds()
    return max(0.0, (elapsed / window) * 100)


async def create_ticket(bus, actor: dict, payload) -> dict:
    priority = await resolve_priority_from_db(payload.impact, payload.urgency)
    policy = await get_sla_policy(priority)
    calendar = await get_business_calendar()
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
        "requester_id": actor["id"],
        "requester_username": actor["username"],
        "assignee_id": None,
        "assignee_username": None,
        "tags": [],
        "previous_status": None,
        "escalation_pending": False,
        "sla": {
            "first_response_due_at": add_business_minutes(now, policy["first_response_minutes"], calendar),
            "resolve_due_at": add_business_minutes(now, policy["resolve_minutes"], calendar),
            "first_responded_at": None,
            "resolved_at": None,
            "first_response_breached": False,
            "resolve_breached": False,
            "first_response_near_breach": False,
            "resolve_near_breach": False,
        },
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
        {"ticket_id": ticket["id"], "subject": ticket["subject"], "priority": priority, "requester_id": actor["id"]},
        actor_id=actor["id"], ticket_id=ticket["id"],
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


async def list_my_tickets(user: dict, tag: str | None = None, date_from: str | None = None, date_to: str | None = None) -> list[dict]:
    query: dict = {"requester_id": user["id"]}
    if tag:
        query["tags"] = tag
    date_query = _build_date_query(date_from, date_to)
    if date_query:
        query["created_at"] = date_query
    cursor = db.tickets.find(query).sort("created_at", -1)
    return [strip_sla_if_unauthorized(serialize_doc(t), user["role"]) async for t in cursor]


async def list_all_tickets(
    status: str | None = None,
    priority: str | None = None,
    assignee_id: str | None = None,
    search: str | None = None,
    tag: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sla_min_pct: float | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    query: dict = {}
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if assignee_id:
        query["assignee_id"] = None if assignee_id == "unassigned" else assignee_id
    if search:
        query["subject"] = {"$regex": search, "$options": "i"}
    if tag:
        query["tags"] = tag
    date_query = _build_date_query(date_from, date_to)
    if date_query:
        query["created_at"] = date_query

    if sla_min_pct is None:
        # No derived/computed filter active - paginate straight at the DB
        # level (indexed skip/limit) instead of materializing every match.
        total = await db.tickets.count_documents(query)
        skip = (page - 1) * page_size
        cursor = db.tickets.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        tickets = [serialize_doc(t) async for t in cursor]
        return {"items": tickets, "total": total, "page": page, "page_size": page_size}

    # sla_min_pct is a derived value (depends on the business calendar and
    # "now") that isn't stored on the document, so it can't be a Mongo query
    # operator - materialize just the already-narrowed match set (every
    # other filter above still ran at the DB level) and paginate in Python.
    cursor = db.tickets.find(query).sort("created_at", -1)
    tickets = [serialize_doc(t) async for t in cursor]
    tickets = [t for t in tickets if (pct := sla_elapsed_pct(t)) is not None and pct >= sla_min_pct]
    total = len(tickets)
    start = (page - 1) * page_size
    return {"items": tickets[start:start + page_size], "total": total, "page": page, "page_size": page_size}


async def list_queue(
    technician: dict,
    tag: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sla_min_pct: float | None = None,
) -> list[dict]:
    """Actionable tickets: assigned to me, or unassigned & open, excluding resolved/rejected/closed."""
    query: dict = {
        "status": {"$in": [TicketStatus.NEW.value, TicketStatus.ASSIGNED.value, TicketStatus.IN_PROGRESS.value, TicketStatus.ESCALATED.value]},
        "$or": [{"assignee_id": technician["id"]}, {"assignee_id": None}],
    }
    if tag:
        query["tags"] = tag
    date_query = _build_date_query(date_from, date_to)
    if date_query:
        query["created_at"] = date_query
    cursor = db.tickets.find(query).sort("created_at", 1)
    tickets = [serialize_doc(t) async for t in cursor]
    if sla_min_pct is not None:
        tickets = [t for t in tickets if (pct := sla_elapsed_pct(t)) is not None and pct >= sla_min_pct]
    return tickets


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


async def unassign_ticket(bus, ticket_id: str, reason: str = "technician_offline") -> dict:
    """Clears the assignee (e.g. because they went offline with no online
    replacement available) so the ticket falls back into the unassigned
    queue - visible to every technician's Queue and filterable on the
    Admin > All Tickets page."""
    now = datetime.now(timezone.utc)
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"assignee_id": None, "assignee_username": None, "updated_at": now}},
    )
    ticket = await get_ticket_or_404(ticket_id)
    await emit_event(
        bus, EventDomain.TICKET.value, EventType.TICKET_UNASSIGNED.value,
        {"ticket_id": ticket_id, "reason": reason}, ticket_id=ticket_id,
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
    lock = await get_lock(ticket_id)
    if lock["locked_by"] and lock["locked_by"] != technician["id"]:
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
    lock = await get_lock(ticket_id)
    if lock["locked_by"] and lock["locked_by"] != technician["id"]:
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
