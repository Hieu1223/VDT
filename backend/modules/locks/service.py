from datetime import datetime, timedelta, timezone

from common.config import settings
from common.enums import EventDomain, EventType
from common.errors import ConflictError, ForbiddenError
from common.events import emit_event
from modules.tickets.service import get_ticket_or_404
from persistence.db import db


def _is_active_lock(ticket: dict) -> bool:
    lock = ticket.get("lock") or {}
    if not lock.get("locked_by"):
        return False
    expires_at = lock.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return bool(expires_at and expires_at > datetime.now(timezone.utc))


async def acquire_lock(bus, ticket_id: str, user: dict) -> dict:
    ticket = await get_ticket_or_404(ticket_id)
    if _is_active_lock(ticket) and ticket["lock"]["locked_by"] != user["id"]:
        raise ConflictError(f"Ticket is currently locked by {ticket['lock']['locked_by_username']}")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.lock_ttl_seconds)
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"lock": {"locked_by": user["id"], "locked_by_username": user["username"], "locked_at": now, "expires_at": expires_at}}},
    )
    await emit_event(
        bus, EventDomain.LOCK.value, EventType.LOCK_ACQUIRED.value,
        {"ticket_id": ticket_id, "locked_by": user["id"], "locked_by_username": user["username"]},
        actor_id=user["id"], ticket_id=ticket_id,
    )
    return await get_ticket_or_404(ticket_id)


async def refresh_lock(bus, ticket_id: str, user: dict) -> dict:
    ticket = await get_ticket_or_404(ticket_id)
    if not _is_active_lock(ticket) or ticket["lock"]["locked_by"] != user["id"]:
        raise ForbiddenError("You do not hold the lock on this ticket")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.lock_ttl_seconds)
    await db.tickets.update_one({"id": ticket_id}, {"$set": {"lock.expires_at": expires_at}})
    await emit_event(
        bus, EventDomain.LOCK.value, EventType.LOCK_REFRESHED.value,
        {"ticket_id": ticket_id, "locked_by": user["id"]}, actor_id=user["id"], ticket_id=ticket_id,
    )
    return await get_ticket_or_404(ticket_id)


async def release_lock(bus, ticket_id: str, user: dict, force: bool = False) -> dict:
    ticket = await get_ticket_or_404(ticket_id)
    lock = ticket.get("lock") or {}
    if not force and lock.get("locked_by") and lock["locked_by"] != user["id"]:
        raise ForbiddenError("You do not hold the lock on this ticket")

    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"lock": {"locked_by": None, "locked_by_username": None, "locked_at": None, "expires_at": None}}},
    )
    await emit_event(
        bus, EventDomain.LOCK.value, EventType.LOCK_RELEASED.value,
        {"ticket_id": ticket_id, "released_by": user["id"], "forced": force, "was_locked_by": lock.get("locked_by")},
        actor_id=user["id"], ticket_id=ticket_id,
    )
    return await get_ticket_or_404(ticket_id)


async def janitor_sweep(bus) -> int:
    """Release any ticket lock whose TTL has expired. Returns count released."""
    now = datetime.now(timezone.utc)
    cursor = db.tickets.find({"lock.locked_by": {"$ne": None}, "lock.expires_at": {"$lt": now}})
    count = 0
    async for ticket in cursor:
        await db.tickets.update_one(
            {"id": ticket["id"]},
            {"$set": {"lock": {"locked_by": None, "locked_by_username": None, "locked_at": None, "expires_at": None}}},
        )
        await emit_event(
            bus, EventDomain.LOCK.value, EventType.LOCK_EXPIRED.value,
            {"ticket_id": ticket["id"], "was_locked_by": ticket["lock"]["locked_by"]}, ticket_id=ticket["id"],
        )
        count += 1
    return count
