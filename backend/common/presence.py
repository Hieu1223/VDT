"""In-memory, TTL-based online-presence tracker.

Deliberately NOT persisted to Mongo — "online" is a live, ephemeral concept
driven by heartbeats (web UI + SDK poll `/users/me/heartbeat` periodically)
and/or an open WebSocket. A user is considered online if we've heard from
them within PRESENCE_TTL_SECONDS.
"""
from datetime import datetime, timezone

PRESENCE_TTL_SECONDS = 45


class PresenceTracker:
    def __init__(self, ttl_seconds: int = PRESENCE_TTL_SECONDS):
        self._ttl = ttl_seconds
        self._last_seen: dict[str, datetime] = {}
        self._known_online: set[str] = set()

    def touch(self, user_id: str) -> bool:
        """Records a heartbeat. Returns True if this is a fresh online transition."""
        was_online = self.is_online(user_id)
        self._last_seen[user_id] = datetime.now(timezone.utc)
        self._known_online.add(user_id)
        return not was_online

    def is_online(self, user_id: str) -> bool:
        last = self._last_seen.get(user_id)
        if not last:
            return False
        return (datetime.now(timezone.utc) - last).total_seconds() < self._ttl

    def online_ids(self) -> set[str]:
        return {uid for uid in self._known_online if self.is_online(uid)}

    def sweep_expired(self) -> set[str]:
        """Call periodically. Returns the set of user_ids that just went offline."""
        expired = set()
        for uid in list(self._known_online):
            if not self.is_online(uid):
                expired.add(uid)
                self._known_online.discard(uid)
        return expired

    def mark_offline(self, user_id: str) -> None:
        """Explicit logout - force offline immediately rather than waiting for TTL expiry."""
        self._last_seen.pop(user_id, None)
        self._known_online.discard(user_id)


presence = PresenceTracker()


def enrich_online(user: dict) -> dict:
    user["online"] = presence.is_online(user["id"])
    return user
