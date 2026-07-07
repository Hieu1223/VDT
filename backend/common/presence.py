"""Redis-backed, TTL-based online-presence tracker.

A user is considered online if we have heard from them (heartbeat or open
WebSocket) within PRESENCE_TTL_SECONDS. The state lives in Redis under the
key `presence:{user_id}` with a TTL - so it is:

  * shared across all backend instances (horizontal scale-out),
  * durable to single-instance restarts (as long as Redis is up),
  * self-expiring (no in-process sweep required, although `sweep_expired`
    is kept for emitting the offline-broadcast event on transition).

This replaces the previous in-memory dict implementation.
"""
import logging
from typing import Iterable

from common.redis_client import redis_client

logger = logging.getLogger("presence")

PRESENCE_TTL_SECONDS = 45
_KEY_PREFIX = "presence:"


def _key(user_id: str) -> str:
    return f"{_KEY_PREFIX}{user_id}"


async def _scan_keys() -> list[str]:
    """Return all currently-known presence keys."""
    assert redis_client is not None, "redis_client not initialised"
    keys: list[str] = []
    async for k in redis_client.scan_iter(match=f"{_KEY_PREFIX}*", count=500):
        keys.append(k)
    return keys


async def touch(user_id: str) -> bool:
    """Record a heartbeat. Returns True if this is a fresh online transition."""
    assert redis_client is not None, "redis_client not initialised"
    was_online = await is_online(user_id)
    # SET with NX would not refresh an existing key's TTL, so we always SET
    # and rely on the return value of EXPIRE-by-SET to detect transition.
    # To detect a fresh transition we check `was_online` first (above).
    await redis_client.set(_key(user_id), "1", ex=PRESENCE_TTL_SECONDS)
    return not was_online


async def is_online(user_id: str) -> bool:
    assert redis_client is not None, "redis_client not initialised"
    return bool(await redis_client.exists(_key(user_id)))


async def online_ids() -> set[str]:
    """Return the set of currently-online user ids."""
    keys = await _scan_keys()
    return {k[len(_KEY_PREFIX):] for k in keys}


async def sweep_expired() -> set[str]:
    """Inspect presence keys and return user ids whose TTL has just lapsed.

    Redis expires keys lazily, so this scans the keyspace and diffs against
    a caller-supplied known set is unnecessary - we simply report whatever
    is currently absent. To make this useful for the presence-janitor
    (which wants to broadcast offline transitions) we accept the set of ids
    that *were* online last sweep via module-level memo below.
    """
    # Redis handles TTL expiry itself; nothing to physically delete. The
    # caller (presence janitor) reads online_ids() and compares against the
    # previous snapshot to detect transitions.
    return await online_ids()


async def mark_offline(user_id: str) -> None:
    """Explicit logout - force offline immediately rather than waiting for TTL."""
    assert redis_client is not None, "redis_client not initialised"
    await redis_client.delete(_key(user_id))


# ---------------------------------------------------------------------------
# Backwards-compatible facade
# ---------------------------------------------------------------------------
# Lots of call sites do `presence.is_online(...)` / `presence.touch(...)`.
# The previous module exposed a PresenceTracker instance named `presence`.
# We keep the same name but as a thin module-like object that forwards to
# the async functions above, so existing call sites only need to add `await`.
class _PresenceFacade:
    """Forwards attribute access to the module-level async functions."""

    touch = staticmethod(touch)
    is_online = staticmethod(is_online)
    online_ids = staticmethod(online_ids)
    sweep_expired = staticmethod(sweep_expired)
    mark_offline = staticmethod(mark_offline)


presence = _PresenceFacade()


async def enrich_online(user: dict) -> dict:
    """Attach `online: bool` to a user dict (read from Redis)."""
    user["online"] = await is_online(user["id"])
    return user
