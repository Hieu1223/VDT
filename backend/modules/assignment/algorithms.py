"""Plug-and-play assignment algorithm registry. Admin picks the active
algorithm at runtime via /assignment/config; adding a new algorithm is
just adding a function here and registering it in ALGORITHMS.
"""
from common.enums import OPEN_TICKET_STATUSES
from persistence.db import db


async def round_robin(candidates: list[dict], config: dict) -> dict | None:
    if not candidates:
        return None
    cursor = config.get("round_robin_cursor", 0) % len(candidates)
    chosen = candidates[cursor]
    await db.assignment_config.update_one({"id": "config"}, {"$set": {"round_robin_cursor": (cursor + 1) % len(candidates)}})
    return chosen


async def least_busy(candidates: list[dict], config: dict) -> dict | None:
    if not candidates:
        return None
    best, best_count = None, None
    for tech in candidates:
        count = await db.tickets.count_documents({"assignee_id": tech["id"], "status": {"$in": list(OPEN_TICKET_STATUSES)}})
        if best_count is None or count < best_count:
            best, best_count = tech, count
    return best


ALGORITHMS = {
    "round_robin": round_robin,
    "least_busy": least_busy,
}
