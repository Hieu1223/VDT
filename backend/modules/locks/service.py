"""Redis-backed ticket lock with TTL.

A lock is stored in Redis as a hash  `lock:{ticket_id}` containing:
    locked_by          – user id of the lock holder
    locked_by_username – display name
    locked_at          – ISO timestamp when acquired
    expires_at         – ISO timestamp when it auto-expires

The *key itself* carries a TTL equal to `settings.lock_ttl_seconds`.
When a lock is refreshed we re-SET with the same TTL so Redis handles
expiry natively — no need for a periodic sweep to delete expired locks.

The `janitor_sweep` function scans for locks that have just expired
(by looking for keys whose remaining TTL is zero or negative) so that
a LOCK_EXPIRED event can be emitted for downstream consumers.

This replaces the previous approach of storing lock data inside the
Mongo ticket document.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from common.config import settings
from common.enums import EventDomain, EventType
from common.errors import ConflictError, ForbiddenError
from common.events import emit_event
from common.redis_client import get_redis

logger = logging.getLogger("locks")

_KEY_PREFIX = "lock:"


def _key(ticket_id: str) -> str:
    return f"{_KEY_PREFIX}{ticket_id}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expires_at_iso() -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=settings.lock_ttl_seconds)).isoformat()


def _parse_hash(data: dict | None) -> dict:
    """Normalise a Redis hash (all strings) into a lock dict."""
    if not data or not data.get("locked_by"):
        return _empty_lock()
    return {
        "locked_by": data["locked_by"],
        "locked_by_username": data.get("locked_by_username"),
        "locked_at": data.get("locked_at"),
        "expires_at": data.get("expires_at"),
    }


def _empty_lock() -> dict:
    return {
        "locked_by": None,
        "locked_by_username": None,
        "locked_at": None,
        "expires_at": None,
    }


def _is_active_lock(lock: dict) -> bool:
    """Check if a parsed lock dict is still active (has owner & not expired)."""
    if not lock.get("locked_by") or not lock.get("expires_at"):
        return False
    expires_at = lock["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return bool(expires_at and expires_at > datetime.now(timezone.utc))


async def get_lock(ticket_id: str) -> dict:
    """Public helper – returns the lock dict for a ticket (from Redis)."""
    data = await get_redis().hgetall(_key(ticket_id))
    return _parse_hash(data) if data else _empty_lock()


# ---------------------------------------------------------------------------
# Public lock operations
# ---------------------------------------------------------------------------

async def acquire_lock(bus, ticket_id: str, user: dict) -> dict:
    """Acquire (or overwrite) the lock on *ticket_id* for *user*."""
    from modules.tickets.service import get_ticket_or_404
    await get_ticket_or_404(ticket_id)  # validate existence

    existing = await get_lock(ticket_id)
    if _is_active_lock(existing) and existing["locked_by"] != user["id"]:
        raise ConflictError(f"Ticket is currently locked by {existing['locked_by_username']}")

    now = _now_iso()
    expires = _expires_at_iso()
    lock_data = {
        "locked_by": user["id"],
        "locked_by_username": user["username"],
        "locked_at": now,
        "expires_at": expires,
    }

    # HSET + EXPIRE in a pipeline for atomicity
    async with get_redis().pipeline(transaction=True) as pipe:
        pipe.delete(_key(ticket_id))
        pipe.hset(_key(ticket_id), mapping=lock_data)
        pipe.expire(_key(ticket_id), settings.lock_ttl_seconds)
        await pipe.execute()

    await emit_event(
        bus, EventDomain.LOCK.value, EventType.LOCK_ACQUIRED.value,
        {"ticket_id": ticket_id, "locked_by": user["id"], "locked_by_username": user["username"]},
        actor_id=user["id"], ticket_id=ticket_id,
    )
    return await get_ticket_or_404(ticket_id)


async def refresh_lock(bus, ticket_id: str, user: dict) -> dict:
    """Refresh the TTL of a lock held by *user*."""
    from modules.tickets.service import get_ticket_or_404
    existing = await get_lock(ticket_id)
    if not _is_active_lock(existing) or existing["locked_by"] != user["id"]:
        raise ForbiddenError("You do not hold the lock on this ticket")

    new_expires = _expires_at_iso()
    async with get_redis().pipeline(transaction=True) as pipe:
        pipe.hset(_key(ticket_id), "expires_at", new_expires)
        pipe.expire(_key(ticket_id), settings.lock_ttl_seconds)
        await pipe.execute()

    await emit_event(
        bus, EventDomain.LOCK.value, EventType.LOCK_REFRESHED.value,
        {"ticket_id": ticket_id, "locked_by": user["id"]}, actor_id=user["id"], ticket_id=ticket_id,
    )
    return await get_ticket_or_404(ticket_id)


async def release_lock(bus, ticket_id: str, user: dict, force: bool = False) -> dict:
    """Release a lock (holder or admin force-release)."""
    from modules.tickets.service import get_ticket_or_404
    existing = await get_lock(ticket_id)
    if not force and existing.get("locked_by") and existing["locked_by"] != user["id"]:
        raise ForbiddenError("You do not hold the lock on this ticket")

    was_locked_by = existing.get("locked_by")

    await get_redis().delete(_key(ticket_id))

    await emit_event(
        bus, EventDomain.LOCK.value, EventType.LOCK_RELEASED.value,
        {"ticket_id": ticket_id, "released_by": user["id"], "forced": force, "was_locked_by": was_locked_by},
        actor_id=user["id"], ticket_id=ticket_id,
    )
    return await get_ticket_or_404(ticket_id)


async def janitor_sweep(bus) -> int:
    """Scan for lock keys whose TTL has run out and emit LOCK_EXPIRED events.

    Redis auto-deletes keys when their TTL reaches 0, but there is a small
    window between the TTL reaching 0 and the actual deletion (lazy expiry).
    We iterate all lock keys and check their remaining TTL — any key whose
    TTL is None or <= 0 (i.e. already logically expired) is deleted and an
    event is emitted.

    Returns the count of locks that were expired and cleaned up.
    """
    count = 0
    async for key in get_redis().scan_iter(match=f"{_KEY_PREFIX}*", count=500):
        ttl = await get_redis().ttl(key)
        if ttl is not None and ttl <= 0:
            # Key expired but not yet deleted — grab data before we delete
            data = await get_redis().hgetall(key)
            lock = _parse_hash(data)
            ticket_id = key[len(_KEY_PREFIX):]
            await get_redis().delete(key)
            await emit_event(
                bus, EventDomain.LOCK.value, EventType.LOCK_EXPIRED.value,
                {"ticket_id": ticket_id, "was_locked_by": lock.get("locked_by")},
                ticket_id=ticket_id,
            )
            count += 1
    return count
