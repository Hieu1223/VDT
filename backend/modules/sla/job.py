import logging
from datetime import datetime, timezone

from common.config import settings
from common.enums import EventDomain, EventType, OPEN_TICKET_STATUSES
from common.events import emit_event
from persistence.db import db

logger = logging.getLogger("sla.job")


def _aware(dt):
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def _check_first_response(bus, ticket: dict, now: datetime) -> None:
    sla = ticket["sla"]
    if sla.get("first_responded_at"):
        return
    due = _aware(sla.get("first_response_due_at"))
    created = _aware(ticket["created_at"])
    if not due:
        return

    if now >= due and not sla.get("first_response_breached"):
        await db.tickets.update_one({"id": ticket["id"]}, {"$set": {"sla.first_response_breached": True}})
        await emit_event(bus, EventDomain.SLA.value, EventType.SLA_BREACHED_FIRST_RESPONSE.value,
                          {"ticket_id": ticket["id"], "assignee_id": ticket.get("assignee_id")}, ticket_id=ticket["id"])
        return

    window = (due - created).total_seconds()
    elapsed = (now - created).total_seconds()
    if window > 0 and elapsed / window >= settings.sla_near_breach_ratio and not sla.get("first_response_near_breach"):
        await db.tickets.update_one({"id": ticket["id"]}, {"$set": {"sla.first_response_near_breach": True}})
        await emit_event(bus, EventDomain.SLA.value, EventType.SLA_NEAR_BREACH_FIRST_RESPONSE.value,
                          {"ticket_id": ticket["id"], "assignee_id": ticket.get("assignee_id")}, ticket_id=ticket["id"])


async def _check_resolve(bus, ticket: dict, now: datetime) -> None:
    sla = ticket["sla"]
    if sla.get("resolved_at"):
        return
    due = _aware(sla.get("resolve_due_at"))
    created = _aware(ticket["created_at"])
    if not due:
        return

    if now >= due and not sla.get("resolve_breached"):
        await db.tickets.update_one({"id": ticket["id"]}, {"$set": {"sla.resolve_breached": True}})
        await emit_event(bus, EventDomain.SLA.value, EventType.SLA_BREACHED_RESOLVE.value,
                          {"ticket_id": ticket["id"], "assignee_id": ticket.get("assignee_id")}, ticket_id=ticket["id"])
        return

    window = (due - created).total_seconds()
    elapsed = (now - created).total_seconds()
    if window > 0 and elapsed / window >= settings.sla_near_breach_ratio and not sla.get("resolve_near_breach"):
        await db.tickets.update_one({"id": ticket["id"]}, {"$set": {"sla.resolve_near_breach": True}})
        await emit_event(bus, EventDomain.SLA.value, EventType.SLA_NEAR_BREACH_RESOLVE.value,
                          {"ticket_id": ticket["id"], "assignee_id": ticket.get("assignee_id")}, ticket_id=ticket["id"])


async def run_sla_check(bus) -> int:
    now = datetime.now(timezone.utc)
    cursor = db.tickets.find({"status": {"$in": list(OPEN_TICKET_STATUSES)}})
    count = 0
    async for ticket in cursor:
        await _check_first_response(bus, ticket, now)
        await _check_resolve(bus, ticket, now)
        count += 1
    return count
